import iio

import adi
import pytest

hardware = ["packrf", "adrv9364", "fmcomms4", "ad9364", "adrv9361","fmcomms2","fmcomms3","ad9361",]
classname = "adi.ad9361"

@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_dcxo(test_dcxo_calibration, classname, iio_uri):
    test_dcxo_calibration(classname, iio_uri)