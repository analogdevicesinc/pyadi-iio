import pytest

hardware = "ltc2664"
classname = "adi.ltc2664"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("raw", 0, 65000, 1000, 1, 3, "voltage0"),  # Standard Channel
        ("raw0", 0, 65000, 1000, 1, 3, "voltage1"),  # Toggle Channel
        ("raw1", 0, 65000, 1000, 1, 3, "voltage1"),  # Toggle Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage2"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage3"),  # Standard Channel
    ],
)
def test_ltc2688_raw_attr(
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
