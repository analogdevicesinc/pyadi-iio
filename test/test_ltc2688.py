import pytest

hardware = "ltc2688"
classname = "adi.ltc2688"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats, sub_channel",
    [
        ("raw", 0, 65000, 1000, 1, 3, "voltage0"),  # Dither Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage1"),  # Standard Channel
        ("raw0", 0, 65000, 1000, 1, 3, "voltage2"),  # Toggle Channel
        ("raw1", 0, 65000, 1000, 1, 3, "voltage2"),  # Toggle Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage3"),  # Dither Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage4"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage5"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage6"),  # Standard Channel
        ("raw1", 0, 65000, 1000, 1, 3, "voltage7"),  # Toggle Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage8"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage9"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage10"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage11"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage12"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage13"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage14"),  # Standard Channel
        ("raw", 0, 65000, 1000, 1, 3, "voltage15"),  # Standard Channel
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
