import datetime
import os
import random
import sys
import test.iio_scanner as iio_scanner
import test.rf.spec as spec
import time

import iio

import adi
import numpy as np
import pytest
import yaml
from elasticsearch import Elasticsearch

target_uri_arg = None
ignore_skip = False
dev_checked = False
found_dev = False
found_devices = {}  # type: ignore
found_uris = {}  # type: ignore
URI = "ip:analog"
TESTCONFIG_DEFAULT_PATH = "/etc/default/pyadi_test.yaml"


def get_test_config(filename=None):
    if not filename:
        if os.name == "nt" or os.name == "posix":
            if os.path.exists(TESTCONFIG_DEFAULT_PATH):
                filename = TESTCONFIG_DEFAULT_PATH
    if not filename:
        return None

    stream = open(filename, "r")
    config = yaml.safe_load(stream)
    stream.close()
    return config


# Get default config if it exists
imported_config = get_test_config()


def pytest_addoption(parser):
    parser.addoption(
        "--error_on_filter",
        action="store_true",
        help="When device is not found generate error not skip",
    )
    parser.addoption(
        "--uri",
        action="store",
        help="Run test on device with the given uri. IP scanning will be skipped.",
    )
    parser.addoption(
        "--test-configfilename",
        action="store",
        help="Import custom configuration file not in default location.",
    )
    parser.addoption(
        "--elastic-log",
        action="store_true",
        help="Enable submission of telemetry to elasticsearch",
    )


def submit_elastic_tx_quad_cal(devname, failed, iterations, channel, date):
    global imported_config
    print(imported_config)
    if "elastic" not in imported_config:
        print("No elasticsearch configuration found")
        return
    s = imported_config["elastic"]
    es = Elasticsearch(
        [{"host": s["server"], "port": s["port"]}],
        http_auth=(s["username"], s["password"]),
    )
    if not es.ping():
        print("elasticsearch server not found")
        return
    index = "ad936x_tx_quad_cal"
    if not es.indices.exists(index):
        record = {
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "test_name": {"type": "text"},
                    "date": {"type": "date"},
                    "device": {"type": "text"},
                    "failed": {"type": "integer"},
                    "iterations": {"type": "integer"},
                    "channel": {"type": "integer"},
                }
            },
        }
        es.indices.create(index=index, body=record)

    record = {
        "test_name": "ad936x_tx_quad_cal",
        "date": date,
        "device": devname,
        "failed": failed,
        "iterations": iterations,
        "channel": channel,
    }
    print(record)
    es.index(index=index, body=record)


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
        self.board = "NA"
        board = "NA"
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

        if not board == "NA":
            self.board = board.name
        else:
            self.board = board
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


def iio_attribute_single_value(
    devicename,
    attrtype,
    dev_name,
    chan_name,
    inout,
    attr,
    start,
    stop,
    step,
    tol,
    repeats=1,
):
    bi = BoardInterface(None, devicename)
    # Pick random number in operational range
    numints = int((stop - start) / step)
    for _ in range(repeats):
        ind = random.randint(0, numints)
        val = start + step * ind
        # Check hardware
        assert (
            bi.iio_dev_interface(attrtype, dev_name, chan_name, inout, attr, val, tol)
            <= tol
        )


def attribute_single_value(
    classname, devicename, attr, start, stop, step, tol, repeats=1
):
    bi = BoardInterface(classname, devicename)
    # Pick random number in operational range
    numints = int((stop - start) / step)
    for _ in range(repeats):
        ind = random.randint(0, numints)
        val = start + step * ind
        # Check hardware
        assert bi.dev_interface(val, attr, tol) <= tol


def attribute_single_value_str(classname, devicename, attr, val, tol):
    bi = BoardInterface(classname, devicename)
    # Check hardware
    assert bi.dev_interface(str(val), attr, tol) <= tol


def attribute_single_value_pow2(classname, devicename, attr, max_pow, tol, repeats=1):
    bi = BoardInterface(classname, devicename)
    # Pick random number in operational range
    nums = []
    for k in range(0, max_pow):
        nums.append(2 ** k)
    for _ in range(repeats):
        ind = random.randint(0, len(nums) - 1)
        val = nums[ind]
        # Check hardware
        assert bi.dev_interface(val, attr, tol) <= tol


