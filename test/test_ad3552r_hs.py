import pytest

hardware = ["ad3552r", "ad3551r", "ad3542r", "ad3541r"]
classname = "adi.ad3552r_hs"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("raw", 0, 4000, 1000, 1, 3, "voltage0"),
        ("raw", 0, 4000, 1000, 1, 3, "voltage1"),
    ],
)
def test_ad3552r_hs_raw_attr(
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
