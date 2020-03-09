import random
import sys
import test.iio_scanner as iio_scanner
import test.rf.spec as spec
import time

import iio

import adi
import numpy as np
import pytest

ignore_skip = False
dev_checked = False
found_dev = False
found_devices = {}  # type: ignore
found_uris = {}  # type: ignore
URI = "ip:analog"


def pytest_addoption(parser):
    parser.addoption(
        "--error_on_filter",
        action="store_true",
        help="When device is not found generate error not skip",
    )


class BaseTestHelpers:
    devicename = "pluto"
    skipped_tests = []  # type: ignore
    classname = "adi.ad9361"
    uri = "ip:pluto.local"

    def check_skip(self):
        # Check if calling function is in skip list
        calling_func = sys._getframe(1).f_code.co_name
        global ignore_skip
        if not ignore_skip:
            if (calling_func in self.skipped_tests) or (not self.check_dev()):
                # pytest.xfail()
                pytest.skip("Skipping")

    def check_dev(self):
        # Must use globals since each test is a separate class instance
        global found_devices
        global found_uris
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
            found_dev, board = iio_scanner.find_device(self.devicename)
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
        setattr(sdr, attr, val)
        rval = float(getattr(sdr, attr))
        del sdr
        if not isinstance(val, str):
            if abs(val - rval) > tol:
                print("Failed to set: " + attr)
                print("Set: " + str(val))
                print("Got: " + str(rval))
            return abs(val - rval)
        else:
            return val == str(rval)


class BoardInterface(BaseTestHelpers):
    def __init__(self, classname, devicename):
        self.classname = classname
        self.devicename = devicename
        self.uri = ""
        self.check_skip()


def attribute_single_value(classname, devicename, attr, start, stop, step, tol):
    bi = BoardInterface(classname, devicename)
    # Pick random number in operational range
    numints = int((stop - start) / step)
    ind = random.randint(0, numints + 1)
    val = start + step * ind
    # Check hardware
    assert bi.dev_interface(val, attr, tol) <= tol


def attribute_single_value_str(classname, devicename, attr, val, tol):
    bi = BoardInterface(classname, devicename)
    # Check hardware
    assert bi.dev_interface(str(val), attr, tol) <= tol


def attribute_single_value_pow2(classname, devicename, attr, max_pow, tol):
    bi = BoardInterface(classname, devicename)
    # Pick random number in operational range
    nums = []
    for k in range(0, max_pow):
        nums.append(2 ** k)
    ind = random.randint(0, len(nums) - 1)
    val = nums[ind]
    # Check hardware
    assert bi.dev_interface(val, attr, tol) <= tol


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
    else:
        RXFS = int(sdr.rx_sample_rate)
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


def command_line_config(request):
    if request.config.getoption("--error_on_filter"):
        global ignore_skip
        ignore_skip = True


#########################################
# Fixtures
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
