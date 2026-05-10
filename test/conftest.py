import inspect
import random
import test.rf.spec as spec
import time
from test.attr_tests import *
from test.common import (
    dev_interface,
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_configure,
    pytest_generate_tests,
    pytest_runtest_setup,
)
from test.dma_tests import *
from test.generics import iio_attribute_single_value
from test.globals import *
from test.html import pytest_html_report_title, pytest_runtest_makereport
from test.jesd_tests import *

import numpy as np
import pytest

import adi

try:
    from test.scpi import dcxo_calibrate

    disable_prod_tests = False
except ImportError:
    disable_prod_tests = True


def pytest_runtest_makereport(item, call):
    """pytest_runtest_makereport:
    This pytest hook is used to create a custom test report using
    the xml property tag to add custom properties
    """

    if call.when == "call" and call.excinfo is not None:
        # Extract error type and message
        exception_type_and_message_formatted = call.excinfo.exconly() or "N/A"
        item.user_properties.append(
            ("exception_type_and_message", exception_type_and_message_formatted)
        )

        for fixture in item.fixturenames:
            if "test_" in fixture:  # Get fixtures in conftest.py
                fixture_defs = item.session._fixturemanager._arg2fixturedefs.get(
                    fixture, []
                )
                if fixture_defs:
                    # Get the fixture definition
                    for fix_func in fixture_defs:
                        fixture_func = fix_func.func
                        # Check if the fixture is a generator (yielding)
                        if inspect.isgeneratorfunction(fixture_func):
                            request_fixture = item.funcargs.get("request")
                            if request_fixture:
                                # Get the generator
                                generator = fixture_func(request_fixture)
                                # Get the yielded function (test function)
                                yielded_function = next(generator)
                                # Get the yielded function name
                                yielded_function_name = (
                                    yielded_function.__name__ or "N/A"
                                )
                                # Get the test function module
                                yielded_module = yielded_function.__module__ or "N/A"

                                # Add test function name and module as property in pytest xml report
                                item.user_properties.append(
                                    ("test_name_function", yielded_function_name)
                                )
                                item.user_properties.append(
                                    ("test_function_module", yielded_module)
                                )


def pytest_make_parametrize_id(val, argname):
    """pytest_make_parametrize_id:
        This pytest hook is used to return the test parameters as name=parameter value in the test report
        """
    return f"{argname}={val}"


#########################################
# Labgrid hardware-CI integration.
#
# Active only when LG_ENV is set (CI hardware runs).  When unset, this
# block is a no-op and the existing emu/unit-test path is untouched.
#
# Flow: pytest_configure boots the board via labgrid, polls for the
# DHCP-assigned IP and the IIO daemon coming up, then sets
# config.option.uri.  pytest-libiio's _contexts fixture (session-scope,
# runs after pytest_configure) reads --uri, builds an iio.Context,
# matches its devices against test/emu/hardware_map.yml, and skips any
# test whose @iio_hardware(...) doesn't match the discovered hardware.
# pytest_sessionfinish powers the board off after the last test.
import os as _os

_LG_ENV = _os.environ.get("LG_ENV")
_lg_strategy = None  # captured in pytest_configure for sessionfinish teardown


def _wait_for_ipv4(shell, timeout=60):
    """Poll the booted board for a valid DHCP-assigned IPv4 address.

    shell.run() captures both stdout and stderr from the serial console,
    so transient errors like "RTNETLINK answers: Network is unreachable"
    can land in the output before the link is up — validate the line is
    dotted-quad before accepting it.
    """
    import re
    import time

    ipv4_re = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
    deadline = time.time() + timeout
    while time.time() < deadline:
        out, _, _ = shell.run(
            "ip -4 -o route get 1.1.1.1 2>/dev/null "
            "| awk '{for(i=1;i<=NF;i++) if($i==\"src\") print $(i+1); exit}'"
        )
        for line in out or []:
            line = line.strip()
            if ipv4_re.match(line):
                return line
        time.sleep(2)
    return ""


def _wait_for_iio(uri, timeout=60):
    """Poll iio.Context(uri) until it succeeds or the deadline elapses."""
    import time

    import iio

    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            iio.Context(uri)
            return None
        except Exception as e:
            last_err = e
            time.sleep(2)
    return last_err


def _do_labgrid_boot(config):
    """One attempt at full labgrid boot + IP-readiness + URI publish."""
    global _lg_strategy
    from labgrid import Environment

    env = Environment(_LG_ENV)
    target = env.get_target("main")
    _lg_strategy = target.get_driver("Strategy")

    # `Status.shell` (rather than `Status.booted`) ensures BootFabric's
    # udhcpc fixup_networking runs and BootFPGASoC's shell driver is
    # active — both required so we can read the real DHCP IP below.
    _lg_strategy.transition("shell")

    shell = target.get_driver("CommandProtocol")
    ip = _wait_for_ipv4(shell, timeout=60)
    if not ip:
        raise RuntimeError("could not extract a valid IPv4 from board within 60s")
    uri = f"ip:{ip}"

    err = _wait_for_iio(uri, timeout=60)
    if err is not None:
        raise RuntimeError(f"IIO context at {uri} unreachable within 60s: {err!r}")

    config.option.uri = uri


