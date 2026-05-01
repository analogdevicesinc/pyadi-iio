"""Test conftest for the prism_report plugin tests.

Enables pytest's built-in `pytester` fixture (disabled by default in pytest 9.x)
and works around an environment-specific issue: when `pytester` runs an inner
pytest in-process, labgrid's pytest plugin (auto-loaded via entry-point) calls
`StepLogger.start()` again and asserts because the outer pytest already
started it. Disabling labgrid in inner runs avoids the collision; our plugin
under test is unaffected.
"""
from __future__ import annotations

import numpy as np
import pytest

# NOTE: `pytest_plugins = ["pytester"]` would belong here, but pytest 9.x
# rejects pytest_plugins in non-rootdir conftests. It is registered in the
# top-level test/conftest.py instead.


@pytest.fixture
def pytester(pytester):  # type: ignore[no-redef]
    # Ensure inner pytest invocations do not try to re-init labgrid's
    # global StepLogger (which the outer pytest already started). Also
    # explicitly load the prism_report plugin (the inner ini we install
    # below shadows the outer rootdir's pyproject.toml/conftest, so the
    # plugin must be referenced here for it to register its addoptions).
    pytester.makeini(
        """
        [pytest]
        addopts = -p no:labgrid -p test.plugins.prism_report.plugin
        """
    )
    return pytester


@pytest.fixture
def synthetic_tone():
    """One-tone complex IQ at known frequency, with controlled HD2/HD3."""
    fs = 4_000_000
    n = 2 ** 14
    f0 = fs * 0.1
    f0 = int(f0 / (fs / n)) * (fs / n)
    t = np.arange(n) / fs
    rng = np.random.default_rng(seed=0)
    iq = (
        1.0 * np.exp(2j * np.pi * f0 * t)
        + 0.01 * np.exp(2j * np.pi * 2 * f0 * t)   # HD2 ~ -40 dBc
        + 0.003 * np.exp(2j * np.pi * 3 * f0 * t)  # HD3 ~ -50 dBc
        + 1e-4 * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    )
    iq = (iq * (2 ** 14)).astype(np.complex64)
    return {"iq": iq, "fs": fs, "f0": f0}


@pytest.fixture
def synthetic_two_tone():
    fs = 4_000_000
    n = 2 ** 14
    f1 = fs * 0.10
    f2 = fs * 0.13
    f1 = int(f1 / (fs / n)) * (fs / n)
    f2 = int(f2 / (fs / n)) * (fs / n)
    t = np.arange(n) / fs
    iq = (
        np.exp(2j * np.pi * f1 * t) + np.exp(2j * np.pi * f2 * t)
    )
    iq = (iq * (2 ** 14)).astype(np.complex64)
    return {"iq": iq, "fs": fs, "f1": f1, "f2": f2}


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden", action="store_true", default=False,
        help="Regenerate render.py golden HTML files.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "bench_pluto: hardware-loop tests that require a real Pluto. "
        "Skipped unless BENCH_PLUTO_URI env var is set.",
    )
    config.addinivalue_line(
        "markers",
        "prism_live: contract test against a running Prism instance. "
        "Skipped unless PRISM_LIVE_URL env var is set.",
    )
