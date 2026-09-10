"""Verify the plugin is a no-op unless --prism-report is passed."""
from __future__ import annotations


def test_plugin_registers_addoption(pytestconfig):
    # The flag must exist (pytest registered our addoption).
    assert pytestconfig.getoption("--prism-report") is False


def test_plugin_idle_when_flag_off(pytester):
    pytester.makepyfile(
        """
        def test_one():
            assert 1 == 1
        """
    )
    result = pytester.runpytest("-q")
    result.assert_outcomes(passed=1)
    # Plugin must not write any artifacts when flag is off.
    assert not any(p.name.startswith("prism-report") for p in pytester.path.iterdir())
