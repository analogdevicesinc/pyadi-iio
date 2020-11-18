import random
from test.common import pytest_collection_modifyitems, pytest_configure
from test.globals import *

import iio

import numpy as np
import pytest
from adi.context_manager import context_manager
from adi.rx_tx import rx


def iio_dev_interface(uri, attrtype, dev_name, chan_name, inout, attr, val, tol):
    try:
        sdr = iio.Context(uri)
    except:
        pytest.skip("Context not reachable: " + str(uri))
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


def iio_attribute_single_value(
    uri, attrtype, dev_name, chan_name, inout, attr, start, stop, step, tol, repeats=1,
):
    """ iio_attribute_single_value: Test numeric attributes over ranges
        This is a generic test that does not use pyadi-iio classes
        but instead uses libiio directly.

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            attrtype: type=string
                Name attribute type to test. Options are: context, channel, debug, device, and channel
            dev_name: type=string
                Name device with associated attribute. Ignored if not device,
                debug, or channel attribute under test
            chan_name: type=string
                Name of channel if channel attribute. Ignored if not channel
                attribute under test
            inout: type=boolean
                True if output channel, False otherwise. Ignored if not channel
                attribute under test
            attr: type=string
                Attribute name to be written. Must be property of classname
            start: type=integer
                Lower bound of possible values attribute can be
            stop: type=integer
                Upper bound of possible values attribute can be
            step: type=integer
                Difference between successive values attribute can be
            tol: type=integer
                Allowable error of written value compared to read back value
            repeats: type=integer
                Number of random values to tests. Generated from uniform distribution
    """
    # Pick random number in operational range
    numints = int((stop - start) / step)
    for _ in range(repeats):
        ind = random.randint(0, numints)
        val = start + step * ind
        # Check hardware
        assert (
            iio_dev_interface(uri, attrtype, dev_name, chan_name, inout, attr, val, tol)
            <= tol
        )


#####################################
## Helper functions for comparing driver states
def get_states(ctx, devices_to_ignore=None, show_skipped=False):
    # Read all attributes in to flattened structure
    state = {}
    for device in ctx.devices:
        if str(device.name) in devices_to_ignore:
            continue
        state[device.name] = {}
        # Get device attributes
        for attr in device.attrs:
            # print(attr)
            try:
                state[device.name][attr] = device.attrs[attr].value
            except OSError:
                if show_skipped:
                    print("Skipped {} {}".format(device.name, attr))
                continue
        # Get channel attributes
        for channel in device.channels:
            # if channel.name:
            #     c_name = str(channel.name) + "_out" if channel.output else "_in"
            # else:
            c_name = "out" if channel.output else "in"
            c_name += "_" + str(channel.id)
            state[device.name][c_name] = {}
            for attr in channel.attrs:
                # print(attr)
                try:
                    # print(c_name)
                    state[device.name][c_name][attr] = channel.attrs[attr].value
                except OSError:
                    if show_skipped:
                        print(
                            "Skipped {} {} {}".format(device.name, channel.name, attr)
                        )
                    continue
    return state


def compare_dictionaries(dict_1, dict_2, dict_1_name, dict_2_name, path=""):
    err = ""
    key_err = ""
    value_err = ""
    old_path = path
    for k in dict_1.keys():
        path = old_path + "[%s]" % k
        if k not in dict_2:
            pass
            # key_err += "Key %s%s\nnot in %s\n" % (dict_2_name, path, dict_2_name)
        else:
            if isinstance(dict_1[k], dict) and isinstance(dict_2[k], dict):
                err += compare_dictionaries(
                    dict_1[k], dict_2[k], dict_1_name, dict_2_name, path
                )
            else:
                if dict_1[k] != dict_2[k]:
                    value_err += "Value of %s%s (%s)\n-------- %s%s (%s)\n" % (
                        dict_1_name,
                        path,
                        dict_1[k],
                        dict_2_name,
                        path,
                        dict_2[k],
                    )

    for k in dict_2.keys():
        path = old_path + "[%s]" % k
        if k not in dict_1:
            key_err += "Key %s%s not in %s\n" % (dict_2_name, path, dict_1_name)

    return key_err + value_err + err


def get_attrs(diff_str):
    lines = diff_str.split("\n")
    odds = lines[::2]
    odds = odds[:-1]
    attr_trees = []
    for line in odds:
        attr_tree = ""
        b1 = line.split("[")
        c = 0
        for b in b1:
            if "]" in b:
                c += 1
                d = b.split("]")[0]
                attr_tree += d + "_"
                if c == 3:
                    break
        attr_trees.append(attr_tree[:-1])

    return attr_trees


def compare_states(state1, state2, expected_to_change, allowed_to_change):
    a = compare_dictionaries(state1, state2, "state1", "state2")
    if a:
        print("\n--Found attribute differences:--")
        print(a)
        delta_attrs = get_attrs(a)
        for attr in delta_attrs:
            if attr not in expected_to_change and attr not in allowed_to_change:
                raise Exception("Unexpected attribute change: " + attr)
        for attr in expected_to_change:
            if attr not in delta_attrs:
                raise Exception("Expected attribute change not found: " + attr)
    else:
        print("\nNo found attribute differences:\n", a)
        if expected_to_change:
            raise Exception("Expected changed attributes did not change")


################################
# Generic Buffer checks
def iio_buffer_check(phy, rxdev, uri, percent_fail):
    """ iio_buffer_check: Check receive buffers for repeative patterns of zeros.
        This function does not require an interfaces class in pyadi but will
        construct a generic interface on the fly.

        parameters:
            phy: type=string
                Name of PHY IIO driver
            rxdev: type=string
                Name of driver with scan elements to create buffers with
            uri: type=string
                URI of IIO context of target board/system
            percent_fail: type=float
                Allowable percentage of zeros at a given index of collected
                buffers
    """

    class rx_generic(rx, context_manager):
        _complex_data = False
        _rx_channel_names = []
        _device_name = ""

        def __init__(self, uri, phy, rxdev):
            context_manager.__init__(self, uri, self._device_name)
            self._rxadc = self._ctx.find_device(rxdev)
            assert self._rxadc, "Device not found: " + rxdev
            # Set channels
            for chan in self._rxadc.channels:
                if chan.scan_element:
                    self._rx_channel_names.append(chan.id)
            rx.__init__(self)

    c = rx_generic(uri, phy, rxdev)
    chans = len(c._rx_channel_names)
    bs = c.rx_buffer_size
    c.rx_enabled_channels = range(chans)

    # Check for zeros
    counts = np.zeros((chans, bs), dtype=int)
    tries = 10
    for _ in range(tries):
        datas = c.rx()
        for chan, data in enumerate(datas):
            for i, sample in enumerate(data):
                counts[chan, i] += counts[chan, i] + sample == 0.0

    for chan, data in enumerate(datas):
        for i, sample in enumerate(data):
            counts[chan, i] = counts[chan, i] / tries
            # print(counts[chan,i])
            if counts[chan, i] > percent_fail:
                raise Exception("Zeros in common pattern found")