def attribute_multipe_values(classname, devicename, attr, values, tol, repeats=1):
    bi = BoardInterface(classname, devicename)
    for _ in range(repeats):
        for val in values:
            if isinstance(val, str):
                assert bi.dev_interface(val, attr, 0)
            else:
                assert bi.dev_interface(val, attr, tol) <= tol


def attribute_multipe_values_with_depends(
    classname, devicename, attr, depends, values, tol, repeats=1
):
    bi = BoardInterface(classname, devicename)
    # Set custom dependencies for the attr being tested
    for p in depends.keys():
        if isinstance(depends[p], str):
            assert bi.dev_interface(depends[p], p, 0)
        else:
            assert bi.dev_interface(depends[p], p, tol) <= tol
    for _ in range(repeats):
        for val in values:
            if isinstance(val, str):
                assert bi.dev_interface(val, attr, 0)
            else:
                assert bi.dev_interface(val, attr, tol) <= tol


def attribute_write_only_str(classname, devicename, attr, file):
    bi = BoardInterface(classname, devicename)
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    try:
        setattr(sdr, attr, file)
        del sdr
    except Exception as e:
        del sdr
        raise Exception(e)


def dma_rx(classname, devicename, channel):
    bi = BoardInterface(classname, devicename)
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    N = 2 ** 15
    if not isinstance(channel, list):
        sdr.rx_enabled_channels = [channel]
    else:
        sdr.rx_enabled_channels = channel
    sdr.rx_buffer_size = N * len(sdr.rx_enabled_channels)
    try:
        for _ in range(10):
            data = sdr.rx()
            if isinstance(data, list):
                for chan in data:
                    assert np.sum(np.abs(chan)) > 0
            else:
                assert np.sum(np.abs(data)) > 0
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def dma_tx(classname, devicename, channel):
    bi = BoardInterface(classname, devicename)
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    TXFS = 1000
    N = 2 ** 15
    ts = 1 / float(TXFS)
    t = np.arange(0, N * ts, ts)
    fc = 10000
    d = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5

    if not isinstance(channel, list):
        sdr.tx_enabled_channels = [channel]
    else:
        sdr.tx_enabled_channels = channel
        d = [d] * len(channel)
    sdr.tx_buffer_size = N * len(sdr.tx_enabled_channels)

    try:
        for _ in range(10):
            sdr.tx(d)
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def dma_loopback(classname, devicename, channel):
    bi = BoardInterface(classname, devicename)
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    if classname == "adi.FMComms5" and (channel in [2, 3]):
        sdr.loopback_chip_b = 1
    else:
        sdr.loopback = 1
    sdr.tx_cyclic_buffer = True
    # Create a ramp signal with different values for I and Q
    start = 0
    tx_data = np.array(range(start, 2 ** 11), dtype=np.int16)
    tx_data = tx_data << 4
    tx_data = tx_data + 1j * (tx_data * -1 - 1)
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = len(tx_data) * 2 * len(sdr.tx_enabled_channels)
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = len(tx_data) * 2 * len(sdr.rx_enabled_channels)
    try:
        sdr.tx(tx_data)
        # Flush buffers
        for _ in range(100):
            data = sdr.rx()
        # Turn off loopback (for other tests)
        if classname == "adi.FMComms5" and (channel in [2, 3]):
            sdr.loopback_chip_b = 0
        else:
            sdr.loopback = 0
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    # Check data
    offset = 0
    for i in range(len(data)):
        if np.real(data[i]) == start:
            for d in range(len(tx_data)):
                # print(str(data[i+offset])+" "+str(d+start))
                assert np.real(data[i + offset]) == (d + start)
                assert np.imag(data[i + offset]) == ((d + start) * -1 - 1)
                offset = offset + 1
            break


def freq_est(y, fs):
    N = len(y)
    T = 1.0 / fs
    yf = np.fft.fft(y)
    yf = np.fft.fftshift(yf)
    xf = np.linspace(-1.0 / (2.0 * T), 1.0 / (2.0 * T), N)
    # if self.do_plots:
    #     import matplotlib.pyplot as plt
    #
    #     fig, ax = plt.subplots()
    #     ax.plot(xf, 2.0 / N * np.abs(yf))
    #     plt.show()
    indx = np.argmax(np.abs(yf))
    return xf[indx]


