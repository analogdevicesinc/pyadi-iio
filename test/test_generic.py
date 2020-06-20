import pytest

hardware = ["pluto", "adrv9361", "fmcomms2"]
classname = ""


#########################################
# fmt: off
@pytest.mark.skip(reason="This is only used as a template")
@pytest.mark.parametrize("hardware", [(hardware)])
@pytest.mark.parametrize(
    "attrtype, dev_name, chan_name, inout, attr, start, stop, step, tol, repeats",
    [
        ("channel", "ad9361-phy", "voltage0", False, "hardwaregain", -89.75, 0.0, 0.25, 0, 100),
        ("channel", "ad9361-phy", "TX_LO", True, "frequency", 47000000, 6000000000, 1, 4, 100),
        ("channel", "ad9361-phy", "RX_LO", True, "frequency", 70000000, 6000000000, 1, 4, 100)
    ],
)
def test_iio_attr(
    test_iio_attribute_single_value,
    classname,
    hardware,
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
        classname,
        hardware,
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
