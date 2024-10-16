import sys
import time
from test.globals import *

import iio

import adi
import numpy as np
import pytest


def pytest_configure(config):
    # Add customer marks to ini to remove warnings
    from test import test_map as tm

    test_map = tm.get_test_map()
    vals = []
    for k in test_map:
        vals = vals + test_map[k]
    keys = np.unique(np.array(vals))
    for k in keys:
        config.addinivalue_line("markers", k.replace("-", "_"))

    # Add custom marks to ini for OBS channels
    config.addinivalue_line(
        "markers", "obs_required: mark tests that require observation data paths"
    )
    config.addinivalue_line(
        "markers", "no_obs_required: mark tests that require observation data paths"
    )
    config.addinivalue_line("markers", "lvds_test: mark tests for LVDS")
    config.addinivalue_line("markers", "cmos_test: mark tests for CMOS")


def pytest_collection_modifyitems(items):
    # Map HDL project names to tests as markers
    from test import test_map as tm

    test_map = tm.get_test_map()
    test_map_keys = test_map.keys()

    for item in items:
        if item.originalname:
            for key in test_map_keys:
                if key in item.originalname:
                    for marker in test_map[key]:
                        item.add_marker(marker.replace("-", "_"))
                    break


def pytest_addoption(parser):
    parser.addoption(
        "--obs-enable",
        action="store_true",
        help="Run tests that use observation data paths",
    )
    parser.addoption(
        "--lvds", action="store_true", help="Run tests for LVDS",
    )
    parser.addoption(
        "--cmos", action="store_true", help="Run tests for CMOS",
    )
    parser.addoption(
        "--username", default="root", help="SSH login username",
    )
    parser.addoption(
        "--password", default="analog", help="SSH login password",
    )


def pytest_runtest_setup(item):
    # Handle observation based devices
    obs = item.config.getoption("--obs-enable")
    marks = [mark.name for mark in item.iter_markers()]
    if not obs and "obs_required" in marks:
        pytest.skip(
            "Testing requiring observation disabled. Use --obs-enable flag to enable"
        )
    if obs and "no_obs_required" in marks:
        pytest.skip("Testing requiring observation enabled. Skipping this test")

    # Handle CMOS and LVDS tests
    cmos = item.config.getoption("--cmos")
    lvds = item.config.getoption("--lvds")
    marks = [mark.name for mark in item.iter_markers()]
    if cmos and lvds:
        pytest.skip(
            "CMOS and LVDS tests can't be performed simultaneously. Use either the --cmos or the --lvds flag one at a time.",
            allow_module_level=True,
        )
    elif not cmos and "cmos_test" in marks:
        pytest.skip("CMOS testing disabled. Use --cmos flag to enable")
    elif not lvds and "lvds_test" in marks:
        pytest.skip("LVDS testing disabled. Use --lvds flag to enable")


def pytest_generate_tests(metafunc):
    if "username" in metafunc.fixturenames:
        metafunc.parametrize("username", [metafunc.config.getoption("username")])
    if "password" in metafunc.fixturenames:
        metafunc.parametrize("password", [metafunc.config.getoption("password")])


#################################################
def dev_interface(
    uri, classname, val, attr, tol, sub_channel=None, sleep=0, readonly=False
):
    sdr = eval(classname + "(uri='" + uri + "')")
    # Check hardware
    if not hasattr(sdr, attr):
        raise AttributeError(attr + " not defined in " + classname)

    rval = getattr(sdr, attr)
    is_list = isinstance(rval, list)
    if is_list:
        l = len(rval)
        val = [val] * l

    setattr(sdr, attr, val)
    if sleep > 0:
        time.sleep(sleep)
    rval = getattr(sdr, attr)

    if not isinstance(rval, str) and not is_list:
        rval = float(rval)
        for _ in range(5):
            setattr(sdr, attr, val)
            time.sleep(0.3)
            rval = float(getattr(sdr, attr))
            if rval == val:
                break

    del sdr

    if is_list and isinstance(rval[0], str):
        return val == rval

    if not isinstance(val, str):
        abs_val = np.max(abs(np.array(val) - np.array(rval)))
        if abs_val > tol:
            print(f"Failed to set: {attr}")
            print(f"Set: {str(val)}")
            print(f"Got: {str(rval)}")
        return abs_val <= tol
    else:
        if val != str(rval):
            print(f"Failed to set: {attr}")
            print(f"Set: {val}")
            print(f"Got: {rval}")
        return val == str(rval)


def dev_interface_sub_channel(
    uri, classname, sub_channel, val, attr, tol, readonly=False, sleep=0,
):
    sdr = eval(classname + "(uri='" + uri + "')")
    # Check hardware
    if not hasattr(sdr, sub_channel):
        raise AttributeError(sub_channel + " not defined in " + classname)
    if not hasattr(getattr(sdr, sub_channel), attr):
        raise AttributeError(attr + " not defined in " + classname)

    rval = getattr(getattr(sdr, sub_channel), attr)
    is_list = isinstance(rval, list)
    if is_list:
        l = len(rval)
        val = [val] * l

    if readonly is False:
        setattr(getattr(sdr, sub_channel), attr, val)
        if sleep > 0:
            time.sleep(sleep)
    rval = getattr(getattr(sdr, sub_channel), attr)

    del sdr

    if not isinstance(rval, str) and not is_list:
        rval = float(rval)

    if is_list and isinstance(rval[0], str):
        return val == rval

    if not isinstance(val, str):
        abs_val = np.max(abs(np.array(val) - np.array(rval)))
        if abs_val > tol:
            print(f"Failed to set: {attr}")
            print(f"Set: {str(val)}")
            print(f"Got: {str(rval)}")
        return abs_val <= tol
    return val == str(rval)


def dev_interface_device_name_channel(
    uri,
    classname,
    device_name,
    channel,
    val,
    attr,
    tol,
    sub_channel=None,
    sleep=0.3,
    readonly=False,
):
    """dev_interface_device_name_channel:
    Includes device name and channel in the source to be evaluated
    """

    sdr = eval(
        classname
        + "(uri='"
        + uri
        + "', device_name='"
        + device_name
        + "').channel['"
        + channel
        + "']"
    )
    # Check hardware
    if not hasattr(sdr, attr):
        raise AttributeError(attr + " not defined in " + classname)

    rval = getattr(sdr, attr)
    is_list = isinstance(rval, list)
    if is_list:
        l = len(rval)
        val = [val] * l

    setattr(sdr, attr, val)
    if sleep > 0:
        time.sleep(sleep)
    rval = getattr(sdr, attr)

    if not isinstance(rval, str) and not is_list:
        rval = float(rval)
        for _ in range(5):
            setattr(sdr, attr, val)
            time.sleep(0.3)
            rval = float(getattr(sdr, attr))
            if rval == val:
                break
    else:
        for _ in range(2):
            setattr(sdr, attr, val)
            time.sleep(0.3)
            rval = str(getattr(sdr, attr))
            if rval == val:
                break

    del sdr

    if is_list and isinstance(rval[0], str):
        return val == rval

    if not isinstance(val, str):
        abs_val = np.max(abs(np.array(val) - np.array(rval)))
        if abs_val > tol:
            print(f"Failed to set1: {attr}")
            print(f"Set: {str(val)}")
            print(f"Got: {str(rval)}")
        return abs_val <= tol
    else:
        if val != str(rval):
            print(f"Failed to set: {attr}")
            print(f"Set: {val}")
            print(f"Got: {rval}")
        return val == str(rval)
