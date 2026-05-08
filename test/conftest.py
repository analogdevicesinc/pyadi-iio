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
# Active only when LG_ENV is set (CI hardware runs).  When unset,
# pytest-libiio's iio_uri fixture wins and the existing emu/scan path
# is untouched.  See .github/workflows/hardware-test.yml.
import os as _os

_LABGRID_MODE = bool(_os.environ.get("LG_ENV"))

if _LABGRID_MODE:

    @pytest.fixture(scope="session")
    def labgrid_iio_uri(strategy, target):
        # `strategy` and `target` come from labgrid.pytestplugin (auto-
        # loaded via the pytest11 entry point when LG_ENV is set).
        # `Status.shell` is preferred over `Status.booted` because
        # BootFabric's shell transition runs `udhcpc -i eth0` and
        # updates NetworkService.address to the real DHCP-assigned IP.
        # BootFPGASoC's shell just activates the shell driver; the
        # exporter's static NetworkService.address can be stale, so we
        # always re-read the IP from the booted board's `ip addr`.
        strategy.transition("shell")

        shell = target.get_driver("CommandProtocol")
        # `ip route get` returns the source IP for the default route —
        # the address the board uses for outbound traffic, which is the
        # correct one for the runner-to-board IIO connection.
        out, _, rc = shell.run(
            "ip -4 -o route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if($i==\"src\") print $(i+1); exit}'"
        )
        ip = (out[0].strip() if out else "") if rc == 0 else ""
        if not ip:
            pytest.fail(f"could not extract IP from board (rc={rc} out={out!r})")
        uri = f"ip:{ip}"

        # Even with the right IP, IIO daemon on the board may need a
        # few seconds after shell-up before it accepts connections.
        import time as _t
        import iio as _iio
        deadline = _t.time() + 60
        last_err = None
        while _t.time() < deadline:
            try:
                _iio.Context(uri)
                break
            except Exception as e:
                last_err = e
                _t.sleep(2)
        else:
            pytest.fail(f"IIO context at {uri} unreachable within 60s: {last_err!r}")

        yield uri

    @pytest.fixture(scope="function")
    def iio_uri(labgrid_iio_uri):
        # Per-board test selection is already handled by the workflow's
        # `pytest -m <marker>` filter against the place's manifest entry,
        # so no additional skip-logic is needed here.
        return labgrid_iio_uri


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
