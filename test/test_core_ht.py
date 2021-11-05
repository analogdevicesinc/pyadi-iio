from hypothesis import HealthCheck, settings, given, strategies as st

import pytest
import adi

# These are hypothesis based tests meant to validated generic APIs at the core classes


@pytest.mark.iio_hardware("pluto_rev_c", True)
@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@given(f=st.integers(min_value=-3, max_value=71))
def test_iio_attr_interface(f, iio_uri):
    dev = adi.Pluto(iio_uri)
    dev.gain_control_mode_chan0 = "manual"
    dev.rx_hardwaregain_chan0 = f
    fhat = dev.rx_hardwaregain_chan0
    del dev
    assert fhat == f


@pytest.mark.iio_hardware("pluto_emulated")
@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@given(f=st.floats(allow_nan=False, allow_infinity=False))
def test_iio_attr_interface_emu_read(f, iio_uri):
    dev = adi.Pluto(iio_uri)
    dev._set_iio_attr("voltage0", "hardwaregain", False, f)
    fhat = dev.rx_hardwaregain_chan0
    del dev
    assert fhat == f


@pytest.mark.iio_hardware("pluto_emulated")
@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@given(f=st.floats(allow_nan=False, allow_infinity=False))
def test_iio_attr_interface_emu_float(f, iio_uri):
    dev = adi.Pluto(iio_uri)
    dev._set_iio_attr_float("voltage0", "hardwaregain", False, f)
    fhat = dev._get_iio_attr("voltage0", "hardwaregain", False)
    del dev
    assert fhat == f


@pytest.mark.iio_hardware("pluto_emulated")
@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@given(f=st.floats(allow_nan=False, allow_infinity=False))
def test_iio_attr_interface_emu_float_write(f, iio_uri):
    dev = adi.Pluto(iio_uri)
    dev.rx_hardwaregain_chan0 = f
    fhat = dev._get_iio_attr("voltage0", "hardwaregain", False)
    del dev
    assert fhat == f


@pytest.mark.iio_hardware("pluto_emulated")
@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@given(
    f1=st.floats(allow_nan=False, allow_infinity=False),
    f2=st.floats(allow_nan=False, allow_infinity=False),
)
def test_iio_attr_interface_emu_float_write(f1, f2, iio_uri):
    dev = adi.Pluto(iio_uri)
    dev.dds_single_tone(f1, f2)
    phases = dev.dds_phases
    del dev
    assert phases[0] == 90000
    for i, phase in enumerate(phases):
        if i == 0:
            continue
        assert phase == 0
