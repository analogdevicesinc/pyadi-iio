"""Test conftest for the prism_report plugin tests.

Enables pytest's built-in `pytester` fixture (disabled by default in pytest 9.x)
and works around an environment-specific issue: when `pytester` runs an inner
pytest in-process, labgrid's pytest plugin (auto-loaded via entry-point) calls
`StepLogger.start()` again and asserts because the outer pytest already
started it. Disabling labgrid in inner runs avoids the collision; our plugin
under test is unaffected.
"""
from __future__ import annotations

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def pytester(pytester):  # type: ignore[no-redef]
    # Ensure inner pytest invocations do not try to re-init labgrid's
    # global StepLogger (which the outer pytest already started).
    pytester.makeini(
        """
        [pytest]
        addopts = -p no:labgrid
        """
    )
    return pytester
