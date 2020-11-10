import pytest

hardware = "adrv9002"
classname = ""


#########################################
# fmt: off
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "attrtype, dev_name, chan_name, inout, attr, start, stop, step, tol, repeats",
    [
        ("channel", "adrv9002-phy", "voltage0", False, "hardwaregain", -89.75, 0.0, 0.25, 0, 100),
        ("channel", "adrv9002-phy", "altvoltage0", True, "RX1_LO_frequency", 70000000, 6000000000, 1, 4, 100),
        ("channel", "adrv9002-phy", "altvoltage1", True, "RX2_LO_frequency", 70000000, 6000000000, 1, 4, 100)
    ],
)
def test_iio_attr(
    test_iio_attribute_single_value,
    iio_uri,
    attrtype,
    dev_name,
    chan_name,
    inout,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
):
    test_iio_attribute_single_value(
        iio_uri,
        attrtype,
        dev_name,
        chan_name,
        inout,
        attr,
        start,
        stop,
        step,
        tol,
        repeats,
    )
# fmt: on
