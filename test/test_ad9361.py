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
from adi import ad9361

URI = "ip:analog"


def check_ad9361():
    # Try auto discover
    try:
        iio.Context(URI)
        return True
    except Exception as e:
        print(e)
        return False


class TestAD9361(unittest.TestCase):

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

    @unittest.skipUnless(check_ad9361(), "AD9361SDR not attached")
    def testAD9361ADC(self):
        # See if we can get non-zero data from AD9361
        sdr = ad9361(uri=URI)
        data = sdr.rx()
        s = np.sum(np.abs(data))
        self.assertGreater(s, 0, "check non-zero data")

    @unittest.skipUnless(check_ad9361(), "AD9361SDR not attached")
    def testAD9361DAC(self):
        # See if we can tone from AD9361 using DMAs
        sdr = ad9361(uri=URI)
        sdr.tx_lo = 1000000000
        sdr.rx_lo = 1000000000
        sdr.tx_cyclic_buffer = True
        sdr.tx_hardwaregain = -30
        sdr.gain_control_mode = "slow_attack"
        sdr.rx_buffer_size = 2 ** 20
        sdr.sample_rate = 4000000
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
        sdr.tx([iq, iq * 0.0])
        for _ in range(30):  # Wait for IQ correction to stabilize
            data = sdr.rx()

        tone_freq = self.freq_est(data[0], RXFS)

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


if __name__ == "__main__":
    unittest.main()
