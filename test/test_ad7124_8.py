import re

import pytest

import adi

hardware = "ad7124-8"
classname = "adi.ad7124"


#########################################
@pytest.mark.iio_hardware(hardware)
def test_ad7124_8_channels(iio_uri):
    dev = adi.ad7124(uri=iio_uri)

    n_channels = len(dev.rx_channel_names)
    assert n_channels > 0

    for name in dev.rx_channel_names:
        assert re.match(
            r"^(voltage\d+(-voltage\d+)?|temp)$", name
        ), f"Unexpected channel name: {name}"

    voltage_channels = [n for n in dev.rx_channel_names if n.startswith("voltage")]
    is_differential = "-" in voltage_channels[0] if voltage_channels else False

    if is_differential:
        for name in voltage_channels:
            assert "-" in name, f"Mixed single-ended/differential: {name}"
    else:
        for name in voltage_channels:
            assert "-" not in name, f"Mixed single-ended/differential: {name}"

    expected_channel_names = [
        ch.id
        for ch in dev._ctrl.channels
        if ch.id not in dev._ignore_channels and ("temp" in ch.id or "voltage" in ch.id)
    ]
    assert [ch.name for ch in dev.channel] == expected_channel_names
    for ch in dev.channel:
        assert ch is getattr(dev, ch.name)
        assert type(ch).__name__ == (
            "_temp_channel" if "temp" in ch.name else "_ad7124_channel"
        )
        assert hasattr(type(ch), "raw")
        assert hasattr(type(ch), "scale")

    for name in dev.rx_channel_names:
        assert getattr(dev, name) in dev.channel

    voltage_indices = [
        i for i, n in enumerate(dev.rx_channel_names) if n.startswith("voltage")
    ]
    for i in voltage_indices:
        getattr(dev, dev.rx_channel_names[i]).sampling_frequency = 4800


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [[1, 2, 3, 4]])
def test_ad7124_8_rx_data(test_dma_rx, iio_uri, classname, channel, request):
    if request.config.getoption("emu"):
        pytest.skip("AD7124 emulation context does not provide DMA buffer data")
    test_dma_rx(iio_uri, classname, channel, buffer_size=128)
