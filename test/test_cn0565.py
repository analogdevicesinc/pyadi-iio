import pytest

import adi

hardware = ["cn0565"]
classname = "adi.cn0565"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats",
    [
        ("electrode_count", 0, 64, 8, 1, 1),
        ("force_distance", 0, 8, 1, 0, 0),
        ("sense_distance", 0, 8, 1, 0, 0),
    ],
)
def test_cn0565_attrs(
    test_attribute_single_value,
    iio_uri,
    classname,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
):

    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats
    )


@pytest.mark.iio_hardware(hardware)
def test_cn0565_preserves_ad5940_channel_binding(iio_uri):
    """The BIA wrapper remains bound to AD5940 after ADG2128 initialization."""
    with adi.cn0565(uri=iio_uri) as dev:
        assert dev._rxadc.name == "ad5940"
        assert dev._ctrl.name == "adg2128"
        assert list(dev.channel) == ["voltage0"]
        assert dev.channel["voltage0"]._ctrl is dev._rxadc
