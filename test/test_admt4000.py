import iio
import pytest

hardware = ["admt4000", "admt4000ard1z", "admt4000ard2z"]
classname = "adi.admt4000"


def do_mock():
    def mock_set_trigger(self, value):
        pass

    # Mock the _set_trigger method in iio.Device
    iio.Device._set_trigger = mock_set_trigger


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, [0, 1, 2]])
def test_admt4000_rx_data(test_dma_rx, iio_uri, classname, channel):
    do_mock()
    test_dma_rx(iio_uri, classname, channel, buffer_size=2 ** 5)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "channel, attr",
    [
        ("turns", "raw"),
        ("angle", "raw"),
        ("temp", "raw"),
        ("cosine", "raw"),
        ("sine", "raw"),
        ("radius", "raw"),
        ("turns", "scale"),
        ("angle", "scale"),
        ("temp", "scale"),
        ("radius", "scale"),
        ("temp", "offset"),
    ],
)
def test_admt4000_attr_readonly_channel(
    test_attribute_single_value_channel_readonly, iio_uri, classname, channel, attr
):
    do_mock()
    test_attribute_single_value_channel_readonly(iio_uri, classname, channel, attr)
