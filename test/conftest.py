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
