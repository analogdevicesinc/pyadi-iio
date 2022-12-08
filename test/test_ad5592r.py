import pytest

hardware = "ad5592r"
classname = "adi.ad5592r"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("raw", 0, 4000, 1000, 1, 3, "voltage0_dac"),
        ("raw", 0, 4000, 1000, 1, 3, "voltage2_dac"),
        ("raw", 0, 4000, 1000, 1, 3, "voltage3_dac"),
    ],
)
def test_ad5592r_raw_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
    sub_channel,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, sub_channel
    )
