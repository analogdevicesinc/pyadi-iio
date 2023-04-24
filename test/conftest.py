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

import adi
import numpy as np
import pytest

try:
    from test.scpi import dcxo_calibrate

    disable_prod_tests = False
except ImportError:
    disable_prod_tests = True


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
def test_attribute_multipe_values(request):
    yield attribute_multipe_values


@pytest.fixture()
def test_attribute_multipe_values_with_depends(request):
    yield attribute_multipe_values_with_depends


@pytest.fixture()
def test_attribute_write_only_str_with_depends(request):
    yield attribute_write_only_str_with_depends


@pytest.fixture
def test_attribute_write_only_str(request):
    yield attribute_write_only_str


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
