import pytest

import adi

hardware = "ad7124-8"
classname = "adi.ad7124"


#########################################
@pytest.mark.iio_hardware(hardware)
def test_ad7124_8_channels(iio_uri):
    dev = adi.ad7124(uri=iio_uri)

    for chan_i in range(16):
        assert dev.rx_channel_names[chan_i] == f"voltage{str(chan_i)}"
