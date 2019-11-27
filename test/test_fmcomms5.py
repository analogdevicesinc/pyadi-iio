import random
import test.iio_scanner as iio_scanner

import iio

import numpy as np
import pytest
from adi import FMComms5

URI = "ip:analog"
dev_checked = False
found_dev = False


def check_dev(name):
    global dev_checked
    global found_dev
    if not dev_checked:
        found_dev, board = iio_scanner.find_device(name)
        if found_dev:
            global URI
            URI = board.uri
        dev_checked = True
    return found_dev


@pytest.mark.skipif(not check_dev("fmcomms5"), reason="FMComms5 not connected")
def testFMComms5_ADCData():
    # See if we can get non-zero data from ADC
    global URI
    s = FMComms5(uri=URI)
    data = s.rx()
    for k in data:
        s = np.sum(np.abs(k))
        assert s > 0


scalar_properties = [("sample_rate", 10000000, 20000000, 1000000, 0)]


@pytest.mark.skipif(not check_dev("fmcomms5"), reason="FMComms5 not connected")
@pytest.mark.parametrize("attr, start, stop, step, tol", scalar_properties)
def test_FMComms5_attribute_single_value(attr, start, stop, step, tol):
    global URI
    sdr = FMComms5(uri=URI)
    # Pick random number in operational range
    numints = int((stop - start) / step)
    ind = random.randint(0, numints + 1)
    val = start + step * ind
    # Check hardware
    setattr(sdr, attr, val)
    rval = float(getattr(sdr, attr))
    del sdr
    if abs(val - rval) > tol:
        print("Failed to set: " + attr)
        print("Set: " + str(val))
        print("Got: " + str(rval))
    assert abs(val - rval) <= tol
