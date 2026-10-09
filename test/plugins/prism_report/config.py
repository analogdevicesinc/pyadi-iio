"""Resolved configuration for the prism_report plugin.

Precedence: CLI flag > PRISM_* env var > built-in default. All resolution
happens in one place; the rest of the plugin reads a frozen Config.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import socket
from dataclasses import dataclass, field
from pathlib import Path, PosixPath


class ConfigError(Exception):
    """Raised on user-input errors (bad flag combinations, missing required)."""


class _RelDotPath(PosixPath):
    """A Path that preserves a leading ``./`` in its string form.

    ``pathlib.Path('./foo')`` normalises to ``PosixPath('foo')`` and
    ``str(...)`` returns ``'foo'``. The default Prism output directory is
    spelled ``./prism-report-<ts>`` for human-readability; this subclass
    keeps that prefix while remaining a fully-functional ``Path``.
    """

    def __str__(self) -> str:  # type: ignore[override]
        s = super().__str__()
        if s.startswith("/") or s.startswith("./") or s.startswith("../"):
            return s
        return "./" + s


@dataclass(frozen=True)
class Config:
    enabled: bool
    out_dir: Path | None
    upload_url: str | None
    upload_email: str | None
    upload_password: str | None
    upload_project: str | None
    run_name: str
    user_tags: dict[str, str]
    labgrid_place: str | None
    no_labgrid: bool
    dmesg_via: str  # "auto" | "ssh" | "console" | "none"
    dmesg_ssh_user: str
    dmesg_ssh_key: str | None
    fail_on_upload_error: bool
    # Mapping of topic -> human-readable message. Keyed access lets callers
    # check `"<topic>" in cfg.warnings` without parsing prose.
    warnings: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_argv(cls, argv: list[str]) -> "Config":
        parser = _build_parser()
        ns = parser.parse_args(argv)
        return _resolve(ns, os.environ)

    @classmethod
    def from_pytest(cls, pytest_config) -> "Config":
        # invocation_params.args includes pytest's own flags (-q, -v, ...)
        # plus any user args. Use parse_known_args to ignore non-prism flags.
        argv = list(pytest_config.invocation_params.args)
        parser = _build_parser()
        ns, _ = parser.parse_known_args(argv)
        return _resolve(ns, os.environ)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--prism-report", action="store_true", default=None)
    p.add_argument("--prism-out", default=None)
    p.add_argument("--prism-url", default=None)
    p.add_argument("--prism-email", default=None)
    p.add_argument("--prism-password", default=None)
    p.add_argument("--prism-project", default=None)
    p.add_argument("--prism-run-name", default=None)
    p.add_argument("--prism-tag", action="append", default=[])
    p.add_argument("--prism-labgrid-place", default=None)
    p.add_argument("--prism-no-labgrid", action="store_true", default=None)
    p.add_argument("--prism-dmesg-via", default=None,
                   choices=["auto", "ssh", "console", "none"])
    p.add_argument("--prism-dmesg-ssh-user", default=None)
    p.add_argument("--prism-dmesg-ssh-key", default=None)
    p.add_argument("--prism-fail-on-upload-error", action="store_true", default=None)
    return p


def _env_bool(env: dict, key: str) -> bool | None:
    v = env.get(key)
    if v is None:
        return None
    return v.strip().lower() in ("1", "true", "yes", "on")


def _resolve(ns: argparse.Namespace, env: dict) -> Config:
    warnings: dict[str, str] = {}

    def _pick(cli_val, env_key, default=None):
        if cli_val is not None:
            return cli_val
        if env_key in env:
            return env[env_key]
        return default

    enabled_cli = ns.prism_report
    enabled_env = _env_bool(env, "PRISM_REPORT")
    enabled = bool(enabled_cli) or bool(enabled_env)

    if not enabled:
        return Config(
            enabled=False, out_dir=None, upload_url=None, upload_email=None,
            upload_password=None, upload_project=None, run_name="",
            user_tags={}, labgrid_place=None, no_labgrid=False,
            dmesg_via="auto", dmesg_ssh_user="root", dmesg_ssh_key=None,
            fail_on_upload_error=False, warnings={},
        )

    upload_url = _pick(ns.prism_url, "PRISM_URL")
    upload_email = _pick(ns.prism_email, "PRISM_EMAIL")
    upload_password = _pick(ns.prism_password, "PRISM_PASSWORD")
    upload_project = _pick(ns.prism_project, "PRISM_PROJECT")
    if upload_url and not upload_project:
        raise ConfigError(
            "--prism-project is required when --prism-url is set"
        )

    no_labgrid_cli = ns.prism_no_labgrid
    no_labgrid_env = _env_bool(env, "PRISM_NO_LABGRID")
    no_labgrid = bool(no_labgrid_cli) or bool(no_labgrid_env)

    place_cli = ns.prism_labgrid_place
    place_env = env.get("PRISM_LABGRID_PLACE")
    if no_labgrid_cli and place_cli is not None:
        raise ConfigError(
            "--prism-no-labgrid conflicts with --prism-labgrid-place"
        )
    if no_labgrid:
        labgrid_place = None
        if no_labgrid_cli and place_env is not None and place_cli is None:
            warnings["labgrid_place"] = (
                "env PRISM_LABGRID_PLACE ignored because "
                "--prism-no-labgrid is set"
            )
    else:
        labgrid_place = place_cli if place_cli is not None else place_env

    out_cli = ns.prism_out
    out_env = env.get("PRISM_OUT")
    out_resolved = out_cli if out_cli is not None else out_env
    out_is_default = False
    if out_resolved is None and upload_url is None:
        ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_resolved = f"./prism-report-{ts}"
        out_is_default = True
    if out_resolved is None:
        out_dir: Path | None = None
    elif out_is_default:
        # Built-in default keeps its leading ``./`` for clarity in logs.
        out_dir = _RelDotPath(out_resolved)
    else:
        out_dir = Path(out_resolved)

    user_tags: dict[str, str] = {}
    for raw in ns.prism_tag:
        if "=" not in raw:
            raise ConfigError(f"--prism-tag expects key=value, got {raw!r}")
        k, v = raw.split("=", 1)
        user_tags[k.strip()] = v.strip()

    run_name = _pick(ns.prism_run_name, "PRISM_RUN_NAME")
    if not run_name:
        host = socket.gethostname()
        ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_name = f"{host}-{ts}"

    return Config(
        enabled=True,
        out_dir=out_dir,
        upload_url=upload_url,
        upload_email=upload_email,
        upload_password=upload_password,
        upload_project=upload_project,
        run_name=run_name,
        user_tags=user_tags,
        labgrid_place=labgrid_place,
        no_labgrid=no_labgrid,
        dmesg_via=_pick(ns.prism_dmesg_via, "PRISM_DMESG_VIA", "auto"),
        dmesg_ssh_user=_pick(ns.prism_dmesg_ssh_user, "PRISM_DMESG_SSH_USER", "root"),
        dmesg_ssh_key=_pick(ns.prism_dmesg_ssh_key, "PRISM_DMESG_SSH_KEY"),
        fail_on_upload_error=bool(ns.prism_fail_on_upload_error
                                  or _env_bool(env, "PRISM_FAIL_ON_UPLOAD_ERROR")),
        warnings=warnings,
    )
