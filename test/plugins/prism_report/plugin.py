"""prism_report pytest plugin — flag registration + Config (Task 1)."""
from __future__ import annotations

import pytest

from test.plugins.prism_report.config import Config, ConfigError


def pytest_addoption(parser: pytest.Parser) -> None:
    g = parser.getgroup("prism_report", "Prism test-report plugin")
    g.addoption("--prism-report", action="store_true", default=False)
    g.addoption("--prism-out", default=None)
    g.addoption("--prism-url", default=None)
    g.addoption("--prism-email", default=None)
    g.addoption("--prism-password", default=None)
    g.addoption("--prism-project", default=None)
    g.addoption("--prism-run-name", default=None)
    g.addoption("--prism-tag", action="append", default=[])
    g.addoption("--prism-labgrid-place", default=None)
    g.addoption("--prism-no-labgrid", action="store_true", default=False)
    g.addoption("--prism-dmesg-via", default=None,
                choices=["auto", "ssh", "console", "none"])
    g.addoption("--prism-dmesg-ssh-user", default=None)
    g.addoption("--prism-dmesg-ssh-key", default=None)
    g.addoption("--prism-fail-on-upload-error", action="store_true", default=False)


def pytest_configure(config: pytest.Config) -> None:
    if not config.getoption("--prism-report"):
        return
    try:
        cfg = Config.from_pytest(config)
    except ConfigError as exc:
        raise pytest.UsageError(f"prism-report: {exc}") from exc
    config._prism_report_cfg = cfg
    for topic, message in cfg.warnings.items():
        config.issue_config_time_warning(
            pytest.PytestConfigWarning(f"prism-report: {topic}: {message}"),
            stacklevel=1,
        )