def dds_loopback(classname, devicename, param_set, channel, frequency, scale, peak_min):
    bi = BoardInterface(classname, devicename)
    # See if we can tone using DMAs
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    # Set common buffer settings
    sdr.tx_cyclic_buffer = True
    N = 2 ** 14
    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    else:
        RXFS = int(sdr.rx_sample_rate)

    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)
    sdr.dds_single_tone(frequency, scale, channel)

    # Pass through SDR
    try:
        for _ in range(10):  # Wait
            data = sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=2 ** 15)
    indx = np.argmax(tone_peaks)
    diff = np.abs(tone_freqs[indx] - frequency)
    print("Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx]))
    assert (frequency * 0.01) > diff
    assert tone_peaks[indx] > peak_min


def cw_loopback(classname, devicename, channel, param_set):
    bi = BoardInterface(classname, devicename)
    # See if we can tone using DMAs
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    time.sleep(1)
    # Verify still set
    for p in param_set.keys():
        if isinstance(param_set[p], str):
            assert getattr(sdr, p) == param_set[p]
        else:
            assert np.abs(getattr(sdr, p) - param_set[p]) < 4
    # Set common buffer settings
    sdr.tx_cyclic_buffer = True
    N = 2 ** 14
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)
    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    elif hasattr(sdr, "rx_sample_rate"):
        RXFS = int(sdr.rx_sample_rate)
    else:
        """ no sample_rate nor rx_sample_rate. Let's try something like
        rx($channel)_sample_rate"""
        attr = "rx" + str(channel) + "_sample_rate"
        RXFS = int(getattr(sdr, attr))

    A = 2 ** 15
    fc = RXFS * 0.1
    ts = 1 / float(RXFS)
    t = np.arange(0, N * ts, ts)
    if sdr._complex_data:
        i = np.cos(2 * np.pi * t * fc) * A * 0.5
        q = np.sin(2 * np.pi * t * fc) * A * 0.5
        cw = i + 1j * q
    else:
        cw = np.cos(2 * np.pi * t * fc) * A * 1

    # Pass through SDR
    try:
        sdr.tx(cw)
        for _ in range(30):  # Wait to stabilize
            data = sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    # tone_freq = freq_est(data, RXFS)
    # diff = np.abs(tone_freq - fc)
    # print("Peak: @"+str(tone_freq) )
    # assert (fc * 0.01) > diff

    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=A)
    indx = np.argmax(tone_peaks)
    diff = np.abs(tone_freqs[indx] - fc)
    print("Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx]))
    assert (fc * 0.01) > diff
    # self.assertGreater(fc * 0.01, diff, "Frequency offset")


def t_sfdr(classname, devicename, channel, param_set, sfdr_min):
    bi = BoardInterface(classname, devicename)
    # See if we can tone using DMAs
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    time.sleep(5)  # Wait for QEC to kick in
    # Set common buffer settings
    N = 2 ** 14
    sdr.tx_cyclic_buffer = True
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)
    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    else:
        RXFS = int(sdr.rx_sample_rate)
    fc = RXFS * 0.1

    ts = 1 / float(RXFS)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.9
    q = np.sin(2 * np.pi * t * fc) * 2 ** 15 * 0.9
    iq = i + 1j * q
    # Pass through SDR
    try:
        sdr.tx(iq)
        time.sleep(3)
        for _ in range(10):  # Wait for IQ correction to stabilize
            data = sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    val = spec.sfdr(data, plot=False)
    assert val > sfdr_min


def gain_check(
    classname, devicename, channel, param_set, dds_scale, min_rssi, max_rssi
):
    bi = BoardInterface(classname, devicename)
    # See if we can tone using DMAs
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    # Enable DDSs
    if hasattr(sdr, "sample_rate"):
        fs = int(sdr.sample_rate)
    else:
        fs = int(sdr.rx_sample_rate)
    sdr.dds_single_tone(np.floor(fs * 0.1), dds_scale, channel)
    time.sleep(3)

    # Check RSSI
    rssi1 = sdr._get_iio_attr("voltage0", "rssi", False, sdr._ctrl)
    rssi2 = sdr._get_iio_attr("voltage1", "rssi", False, sdr._ctrl)
    rssi3 = sdr._get_iio_attr("voltage0", "rssi", False, sdr._ctrl_b)
    rssi4 = sdr._get_iio_attr("voltage1", "rssi", False, sdr._ctrl_b)

    if channel == 0:
        rssi = rssi1
    if channel == 1:
        rssi = rssi2
    if channel == 2:
        rssi = rssi3
    if channel == 3:
        rssi = rssi4
    print(rssi1, rssi2, rssi3, rssi4)
    assert rssi >= min_rssi
    assert rssi <= max_rssi


