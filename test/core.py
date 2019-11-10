import random

import iio

import numpy as np
import pytest
import adi
import test.iio_scanner as iio_scanner

dev_checked = False
found_dev = False
URI = "ip:analog"


def pytest_generate_tests(metafunc):
    # called once per each test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = list(funcarglist[0])
    metafunc.parametrize(
        argnames, [[funcargs[name] for name in argnames] for funcargs in funcarglist]
    )


class CoreTests:
    # Example parameters
    params = {
        "test_attribute_single_value": [
            dict(
                devname="adXXXX",
                attr="tx_hardwaregain",
                start=-89.75,
                stop=0.0,
                step=0.25,
                tol=0,
            ),
            dict(
                devname="adXXXX",
                attr="rx_lo",
                start=70000000,
                stop=6000000000,
                step=1,
                tol=8,
            ),
        ],
        "test_attribute_single_value_str": [
            dict(devname="adXXXX", attr="loopback", val=2, tol=0),
            dict(devname="adXXXX", attr="loopback", val=1, tol=0),
            dict(devname="adXXXX", attr="loopback", val=0, tol=0),
        ],
    }
    devicename = "pluto"

    def check_dev(self):
        # Must use globals since each test is a separate class instance
        global dev_checked
        global found_dev
        if not dev_checked:
            found_dev, board = iio_scanner.find_device(self.devicename)
            if found_dev:
                global URI
                URI = board.uri
            dev_checked = True
        return found_dev

    def test_attribute_single_value(self, devname, attr, start, stop, step, tol):
        if not self.check_dev():
            pytest.skip("Skipping")
        global URI
        sdr = eval(devname + "(uri='" + URI + "')")
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

    def test_attribute_single_value_str(self, devname, attr, val, tol):
        if not self.check_dev():
            pytest.skip("Skipping")
        global URI
        sdr = eval(devname + "(uri='" + URI + "')")
        # Check hardware
        setattr(sdr, attr, val)
        rval = float(getattr(sdr, attr))
        del sdr
        if abs(val - rval) > tol:
            print("Failed to set: " + attr)
            print("Set: " + str(val))
            print("Got: " + str(rval))
        assert abs(val - rval) <= tol

    def test_dma(self, devname, channel):
        if not self.check_dev():
            pytest.skip("Skipping")
        global URI
        sdr = eval(devname + "(uri='" + URI + "')")
        sdr.loopback = 1
        sdr.tx_cyclic_buffer = True
        if sdr._num_tx_channels > 2:
            sdr.tx_enabled_channels = [channel]
        if sdr._num_rx_channels > 2:
            sdr.rx_enabled_channels = [channel]

        # Create a ramp signal with different values for I and Q
        start = 0
        tx_data = np.array(range(start, 2 ** 11), dtype=np.int16)
        tx_data = tx_data << 4
        tx_data = tx_data + 1j * (tx_data * -1 - 1)
        sdr.rx_buffer_size = len(tx_data) * 2

        sdr.tx(tx_data)
        # Flush buffers
        for _ in range(100):
            data = sdr.rx()
        # Turn off loopback (for other tests)
        sdr.loopback = 0
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


class DSPTests:
    devicename = "pluto"  # Need to specify

    def freq_est(self, y, fs):
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

    def check_dev(self):
        # Must use globals since each test is a separate class instance
        global dev_checked
        global found_dev
        if not dev_checked:
            found_dev, board = iio_scanner.find_device(self.devicename)
            if found_dev:
                global URI
                URI = board.uri
            dev_checked = True
        return found_dev

    def test_iq_loopback(self, devname, channel, param_set):
        # See if we can tone using DMAs
        if not self.check_dev():
            pytest.skip("Skipping")
        global URI
        sdr = eval(devname + "(uri='" + URI + "')")
        # Set custom device parameters
        for p in param_set.keys():
            setattr(sdr, p, param_set[p])
        # Set common buffer settings
        sdr.tx_cyclic_buffer = True
        sdr.rx_buffer_size = 2 ** 15
        if sdr._num_tx_channels > 2:
            sdr.tx_enabled_channels = [channel]
        if sdr._num_rx_channels > 2:
            sdr.rx_enabled_channels = [channel]
        # Create a sinewave waveform
        RXFS = int(sdr.sample_rate)
        fc = RXFS * 0.1
        N = 2 ** 14
        ts = 1 / float(RXFS)
        t = np.arange(0, N * ts, ts)
        i = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5
        q = np.sin(2 * np.pi * t * fc) * 2 ** 15 * 0.5
        iq = i + 1j * q
        # Pass through SDR
        sdr.tx(iq)
        for _ in range(30):  # Wait for IQ correction to stabilize
            data = sdr.rx()

        del sdr
        tone_freq = self.freq_est(data, RXFS)

        # if self.do_plots:
        #     import matplotlib.pyplot as plt
        #
        #     reals = np.real(data)
        #     plt.plot(reals)
        #     imags = np.imag(data)
        #     plt.plot(imags)
        #     plt.xlabel("Samples")
        #     plt.ylabel("Amplitude [dbFS]")
        #     plt.show()

        diff = np.abs(tone_freq - fc)
        assert (fc * 0.01) > diff
        # self.assertGreater(fc * 0.01, diff, "Frequency offset")
