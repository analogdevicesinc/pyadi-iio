import random
import test.iio_scanner as iio_scanner

import iio

import numpy as np
import pytest
from adi import adis16460

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


@pytest.mark.skipif(not check_dev("packrf"), reason="ADIS16460 not connected")
def testADIS16460_SensorData():
    # See if we can get non-zero data from ADC
    global URI
    s = adis16460(uri=URI)
    data = s.rx()
    for k in data:
        s = np.sum(np.abs(k))
        assert s > 0


scalar_properties = [("sample_rate", 1, 4096, 0)]


@pytest.mark.skipif(not check_dev("packrf"), reason="ADIS16460 not connected")
@pytest.mark.parametrize("attr, start, stop, tol", scalar_properties)
def test_adis16460_attribute_single_value(attr, start, stop, tol):
    global URI
    sdr = adis16460(uri=URI)
    # Pick random number in operational range
    nums = []
    for k in range(0, 12):
        nums.append(2 ** k)
    ind = random.randint(0, len(nums) - 1)
    val = nums[ind]
    # Check hardware
    setattr(sdr, attr, val)
    rval = float(getattr(sdr, attr))
    del sdr
    if abs(val - rval) > tol:
        print("Failed to set: " + attr)
        print("Set: " + str(val))
        print("Got: " + str(rval))
    assert abs(val - rval) <= tol
