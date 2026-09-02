from decimal import Decimal

import pytest

import adi

hardware = "ad5686"
classname = "adi.ad5686"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", ["voltage0", "voltage1", "voltage2", "voltage3"])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol, repeats", [("raw", 0, 65535, 10000, 0, 3)],
)
def test_ad5686_raw_attr(
    test_attribute_single_value,
    iio_uri,
    classname,
    channel,
    attr,
    start,
    stop,
    step,
    tol,
    repeats,
):
    test_attribute_single_value(
        iio_uri, classname, attr, start, stop, step, tol, repeats, channel
    )


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
def test_ad5686_powerdown_mode_roundtrip(iio_uri, channel):
    dev = adi.ad5686(iio_uri)
    ch = dev.channel[channel]
    for mode in adi.ad5686.powerdown_mode:
        ch.powerdown_mode = mode
        assert ch.powerdown_mode is mode


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
def test_ad5686_powerdown_toggle(iio_uri, channel):
    dev = adi.ad5686(iio_uri)
    ch = dev.channel[channel]
    ch.powerdown = 1
    assert ch.powerdown == 1
    ch.powerdown = 0
    assert ch.powerdown == 0


#########################################
@pytest.mark.iio_hardware(hardware)
def test_ad5686_channel_voltage_roundtrip(iio_uri):
    dev = adi.ad5686(iio_uri)
    scale = Decimal(dev.channel[0].scale)

    for target in (0.5, 1.0, 1.5):
        dev.channel[0].voltage = target
        expected_raw = int(1000 * Decimal(target) / scale)
        assert dev.channel[0].raw == expected_raw
        assert dev.channel[0].voltage == pytest.approx(target, abs=float(scale) / 1000)


#########################################
@pytest.mark.iio_hardware(hardware)
def test_ad5686_scale_available_and_set_gain(iio_uri):
    dev = adi.ad5686(iio_uri)
    scales = dev.channel[0].scale_available
    assert len(scales) == 2
    assert scales[0] < scales[1]

    dev.set_gain(adi.ad5686.gain.DOUBLE)
    assert Decimal(dev.channel[0].scale) == scales[1]

    dev.set_gain(adi.ad5686.gain.NORMAL)
    assert Decimal(dev.channel[0].scale) == scales[0]


#########################################
@pytest.mark.iio_hardware(hardware)
def test_ad5686_set_gain_rejects_single_scale_device(iio_uri):
    dev = adi.ad5686(iio_uri)
    dev._scales = dev._scales[:1]
    with pytest.raises(ValueError):
        dev.set_gain(adi.ad5686.gain.DOUBLE)
