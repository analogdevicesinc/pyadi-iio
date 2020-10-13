import sys
import test.iio_scanner as iio_scanner
from test.globals import *

import iio

import adi
import numpy as np
import pytest


def command_line_config(request):
    if request.config.getoption("--error_on_test_filter"):
        global ignore_skip
        ignore_skip = True

    global target_uri_arg
    target_uri_arg = request.config.getoption("--uri_py")
    if not target_uri_arg:
        target_uri_arg = None

    global imported_config
    filename = request.config.getoption("--test-configfilename")
    imported_config = get_test_config(filename)


def pytest_addoption(parser):
    parser.addoption(
        "--error_on_test_filter",
        action="store_true",
        help="When device is not found generate error not skip",
    )
    parser.addoption(
        "--uri_py",
        action="store",
        help="Run test on device with the given uri. IP scanning will be skipped.",
    )
    parser.addoption(
        "--test-configfilename",
        action="store",
        help="Import custom configuration file not in default location.",
    )


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


class BaseTestHelpers:
    devicename = "pluto"
    skipped_tests = []  # type: ignore
    classname = "adi.ad9361"
    uri = "ip:pluto.local"

    def check_skip(self):
        # Check if calling function is in skip list
        calling_func = sys._getframe(1).f_code.co_name
        global ignore_skip
        if (calling_func in self.skipped_tests) or (not self.check_dev()):
            if not ignore_skip:
                # Will skip test if board not found or calling_func in skipped_tests
                pytest.skip("Skipping")
            else:
                # Will fail if board not found or calling_func in skipped_tests
                pytest.fail("Board not found!")

    def check_dev(self):
        # Must use globals since each test is a separate class instance
        global found_devices
        global found_uris
        global target_uri_arg
        global imported_config
        global ignore_skip
        if not isinstance(self.devicename, list):
            ds = [self.devicename]
        else:
            ds = self.devicename
        dev_checked = False
        found_dev = False
        for d in ds:
            if d in found_devices:
                found_dev = found_devices[d]
                # If device was already found before, update the board interface URI
                self.uri = found_uris[d]
                dev_checked = True
                break

        if not dev_checked:
            if target_uri_arg:
                found_dev, board = iio_scanner.find_device(
                    self.devicename, target_uri_arg, imported_config, ignore_skip
                )
            else:
                found_dev, board = iio_scanner.find_device(
                    self.devicename, None, imported_config, ignore_skip
                )

            if found_dev:
                found_devices[board.name] = found_dev
                found_uris[board.name] = board.uri
                self.uri = board.uri
            else:
                for d in ds:
                    found_devices[d] = False
                    found_uris[d] = ""
        return found_dev

    def dev_interface(self, val, attr, tol):
        sdr = eval(self.classname + "(uri='" + self.uri + "')")
        # Check hardware
        if not hasattr(sdr, attr):
            raise AttributeError(attr + " not defined in " + self.classname)
        setattr(sdr, attr, val)
        rval = getattr(sdr, attr)
        if not isinstance(rval, str):
            rval = float(rval)
        del sdr
        if not isinstance(val, str):
            if abs(val - rval) > tol:
                print("Failed to set: " + attr)
                print("Set: " + str(val))
                print("Got: " + str(rval))
            return abs(val - rval)
        else:
            return val == str(rval)

    def iio_dev_interface(self, attrtype, dev_name, chan_name, inout, attr, val, tol):
        sdr = iio.Context(self.uri)
        attr_tl = attrtype.lower()

        if attr_tl == "context":
            ats = sdr.attrs
            ats[attr].Value = str(val)
            rval = float(sdr.attrs[attr].Value)
        elif attr_tl == "debug":
            raise Exception("Not supported")
        elif attr_tl == "device":
            dev = sdr.find_device(dev_name)
            assert dev, "Device Not Found"
            dev.attrs[attr].Value = str(val)
            rval = float(dev.attrs[attr].Value)
        elif attr_tl == "channel":
            dev = sdr.find_device(dev_name)
            assert dev, "Device Not Found"
            chan = dev.find_channel(chan_name, inout)
            assert chan, "Channel Not Found"
            chan.attrs[attr].Value = str(val)
            rval = float(chan.attrs[attr].Value)
        else:
            raise Exception("Device type unknown " + str(attrtype))

        del sdr
        if not isinstance(val, str):
            if abs(val - rval) > tol:
                print("Failed to set: " + attr)
                print("Set: " + str(val))
                print("Got: " + str(rval))
            return abs(val - rval)
        return val == str(rval)


class BoardInterface(BaseTestHelpers):
    def __init__(self, classname=None, devicename=None):
        self.classname = classname
        self.devicename = devicename
        self.uri = ""
        self.check_skip()
