import pytest

hardware = "adar3002"
classname = "adi.adar3002"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val",
    [
        ("amp_bias_mute_ELV", [1, 1, 1, 1]),
        ("amp_bias_mute_ELV", [2, 2, 2, 2]),
        ("amp_bias_mute_ELV", [3, 3, 3, 3]),
        ("amp_bias_operational_ELH", [1, 1, 1, 1]),
        ("amp_bias_operational_ELH", [2, 2, 2, 2]),
        ("amp_bias_operational_ELH", [3, 3, 3, 3]),
        ("amp_bias_operational_ELV", [1, 1, 1, 1]),
        ("amp_bias_operational_ELV", [2, 2, 2, 2]),
        ("amp_bias_operational_ELV", [3, 3, 3, 3]),
        ("amp_bias_reset_ELV", [1, 1, 1, 1]),
        ("amp_bias_reset_ELV", [2, 2, 2, 2]),
        ("amp_bias_reset_ELV", [3, 3, 3, 3]),
        ("amp_bias_sleep_ELH", [1, 1, 1, 1]),
        ("amp_bias_sleep_ELH", [2, 2, 2, 2]),
        ("amp_bias_sleep_ELH", [3, 3, 3, 3]),
        ("amp_bias_reset_ELV", [1, 1, 1, 1]),
        ("amp_bias_reset_ELV", [2, 2, 2, 2]),
        ("amp_bias_reset_ELV", [3, 3, 3, 3]),
        ("amp_en_mute_ELV", [1, 1, 1, 1]),
        ("amp_en_mute_ELV", [0, 0, 0, 0]),
        ("amp_en_operational_ELH", [1, 1, 1, 1]),
        ("amp_en_operational_ELH", [0, 0, 0, 0]),
        ("amp_en_operational_ELV", [1, 1, 1, 1]),
        ("amp_en_operational_ELV", [0, 0, 0, 0]),
        ("amp_en_reset_ELV", [1, 1, 1, 1]),
        ("amp_en_reset_ELV", [0, 0, 0, 0]),
        ("amp_en_sleep_ELH", [1, 1, 1, 1]),
        ("amp_en_sleep_ELH", [0, 0, 0, 0]),
        ("amp_en_sleep_ELV", [1, 1, 1, 1]),
        ("amp_en_sleep_ELV", [0, 0, 0, 0]),
    ],
)
def test_adar1000_str_attr(
    test_attribute_multipe_values, iio_uri, classname, attr, val
):
    test_attribute_multipe_values(iio_uri, classname, attr, val, 0)
