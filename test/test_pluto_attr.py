import random

import iio

import numpy as np
import pytest
from adi import Pluto

dev_checked = False
found_dev = False


def check_pluto():
    # Try USB contexts first
    contexts = iio.scan_contexts()
    for c in contexts:
        if "PlutoSDR" in contexts[c]:
            return True
    # Try auto discover
    try:
        iio.Context("ip:pluto.local")
        return True
    except Exception as e:
        print(e)
        return False


def check_dev():
    global dev_checked
    global found_dev
    if not dev_checked:
        found_dev = check_pluto()
        dev_checked = True
    return found_dev


scalar_properties = [
    ("tx_hardwaregain", -89.75, 0.0, 0.25, 0),
    ("rx_lo", 70000000, 6000000000, 1, 8),
    ("tx_lo", 70000000, 6000000000, 1, 8),
    ("sample_rate", 2084000, 30720000, 1, 4),
]


@pytest.mark.skipif(not check_dev(), reason="PlutoSDR not connected")
@pytest.mark.parametrize("attr, start, stop, step, tol", scalar_properties)
def test_pluto_attribute_single_value(attr, start, stop, step, tol):
    sdr = Pluto()
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


string_properties = [("loopback", 2, 0), ("loopback", 1, 0), ("loopback", 0, 0)]


@pytest.mark.skipif(not check_dev(), reason="PlutoSDR not connected")
@pytest.mark.parametrize("attr,val,tol", string_properties)
def test_pluto_attribute_single_value_str(attr, val, tol):
    sdr = Pluto()
    # Check hardware
    setattr(sdr, attr, val)
    rval = float(getattr(sdr, attr))
    del sdr
    if abs(val - rval) > tol:
        print("Failed to set: " + attr)
        print("Set: " + str(val))
        print("Got: " + str(rval))
    assert abs(val - rval) <= tol