def cyclic_buffer(classname, devicename, channel, param_set):
    bi = BoardInterface(classname, devicename)
    # See if we can tone using DMAs
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    fs = int(sdr.sample_rate)
    fc = -3000000
    N = 1024
    ts = 1 / float(fs)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q = np.sin(2 * np.pi * t * fc) * 2 ** 14
    iq = i + 1j * q
    sdr.tx_cyclic_buffer = True
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)
    sdr.tx(iq)
    sdr.tx_destroy_buffer()
    fail = False
    try:
        sdr.tx(iq)
    except Exception as e:
        fail = True
        msg = (
            "Pushing new data after destroying buffer should not fail. "
            "message: " + str(e)
        )

    # Cleanly end
    del sdr
    if fail:
        pytest.fail(msg)


def cyclic_buffer_exception(classname, devicename, channel, param_set):
    bi = BoardInterface(classname, devicename)
    # See if we can tone using DMAs
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    fs = int(sdr.sample_rate)
    fc = -3000000
    N = 1024
    ts = 1 / float(fs)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q = np.sin(2 * np.pi * t * fc) * 2 ** 14
    iq = i + 1j * q
    sdr.tx_cyclic_buffer = True
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)
    try:
        sdr.tx(iq)
        sdr.tx(iq)
    except Exception as e:
        if (
            "TX buffer has been submitted in cyclic mode. "
            "To push more data the tx buffer must be destroyed first." not in str(e)
        ):
            fail = True
            msg = "Wrong exception raised, message was: " + str(e)
        else:
            fail = False
    else:
        fail = True
        msg = "ExpectedException not raised"
    # Cleanly end
    del sdr
    if fail:
        pytest.fail(msg)


#########################################


def stress_context_creation(classname, devicename, channel, repeats):
    """ Repeatedly create and destroy a context """
    for _ in range(repeats):
        bi = BoardInterface(classname, devicename)
        sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
        N = 2 ** 15
        if not isinstance(channel, list):
            sdr.rx_enabled_channels = [channel]
        else:
            sdr.rx_enabled_channels = channel
        sdr.rx_buffer_size = N * len(sdr.rx_enabled_channels)
        try:
            for _ in range(repeats):
                data = sdr.rx()
                if isinstance(data, list):
                    for chan in data:
                        assert np.sum(np.abs(chan)) > 0
                else:
                    assert np.sum(np.abs(data)) > 0
                sdr.rx_destroy_buffer()
        except Exception as e:
            del sdr
            raise Exception(e)

        del sdr


def stress_rx_buffer_length(classname, devicename, channel, buffer_sizes):
    """ Repeatedly create and destroy buffers across different buffer sizes"""
    bi = BoardInterface(classname, devicename)
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    if not isinstance(channel, list):
        sdr.rx_enabled_channels = [channel]
    else:
        sdr.rx_enabled_channels = channel
    try:
        for size in buffer_sizes:
            sdr.rx_buffer_size = size
            data = sdr.rx()
            if isinstance(data, list):
                for chan in data:
                    assert len(chan) == size
                    assert np.sum(np.abs(chan)) > 0
            else:
                assert len(data) == size
                assert np.sum(np.abs(data)) > 0
            sdr.rx_destroy_buffer()
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def stress_rx_buffer_creation(classname, devicename, channel, repeats):
    """ Repeatedly create and destroy buffers """
    bi = BoardInterface(classname, devicename)
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    N = 2 ** 15
    if not isinstance(channel, list):
        sdr.rx_enabled_channels = [channel]
    else:
        sdr.rx_enabled_channels = channel
    sdr.rx_buffer_size = N * len(sdr.rx_enabled_channels)
    try:
        for _ in range(repeats):
            data = sdr.rx()
            if isinstance(data, list):
                for chan in data:
                    assert np.sum(np.abs(chan)) > 0
            else:
                assert np.sum(np.abs(data)) > 0
            sdr.rx_destroy_buffer()
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def stress_tx_buffer_creation(classname, devicename, channel, repeats):
    bi = BoardInterface(classname, devicename)
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")
    TXFS = 1000
    N = 2 ** 15
    ts = 1 / float(TXFS)
    t = np.arange(0, N * ts, ts)
    fc = 10000
    d = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5

    if not isinstance(channel, list):
        sdr.tx_enabled_channels = [channel]
    else:
        sdr.tx_enabled_channels = channel
        d = [d] * len(channel)
    sdr.tx_buffer_size = N * len(sdr.tx_enabled_channels)

    try:
        for _ in range(repeats):
            sdr.tx(d)
            sdr.tx_destroy_buffer()
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def catalina_tx_iq_cal_validate(classname, devicename, repeats):
    bi = BoardInterface(classname, devicename)
    sdr = eval(bi.classname + "(uri='" + bi.uri + "')")

    # Check Quad Cal
    TX1_not_converged = 0
    TX2_not_converged = 0
    for n in range(repeats):
        sdr._ctrl.debug_attrs["initialize"].value = "1"
        time.sleep(1)
        TX1_not_converged += bin(sdr._ctrl.reg_read(0x0A7))[-1] != "1"
        TX2_not_converged += bin(sdr._ctrl.reg_read(0x0A8))[-1] != "1"
        print(TX1_not_converged, TX2_not_converged, n)

    date = datetime.datetime.now()
    submit_elastic_tx_quad_cal(bi.board, TX1_not_converged, repeats, 0, date)
    submit_elastic_tx_quad_cal(bi.board, TX2_not_converged, repeats, 1, date)

    percent_fail = float(TX1_not_converged) / float(repeats)
    assert percent_fail < 0.10
    percent_fail = float(TX2_not_converged) / float(repeats)
    assert percent_fail < 0.10


