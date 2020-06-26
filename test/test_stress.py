import pytest

hardware = ["adrv9361", "fmcomms2"]
classname = "adi.ad9361"


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
@pytest.mark.parametrize("repeats", [100])
def test_ad9361_stress_context_creation(
    test_stress_context_creation, classname, hardware, channel, repeats
):
    test_stress_context_creation(classname, hardware, channel, repeats)


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
@pytest.mark.parametrize("repeats", [100])
def test_ad9361_stress_rx_buffer(
    test_stress_rx_buffer_creation, classname, hardware, channel, repeats
):
    test_stress_rx_buffer_creation(classname, hardware, channel, repeats)


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
@pytest.mark.parametrize("repeats", [100])
def test_ad9361_stress_tx_buffer(
    test_stress_tx_buffer_creation, classname, hardware, channel, repeats
):
    test_stress_tx_buffer_creation(classname, hardware, channel, repeats)


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
@pytest.mark.parametrize("buffer_sizes", [[x * x for x in range(4, 1024)]])
def test_ad9361_stress_rx_buffer_length(
    test_stress_rx_buffer_length, classname, hardware, channel, buffer_sizes
):
    test_stress_rx_buffer_length(classname, hardware, channel, buffer_sizes)
