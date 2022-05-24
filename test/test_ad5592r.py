import pytest

hardware = "ad5592r"
classname = "adi.ad5592r"

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7])
def test_ad5593_test(iio_uri, classname, channel):
    test_ad5593_test(iio_uri, classname, channel)