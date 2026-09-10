"""Resolved Config = CLI > env > built-in defaults."""
from __future__ import annotations

import pytest

from test.plugins.prism_report.config import Config, ConfigError


def _from_argv_and_env(argv, env, monkeypatch):
    for key in list(env.keys()):
        monkeypatch.setenv(key, env[key])
    # Strip out any PRISM_* env vars not in the test fixture.
    for key in [k for k in __import__("os").environ if k.startswith("PRISM_")]:
        if key not in env:
            monkeypatch.delenv(key, raising=False)
    return Config.from_argv(argv)


def test_disabled_when_flag_absent(monkeypatch):
    cfg = _from_argv_and_env([], {}, monkeypatch)
    assert cfg.enabled is False


def test_default_out_when_no_sink(monkeypatch):
    cfg = _from_argv_and_env(["--prism-report"], {}, monkeypatch)
    assert cfg.enabled is True
    assert cfg.out_dir is not None
    assert str(cfg.out_dir).startswith("./prism-report-")
    assert cfg.upload_url is None


def test_cli_beats_env(monkeypatch):
    cfg = _from_argv_and_env(
        ["--prism-report", "--prism-out=cli/path"],
        {"PRISM_OUT": "env/path"},
        monkeypatch,
    )
    assert str(cfg.out_dir) == "cli/path"


def test_env_used_when_no_cli(monkeypatch):
    cfg = _from_argv_and_env(
        ["--prism-report"],
        {"PRISM_OUT": "env/path"},
        monkeypatch,
    )
    assert str(cfg.out_dir) == "env/path"


def test_upload_requires_project(monkeypatch):
    with pytest.raises(ConfigError, match="--prism-project"):
        _from_argv_and_env(
            ["--prism-report", "--prism-url=http://x"],
            {},
            monkeypatch,
        )


def test_no_labgrid_conflicts_with_place_on_cli(monkeypatch):
    with pytest.raises(ConfigError, match="conflict"):
        _from_argv_and_env(
            ["--prism-report", "--prism-no-labgrid", "--prism-labgrid-place=p1"],
            {},
            monkeypatch,
        )


def test_no_labgrid_with_env_place_warns_not_fails(monkeypatch):
    cfg = _from_argv_and_env(
        ["--prism-report", "--prism-no-labgrid"],
        {"PRISM_LABGRID_PLACE": "p1"},
        monkeypatch,
    )
    assert cfg.no_labgrid is True
    assert cfg.labgrid_place is None  # CLI no-labgrid wins over env
    assert "labgrid_place" in cfg.warnings


def test_env_only_no_labgrid_does_not_warn(monkeypatch):
    cfg = _from_argv_and_env(
        ["--prism-report"],
        {"PRISM_NO_LABGRID": "1", "PRISM_LABGRID_PLACE": "p1"},
        monkeypatch,
    )
    assert cfg.no_labgrid is True
    assert cfg.labgrid_place is None
    # Both came from env — no inconsistency to warn about.
    assert "labgrid_place" not in cfg.warnings


def test_repeatable_tag(monkeypatch):
    cfg = _from_argv_and_env(
        ["--prism-report", "--prism-tag", "branch=main", "--prism-tag", "sha=abc"],
        {},
        monkeypatch,
    )
    assert cfg.user_tags == {"branch": "main", "sha": "abc"}


def test_dmesg_via_default_auto(monkeypatch):
    cfg = _from_argv_and_env(["--prism-report"], {}, monkeypatch)
    assert cfg.dmesg_via == "auto"
