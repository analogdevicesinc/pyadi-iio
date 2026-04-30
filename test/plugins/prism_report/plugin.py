"""prism_report pytest plugin — minimal scaffold (Task 0).

All hooks short-circuit unless --prism-report is set. Subsequent tasks fill
in real behavior.
"""
from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("prism_report", "Prism test-report plugin")
    group.addoption(
        "--prism-report",
        action="store_true",
        default=False,
        help="Enable the Prism test-report plugin.",
    )


def pytest_configure(config: pytest.Config) -> None:
    if not config.getoption("--prism-report"):
        return
    # Subsequent tasks attach a session-state object here.
    config._prism_report_active = True
