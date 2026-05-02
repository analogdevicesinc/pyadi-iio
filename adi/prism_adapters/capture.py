"""Run-level captures: iio_info, dmesg, labgrid console.

Each function returns ``bytes | None`` — None on graceful skip.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass


def _open_iio_context(uri: str):
    import iio  # pylibiio
    return iio.Context(uri)


def _walk_iio_context(uri: str) -> bytes:
    ctx = _open_iio_context(uri)
    lines = [f"# IIO context (library walk) uri={uri}",
             f"# description: {getattr(ctx, 'description', '')}"]
    for k, v in dict(ctx.attrs).items():
        lines.append(f"{k}: {v}")
    for dev in ctx.devices:
        lines.append(f"\nDevice: {dev.name} ({dev.id})")
        for k, v in dict(dev.attrs).items():
            lines.append(f"  {k}: {v.value}")
        for ch in dev.channels:
            lines.append(f"  Channel {ch.id} (output={ch.output})")
            for k, v in dict(ch.attrs).items():
                lines.append(f"    {k}: {v.value}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def capture_iio_info(uri: str, *, timeout_s: float = 15.0) -> bytes | None:
    try:
        proc = subprocess.run(
            ["iio_info", "-u", uri],
            capture_output=True, timeout=timeout_s, check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
        sys.stderr.write(
            f"prism-report: iio_info -u {uri} exited {proc.returncode}; "
            f"falling back to library walk\n"
        )
    except FileNotFoundError:
        sys.stderr.write(
            "prism-report: iio_info binary not found; falling back to library "
            "walk\n"
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write(
            f"prism-report: iio_info timed out after {timeout_s}s; falling "
            f"back to library walk\n"
        )

    try:
        return _walk_iio_context(uri)
    except Exception as exc:  # iio import error, connection refused, etc.
        sys.stderr.write(
            f"prism-report: could not capture iio_info: {exc}\n"
        )
        return None


_TS_RE = re.compile(rb"^\[\s*[\d.]+\]\s*")


def _strip_ts(line: bytes) -> bytes:
    return _TS_RE.sub(b"", line)


def _ssh_dmesg(host: str, user: str, key: str | None,
               timeout_s: float = 15.0) -> bytes | None:
    cmd = ["ssh", "-o", "BatchMode=yes",
           "-o", "StrictHostKeyChecking=accept-new",
           "-o", f"ConnectTimeout={int(timeout_s)}"]
    if key:
        cmd += ["-i", key]
    cmd += [f"{user}@{host}", "dmesg"]
    try:
        proc = subprocess.run(cmd, capture_output=True,
                              timeout=timeout_s, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write(f"prism-report: dmesg via ssh failed: {exc}\n")
        return None
    if proc.returncode != 0:
        sys.stderr.write(
            f"prism-report: dmesg via ssh exited {proc.returncode}: "
            f"{proc.stderr[:200]!r}\n"
        )
        return None
    return proc.stdout


def _console_dmesg(labgrid_session) -> bytes | None:
    if labgrid_session is None:
        return None
    try:
        result = labgrid_session.run_shell_command("dmesg")
    except Exception as exc:
        sys.stderr.write(f"prism-report: dmesg via console failed: {exc}\n")
        return None
    if isinstance(result, str):
        result = result.encode("utf-8", errors="replace")
    return result


def capture_dmesg(*, iio_uri: str, via: str, ssh_user: str,
                  ssh_key: str | None, labgrid_session) -> bytes | None:
    if via == "none":
        return None

    host: str | None = None
    if iio_uri.startswith("ip:"):
        host = iio_uri[3:].split(",")[0]

    methods: list[str] = []
    if via == "ssh":
        methods = ["ssh"]
    elif via == "console":
        methods = ["console"]
    else:  # auto
        if host is not None:
            methods.append("ssh")
        methods.append("console")

    for m in methods:
        if m == "ssh" and host is not None:
            out = _ssh_dmesg(host, ssh_user, ssh_key)
            if out is not None:
                return out
        elif m == "console":
            out = _console_dmesg(labgrid_session)
            if out is not None:
                return out
    return None


def compute_dmesg_diff(pre: bytes, post: bytes) -> bytes:
    pre_set = {_strip_ts(line) for line in pre.splitlines() if line.strip()}
    new_lines: list[bytes] = []
    for line in post.splitlines():
        if not line.strip():
            continue
        if _strip_ts(line) not in pre_set:
            new_lines.append(line)
    return (b"\n".join(new_lines) + b"\n") if new_lines else b""


class LabgridSession:
    """Thin wrapper around the actual labgrid client.

    Concrete labgrid client API differs by version; this wrapper exposes only
    the three operations capture.py needs: ``acquire``, ``read_console``,
    ``run_shell_command``. ``__init__`` accepts any object that quacks like
    one — production code wires in the real client at session start; tests
    pass a fake.
    """

    def __init__(self, client):
        self._client = client
        self._claimed_place: str | None = None
        self._handle = None

    def acquire(self, place: str) -> bool:
        self._handle = self._client.acquire(place)
        self._claimed_place = place
        return True

    def read_console(self) -> bytes:
        return self._handle.read_console()

    def run_shell_command(self, cmd: str) -> bytes:
        return self._handle.run_shell_command(cmd)

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            self._handle.release()
        except Exception as exc:
            sys.stderr.write(f"prism-report: labgrid release failed: {exc}\n")
        self._handle = None
        self._claimed_place = None


def capture_boot_log(session: LabgridSession | None, *,
                     place: str | None) -> bytes | None:
    if session is None or place is None:
        return None
    try:
        session.acquire(place)
        buf = session.read_console()
        if isinstance(buf, str):
            buf = buf.encode("utf-8", errors="replace")
        header = (
            f"# captured from labgrid place={place} at session-start\n"
        ).encode("utf-8")
        return header + buf
    except Exception as exc:
        sys.stderr.write(
            f"prism-report: labgrid place {place!r} unreachable: {exc}; "
            f"continuing without console capture\n"
        )
        return None


def open_labgrid_session(*, no_labgrid: bool):
    """Try to import + connect to the real labgrid client. Return None on any
    failure or when --prism-no-labgrid is set."""
    if no_labgrid:
        return None
    try:
        # Verify the real labgrid Python API at write time. Confirm against
        # the labgrid version on the bench.
        from labgrid.remote.client import RemoteSession  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "prism-report: labgrid not installed; skipping console capture\n"
        )
        return None
    try:
        # NOTE: replace with the actual remote-coordinator handshake.
        client = _build_real_labgrid_client()  # type: ignore[name-defined]
    except Exception as exc:
        sys.stderr.write(
            f"prism-report: labgrid coordinator unreachable: {exc}\n"
        )
        return None
    return LabgridSession(client)


def _build_real_labgrid_client():
    """Bench-time hook. Replace with the version-specific labgrid client
    construction. Kept as a separate function so tests can monkeypatch it."""
    from labgrid.remote.client import RemoteSession
    return RemoteSession()


@dataclass
class SessionPre:
    iio_info: bytes | None
    dmesg: bytes | None
    boot_log: bytes | None
    labgrid_session: LabgridSession | None
    dmesg_capture_method: str  # "ssh" | "console" | "skipped"


@dataclass
class SessionPost:
    dmesg_post: bytes | None
    dmesg_diff: bytes | None


def capture_session_pre(cfg, iio_uri: str) -> SessionPre:
    info = capture_iio_info(iio_uri) if iio_uri else None
    sess = open_labgrid_session(no_labgrid=cfg.no_labgrid)
    boot = capture_boot_log(sess, place=cfg.labgrid_place)
    if cfg.dmesg_via == "none":
        dmesg, method = None, "skipped"
    else:
        before_kw = dict(
            iio_uri=iio_uri, via=cfg.dmesg_via,
            ssh_user=cfg.dmesg_ssh_user, ssh_key=cfg.dmesg_ssh_key,
            labgrid_session=sess,
        )
        dmesg = capture_dmesg(**before_kw)
        method = _which_method(cfg.dmesg_via, iio_uri,
                               labgrid_present=sess is not None,
                               got=dmesg is not None)
    return SessionPre(
        iio_info=info, dmesg=dmesg, boot_log=boot,
        labgrid_session=sess, dmesg_capture_method=method,
    )


def capture_session_post(cfg, iio_uri: str, pre: SessionPre) -> SessionPost:
    if cfg.dmesg_via == "none":
        post = None
    else:
        post = capture_dmesg(
            iio_uri=iio_uri, via=cfg.dmesg_via,
            ssh_user=cfg.dmesg_ssh_user, ssh_key=cfg.dmesg_ssh_key,
            labgrid_session=pre.labgrid_session,
        )
    diff = None
    if pre.dmesg is not None and post is not None:
        diff = compute_dmesg_diff(pre.dmesg, post)
    if pre.labgrid_session is not None:
        pre.labgrid_session.release()
    return SessionPost(dmesg_post=post, dmesg_diff=diff)


def _which_method(via, iio_uri, *, labgrid_present, got):
    if not got:
        return "skipped"
    if via == "ssh" or (via == "auto" and iio_uri.startswith("ip:")):
        return "ssh"
    return "console"


# --- pytest-prism SessionHook adapter ---

from collections.abc import Mapping
from typing import Any, ClassVar

from pytest_prism import SessionContext


class ADIDUTHook:
    """SessionHook that captures iio_info, dmesg pre/post, and labgrid console.

    Uses the cfg fields (`labgrid_place`, `no_labgrid`, `dmesg_via`,
    `dmesg_ssh_user`, `dmesg_ssh_key`) carried by `Config` from
    `pytest_prism.config`. The IIO URI is read from the `PYADI_IIO_URI` env var.
    """

    name: ClassVar[str] = "adi_dut"

    def __init__(self) -> None:
        self._pre: SessionPre | None = None
        self._iio_uri: str | None = None

    def _resolve_iio_uri(self) -> str | None:
        import os
        return os.environ.get("PYADI_IIO_URI") or None

    def session_pre(self, ctx: SessionContext) -> Mapping[str, Any]:
        self._iio_uri = self._resolve_iio_uri() or ""
        self._pre = capture_session_pre(ctx.config, self._iio_uri)
        if self._pre.iio_info is not None:
            (ctx.hook_dir / "iio_info.txt").write_bytes(self._pre.iio_info)
        if self._pre.boot_log is not None:
            (ctx.hook_dir / "boot.log").write_bytes(self._pre.boot_log)
        if self._pre.dmesg is not None:
            (ctx.hook_dir / "dmesg_pre.log").write_bytes(self._pre.dmesg)
        return {
            "iio_uri": self._iio_uri,
            "labgrid_place": ctx.config.labgrid_place,
            "dmesg_capture_method": self._pre.dmesg_capture_method,
        }

    def session_post(self, ctx: SessionContext) -> Mapping[str, Any]:
        if self._pre is None:
            self._pre = SessionPre(None, None, None, None, "skipped")
        post = capture_session_post(ctx.config, self._iio_uri or "", self._pre)
        if post.dmesg_post is not None:
            (ctx.hook_dir / "dmesg_post.log").write_bytes(post.dmesg_post)
        if post.dmesg_diff is not None:
            (ctx.hook_dir / "dmesg_diff.log").write_bytes(post.dmesg_diff)
        return {"dmesg_post_captured": post.dmesg_post is not None}