#########################################


def command_line_config(request):
    if request.config.getoption("--error_on_filter"):
        global ignore_skip
        ignore_skip = True

    global target_uri_arg
    target_uri_arg = request.config.getoption("--uri")
    if not target_uri_arg:
        target_uri_arg = None

    global imported_config
    filename = request.config.getoption("--test-configfilename")
    imported_config = get_test_config(filename)


#########################################
# Fixtures
@pytest.fixture()
def test_iio_attribute_single_value(request):
    command_line_config(request)
    yield iio_attribute_single_value


@pytest.fixture()
def test_stress_context_creation(request):
    command_line_config(request)
    yield stress_context_creation


@pytest.fixture()
def test_stress_rx_buffer_length(request):
    command_line_config(request)
    yield stress_rx_buffer_length


@pytest.fixture()
def test_stress_rx_buffer_creation(request):
    command_line_config(request)
    yield stress_rx_buffer_creation


@pytest.fixture()
def test_stress_tx_buffer_creation(request):
    command_line_config(request)
    yield stress_tx_buffer_creation


@pytest.fixture()
def test_attribute_single_value(request):
    command_line_config(request)
    yield attribute_single_value


@pytest.fixture()
def test_attribute_single_value_str(request):
    command_line_config(request)
    yield attribute_single_value_str


@pytest.fixture()
def test_attribute_single_value_pow2(request):
    command_line_config(request)
    yield attribute_single_value_pow2


@pytest.fixture()
def test_dma_rx(request):
    command_line_config(request)
    yield dma_rx


@pytest.fixture()
def test_dma_tx(request):
    command_line_config(request)
    yield dma_tx


@pytest.fixture()
def test_cyclic_buffer(request):
    command_line_config(request)
    yield cyclic_buffer


@pytest.fixture()
def test_cyclic_buffer_exception(request):
    command_line_config(request)
    yield cyclic_buffer_exception


@pytest.fixture()
def test_dma_loopback(request):
    command_line_config(request)
    yield dma_loopback


@pytest.fixture()
def test_sfdr(request):
    command_line_config(request)
    yield t_sfdr


@pytest.fixture()
def test_dds_loopback(request):
    command_line_config(request)
    yield dds_loopback


@pytest.fixture()
def test_iq_loopback(request):
    command_line_config(request)
    yield cw_loopback


@pytest.fixture()
def test_cw_loopback(request):
    command_line_config(request)
    yield cw_loopback


@pytest.fixture()
def test_gain_check(request):
    command_line_config(request)
    yield gain_check


@pytest.fixture()
def test_attribute_multipe_values(request):
    command_line_config(request)
    yield attribute_multipe_values


@pytest.fixture()
def test_attribute_multipe_values_with_depends(request):
    command_line_config(request)
    yield attribute_multipe_values_with_depends


@pytest.fixture
def test_attribute_write_only_str(request):
    command_line_config(request)
    yield attribute_write_only_str


@pytest.fixture
def test_catalina_tx_iq_cal_validate(request):
    command_line_config(request)
    yield catalina_tx_iq_cal_validate
