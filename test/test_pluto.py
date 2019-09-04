# Copyright (C) 2019 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import unittest

import iio

import numpy as np
from adi import Pluto


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


class TestPluto(unittest.TestCase):

    # do_plots = False

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

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skipUnless(check_pluto(), "PlutoSDR not attached")
    def testPlutoADC(self):
        # See if we can get non-zero data from Pluto
        sdr = Pluto()
        data = sdr.rx()
        s = np.sum(np.abs(data))
        self.assertGreater(s, 0, "check non-zero data")

    @unittest.skipUnless(check_pluto(), "PlutoSDR not attached")
    def testPlutoDAC(self):
        # See if we can tone from Pluto using DMAs
        sdr = Pluto()
        sdr.tx_lo = 1000000000
        sdr.rx_lo = 1000000000
        sdr.tx_cyclic_buffer = True
        sdr.tx_hardwaregain = -30
        sdr.gain_control_mode = "slow_attack"
        sdr.rx_buffer_size = 2 ** 20
        # Create a sinewave waveform
        RXFS = int(sdr.sample_rate)
        fc = RXFS * 0.1
        N = 2 ** 15
        ts = 1 / float(RXFS)
        t = np.arange(0, N * ts, ts)
        i = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5
        q = np.sin(2 * np.pi * t * fc) * 2 ** 15 * 0.5
        iq = i + 1j * q
        # Pass through SDR
        sdr.tx(iq)
        for _ in range(5):
            data = sdr.rx()

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
        self.assertGreater(fc * 0.01, diff, "Frequency offset")

    @unittest.skipUnless(check_pluto(), "PlutoSDR not attached")
    def testPlutoDDS(self):
        # See if we can tone from Pluto using DMAs
        sdr = Pluto()
        sdr.tx_lo = 1000000000
        sdr.rx_lo = 1000000000
        sdr.tx_cyclic_buffer = True
        sdr.tx_hardwaregain = -30
        sdr.gain_control_mode = "slow_attack"
        sdr.rx_buffer_size = 2 ** 20
        sdr.sample_rate = 4000000
        sdr.loopback = 1
        # Create a sinewave waveform
        RXFS = int(sdr.sample_rate)
        sdr.dds_enabled = [1, 1, 1, 1]
        fc = 2000
        sdr.dds_frequencies = [fc, 0, fc, 0]
        sdr.dds_scales = [1, 0, 1, 0]
        sdr.dds_phases = [90000, 0, 0, 0]
        # Pass through SDR
        for _ in range(5):
            data = sdr.rx()
        # Turn off loopback (for other tests)
        sdr.loopback = 0
        tone_freq = self.freq_est(data, RXFS)

        # if self.do_plots:
        # import matplotlib.pyplot as plt
        #
        # reals = np.real(data)
        # plt.plot(reals)
        # imags = np.imag(data)
        # plt.plot(imags)
        # plt.xlabel("Samples")
        # plt.ylabel("Amplitude [dbFS]")
        # plt.show()

        diff = np.abs(tone_freq - fc)
        self.assertGreater(fc * 0.01, diff, "Frequency offset")

    @unittest.skipUnless(check_pluto(), "PlutoSDR not attached")
    def testPlutoDMA(self):
        # Test DMA
        sdr = Pluto()
        sdr.loopback = 1
        sdr.tx_cyclic_buffer = True
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
        # Check data
        offset = 0
        for i in range(len(data)):
            if np.real(data[i]) == start:
                for d in range(len(tx_data)):
                    # print(str(data[i+offset])+" "+str(d+start))
                    self.assertEqual(
                        np.real(data[i + offset]),
                        d + start,
                        "Loopback validation failed for I",
                    )
                    self.assertEqual(
                        np.imag(data[i + offset]),
                        (d + start) * -1 - 1,
                        "Loopback validation failed for Q",
                    )
                    offset = offset + 1
                break


if __name__ == "__main__":
    unittest.main()
