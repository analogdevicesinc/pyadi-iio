import adi

import pytest

hardware = "cn0532"
classname = "adi.cn0532"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "sample_rate", [1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000, 256000]
)
def test_cn0532_attr(iio_uri, sample_rate):
    xl = adi.cn0532(iio_uri)
    xl.sample_rate = sample_rate
    del xl


#########################################
@pytest.mark.iio_hardware(hardware)
def test_cn0532_change_sample_rate_with_data(iio_uri):
    xl = adi.cn0532(iio_uri)
    xl.sample_rate = 128000
    data = xl.rx()
    xl.sample_rate = 256000
    data = xl.rx()
    xl.sample_rate = 128000
    data = xl.rx()
    xl.sample_rate = 256000
    data = xl.rx()
    del xl


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_cn0532_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)
