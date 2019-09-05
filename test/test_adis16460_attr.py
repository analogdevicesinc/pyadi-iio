import random

import iio

import numpy as np
import pytest
from adi import adis16460

dev_checked = False
found_dev = False

URI = 'ip:analog'

def check_adis16460():
    # Try auto discover
    try:
        iio.Context(URI)
        return True
    except Exception as e:
        print(e)
        return False


def check_dev():
    global dev_checked
    global found_dev
    if not dev_checked:
        found_dev = check_adis16460()
        dev_checked = True
    return found_dev


@pytest.mark.skipif(not check_dev(), reason="ADIS16460 not connected")
def testADIS16460_SensorData():
    # See if we can get non-zero data from ADC
    s = adis16460(uri=URI)
    data = s.rx()
    for k in data:
        s = np.sum(np.abs(k))
        assert s > 0


scalar_properties = [("sample_rate", 1, 4096, 0)]


@pytest.mark.skipif(not check_dev(), reason="ADIS16460 not connected")
@pytest.mark.parametrize("attr, start, stop, tol", scalar_properties)
def test_adis16460_attribute_single_value(attr, start, stop, tol):
    sdr = adis16460(uri=URI)
    # Pick random number in operational range
    nums = []
    for k in range(0, 12):
        nums.append(2 ** k)
    ind = random.randint(0, len(nums))
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
