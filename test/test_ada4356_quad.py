import pytest

import adi
from adi.ada4356_align import ALIGN_GUARD

hardware = "ada4356_quad"
classname = "adi.ada4356_quad"
labels = ["A", "B", "C", "D"]


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("attr", ["gain_mode", "filter_mode"])
def test_ada4356_quad_mode(iio_uri, attr):
    dev = adi.ada4356_quad(uri=iio_uri)
    available = getattr(dev, attr + "_available")
    assert available
    for val in available:
        setattr(dev, attr, val)
        assert getattr(dev, attr) == {c: val for c in labels}


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("attr", ["gain_mode", "filter_mode"])
def test_ada4356_quad_mode_invalid(iio_uri, attr):
    dev = adi.ada4356_quad(uri=iio_uri)
    with pytest.raises(ValueError):
        setattr(dev, attr, "not_a_mode")


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("attr", ["gain_mode", "filter_mode"])
def test_ada4356_quad_mode_resets_alignment(iio_uri, attr):
    dev = adi.ada4356_quad(uri=iio_uri)
    dev.set_alignment([0, 1, 2, 3])
    setattr(dev, attr, getattr(dev, attr + "_available")[0])
    assert dev.alignment is None


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("size", [1024, 8192, 65536])
def test_ada4356_quad_rx_buffer_size(iio_uri, size):
    dev = adi.ada4356_quad(uri=iio_uri)
    dev.rx_buffer_size = size
    assert dev.rx_buffer_size == size
    assert [ch.rx_buffer_size for ch in dev.channels] == [size] * 4

    # An active alignment captures a guard region on top of the requested size.
    dev.set_alignment([0, 1, 2, 3])
    assert dev.rx_buffer_size == size
    assert [ch.rx_buffer_size for ch in dev.channels] == [size + ALIGN_GUARD] * 4


#########################################
@pytest.mark.iio_hardware(hardware)
def test_ada4356_quad_sampling_frequency(iio_uri):
    dev = adi.ada4356_quad(uri=iio_uri)
    assert dev.sampling_frequency > 0


#########################################
# The class reads rate and *_available from channel A only; check B..D agree.
@pytest.mark.iio_hardware(hardware)
def test_ada4356_quad_channels_match(iio_uri):
    dev = adi.ada4356_quad(uri=iio_uri)
    rates = [float(ch.sampling_frequency) for ch in dev.channels]
    assert rates == [dev.sampling_frequency] * 4
    for attr in ["gain_mode_available", "filter_mode_available"]:
        ref = getattr(dev, attr)
        for ch in dev.channels:
            assert ch._get_iio_attr_str("voltage0", attr, False).split() == ref


#########################################
@pytest.mark.iio_hardware(hardware)
def test_ada4356_quad_channel_scale(iio_uri):
    dev = adi.ada4356_quad(uri=iio_uri)
    assert all(ch.channel[0].scale > 0 for ch in dev.channels)


#########################################
# rx_raw() arms every DMA on the TDD sync before capturing.
@pytest.mark.iio_hardware(hardware)
def test_ada4356_quad_rx_raw_arms_all(iio_uri):
    dev = adi.ada4356_quad(uri=iio_uri)
    for ch in dev.channels:
        assert "arm" in ch._get_iio_dev_attr_str("sync_start_enable_available").split()
    dev.rx_buffer_size = 1024
    data = dev.rx_raw()
    assert [len(x) for x in data] == [1024] * 4


#########################################
# Two values each: the first differs from the XML default so a read-back proves
# the write, the last is boot_align's setup so a board is left usable.
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "attr, vals",
    [
        ("frame_length_raw", [62500000, 125000000]),
        ("startup_delay_raw", [10, 0]),
        ("internal_sync_period_raw", [10, 0]),
        ("burst_count", [1, 0]),
        ("sync_external", [True, False]),
        ("sync_internal", [True, False]),
        ("enable", [False]),  # never armed from a test
    ],
)
def test_ada4356_quad_tdd(iio_uri, attr, vals):
    dev = adi.ada4356_quad(uri=iio_uri)
    for val in vals:
        setattr(dev.tdd, attr, val)
        assert getattr(dev.tdd, attr) == val


#########################################
# ms variants end on the raw values above at the 125 MHz TDD clock.
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "attr, vals",
    [
        ("frame_length_ms", [500, 1000]),
        ("startup_delay_ms", [1, 0]),
        ("internal_sync_period_ms", [1, 0]),
    ],
)
def test_ada4356_quad_tdd_ms(iio_uri, attr, vals):
    dev = adi.ada4356_quad(uri=iio_uri)
    for val in vals:
        setattr(dev.tdd, attr, val)
        assert getattr(dev.tdd, attr) == pytest.approx(val, rel=1e-3)
    assert dev.tdd.state >= 0


#########################################
# Channel 0 drives trig_fmc_out (the external laser trigger): never enable it.
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("channel", range(5))
@pytest.mark.parametrize(
    "attr, vals",
    [
        ("on_raw", [150, 100]),
        ("off_raw", [250, 200]),
        ("polarity", [True, False]),
        ("enable", [False, True]),
    ],
)
def test_ada4356_quad_tdd_channel(iio_uri, channel, attr, vals):
    if channel == 0 and attr == "enable":
        vals = [False]
    dev = adi.ada4356_quad(uri=iio_uri)
    for val in vals:
        setattr(dev.tdd.channel[channel], attr, val)
        assert getattr(dev.tdd.channel[channel], attr) == val


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("channel", range(5))
@pytest.mark.parametrize(
    "attr, vals", [("on_ms", [0.0012, 0.0008]), ("off_ms", [0.002, 0.0016])],
)
def test_ada4356_quad_tdd_channel_ms(iio_uri, channel, attr, vals):
    dev = adi.ada4356_quad(uri=iio_uri)
    for val in vals:
        setattr(dev.tdd.channel[channel], attr, val)
        assert getattr(dev.tdd.channel[channel], attr) == pytest.approx(val, rel=1e-3)


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ada4356_quad_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)
