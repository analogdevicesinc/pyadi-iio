import pytest

hardware = "xmw_tx_platform"
classname = "adi.xmw_tx_platform"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, param_set",
    [
        ("output_freq_range", 0, 1, 1, 0, 10),
        ("output_freq_MHz", 2000, 24000, 500, 0, 10),
        ("output_bpf_freq_MHz", 2000, 17000, 500, 1000, 10),
        ("fixed_pll_freq_MHz", 11000, 28000, 500, 100, 10),
        ("tunable_pll_freq_MHz", 11000, 28000, 500, 100, 10),
        ("if_attenuation_decimal", 0, 63, 1, 1, 10),
    ],
)
def test_xmw_tx_platform_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    param_set,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, param_set
    )