def pytest_configure(config):
    """When LG_ENV is set, boot the lab board and point pytest-libiio at it.

    pytest-libiio reads --uri at session-fixture time (after
    pytest_configure), so setting config.option.uri here is observed
    by its _contexts fixture which then drives discovery-based test
    selection.

    Wrapped in a small retry loop because the lab-side path is flaky:
    mDNS resolution of `mini2`/`nuc` for the rfc2217 serial URL,
    SSH ControlMaster bring-up to the exporter, etc. all surface as
    transient socket.gaierror / connection errors that succeed on a
    second try.
    """
    if not _LG_ENV:
        return

    import time as _t

    attempts = 3
    last_err = None
    for i in range(1, attempts + 1):
        try:
            _do_labgrid_boot(config)
            return
        except Exception as e:
            last_err = e
            if i < attempts:
                _t.sleep(10)
    pytest.fail(f"labgrid boot failed after {attempts} attempts: {last_err!r}")


def pytest_sessionfinish(session, exitstatus):
    """Power the board off after the last test, regardless of pass/fail.

    All three strategies in use (BootFPGASoC, BootFPGASoCTFTP,
    BootFabric) define Status.powered_off so the same string transition
    works across legs.  Cleanup errors are warned, never re-raised, so
    a flaky power-off can't mask a real test failure.
    """
    if _lg_strategy is None:
        return
    try:
        _lg_strategy.transition("powered_off")
    except Exception as e:
        import warnings

        warnings.warn(f"strategy power-off failed: {e}")


#########################################


#########################################
# Fixtures
@pytest.fixture()
def test_iio_attribute_single_value(request):
    yield iio_attribute_single_value


@pytest.fixture()
def test_stress_context_creation(request):
    yield stress_context_creation


@pytest.fixture()
def test_stress_rx_buffer_length(request):
    yield stress_rx_buffer_length


@pytest.fixture()
def test_stress_rx_buffer_creation(request):
    yield stress_rx_buffer_creation


@pytest.fixture()
def test_stress_tx_buffer_creation(request):
    yield stress_tx_buffer_creation


@pytest.fixture()
def test_attribute_single_value(request):
    yield attribute_single_value


@pytest.fixture()
def test_attribute_single_value_readonly(request):
    yield attribute_single_value_readonly


@pytest.fixture()
def test_attribute_single_value_boolean(request):
    yield attribute_single_value_boolean


@pytest.fixture()
def test_attribute_single_value_str(request):
    yield attribute_single_value_str


@pytest.fixture()
def test_attribute_single_value_pow2(request):
    yield attribute_single_value_pow2


@pytest.fixture()
def test_dma_rx(request):
    yield dma_rx


@pytest.fixture()
def test_dma_tx(request):
    yield dma_tx


@pytest.fixture()
def test_cyclic_buffer(request):
    yield cyclic_buffer


@pytest.fixture()
def test_cyclic_buffer_exception(request):
    yield cyclic_buffer_exception


@pytest.fixture()
def test_dma_loopback(request):
    yield dma_loopback


@pytest.fixture()
def test_sfdr(request):
    yield t_sfdr


@pytest.fixture()
def test_dds_loopback(request):
    yield dds_loopback


@pytest.fixture()
def test_iq_loopback(request):
    yield cw_loopback


@pytest.fixture()
def test_cw_loopback(request):
    yield cw_loopback


@pytest.fixture()
def test_tone_loopback(request):
    yield nco_loopback


@pytest.fixture()
def test_gain_check(request):
    yield gain_check


@pytest.fixture()
def test_hardwaregain(request):
    yield hardwaregain


@pytest.fixture()
def test_harmonics(request):
    yield harmonic_vals


if not disable_prod_tests:

    @pytest.fixture()
    def test_dcxo_calibration(request):
        yield dcxo_calibrate


@pytest.fixture()
def test_attribute_multiple_values(request):
    yield attribute_multiple_values


@pytest.fixture()
def test_attribute_multiple_values_error(request):
    yield attribute_multiple_values_error


@pytest.fixture()
def test_attribute_multiple_values_with_depends(request):
    yield attribute_multiple_values_with_depends


@pytest.fixture()
def test_attribute_readonly_with_depends(request):
    yield attribute_readonly_with_depends


@pytest.fixture()
def test_attribute_write_only_str_with_depends(request):
    yield attribute_write_only_str_with_depends


@pytest.fixture
def test_attribute_write_only_str(request):
    yield attribute_write_only_str


@pytest.fixture
def test_attribute_check_range_readonly_with_depends(request):
    yield attribute_check_range_readonly_with_depends


@pytest.fixture()
def test_dma_dac_zeros(request):
    yield dma_dac_zeros


@pytest.fixture()
def test_dds_two_tone(request):
    yield dds_two_tone


@pytest.fixture()
def test_verify_overflow(request):
    yield verify_overflow


@pytest.fixture()
def test_verify_underflow(request):
    yield verify_underflow


@pytest.fixture
def test_attribute_single_value_device_name_channel_readonly(request):
    yield attribute_single_value_device_name_channel_readonly


@pytest.fixture
def test_attribute_write_only_str_device_channel(request):
    yield attribute_write_only_str_device_channel


@pytest.fixture
def test_attribute_single_value_range_channel(request):
    yield attribute_single_value_range_channel


@pytest.fixture
def test_attribute_multiple_values_device_channel(request):
    yield attribute_multiple_values_device_channel


@pytest.fixture
def test_attribute_multiple_values_available_readonly(request):
    yield attribute_multiple_values_available_readonly


@pytest.fixture
def test_attribute_single_value_channel_readonly(request):
    yield attribute_single_value_channel_readonly


@pytest.fixture()
def test_attribute_check_range_singleval_with_depends(request):
    yield attribute_check_range_singleval_with_depends


@pytest.fixture()
def test_attribute_single_value_boolean_readonly(request):
    yield attribute_single_value_boolean_readonly


#########################################
# JESD204 Fixtures


@pytest.fixture()
def test_verify_links(request):
    yield verify_links


@pytest.fixture()
def test_verify_links_errors_stable(request):
    yield verify_links_errors_stable
