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
from adi import ad9144

URI = "ip:analog"


def check_ad9144():
    # Try auto discover
    try:
        iio.Context(URI)
        return True
    except Exception as e:
        print(e)
        return False


class TestAD9144(unittest.TestCase):

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

    @unittest.skipUnless(check_ad9144(), "ad9144 not attached")
    def testAD9144DAC(self):
        # See if we tx data from DAC
        dac = ad9144(uri=URI)
        TXFS = dac.sample_rate
        dac.tx_enabled_channels = [0]
        N = 2 ** 15
        ts = 1 / float(TXFS)
        t = np.arange(0, N * ts, ts)
        fc = 10000
        d = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5
        dac.tx(d)
        self.assertEqual(True, True, "transmit data failed")

    @unittest.skipUnless(check_ad9144(), "ad9144 not attached")
    def testAD9144DAC_p2(self):
        # See if we tx data from DAC
        dac = ad9144(uri=URI)
        TXFS = dac.sample_rate
        dac.tx_enabled_channels = [1]
        N = 2 ** 15
        ts = 1 / float(TXFS)
        t = np.arange(0, N * ts, ts)
        fc = 10000
        d = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5
        dac.tx(d)
        self.assertEqual(True, True, "transmit data failed")

    @unittest.skipUnless(check_ad9144(), "ad9144 not attached")
    def testAD9144DAC_dual(self):
        # See if we tx data from DAC
        dac = ad9144(uri=URI)
        TXFS = dac.sample_rate
        dac.tx_enabled_channels = [0, 1]
        N = 2 ** 15
        ts = 1 / float(TXFS)
        t = np.arange(0, N * ts, ts)
        fc = 10000
        d = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5
        dac.tx([d, d])
        self.assertEqual(True, True, "transmit data failed")


if __name__ == "__main__":
    unittest.main()
