# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.ad9083 import ad9083
from adi.adf5610 import adf5610
from adi.adl5960 import adl5960
from adi.admv8818 import admv8818
from adi.adrf5720 import adrf5720
from adi.gen_mux import genmux
from adi.one_bit_adc_dac import one_bit_adc_dac


class fmcvna(adrf5720, ad9083, admv8818, genmux, adf5610, adl5960):
    """ FMCVNA Scalable 8-port Vector Network Analyzer Board """

    frontend = [0] * 8

    def __init__(self, uri):
        self.lo = adf5610(uri, device_name="adf5610")
        self.rfin_attenuator = adrf5720(uri, device_name="adrf5720-rfin")
        self.lo_attenuator = adrf5720(uri, device_name="adrf5720-lo")
        self.rfin_bpf = admv8818(uri, device_name="admv8818-rfin")
        self.lo_bpf = admv8818(uri, device_name="admv8818-lo")
        self.rfin_mux = genmux(uri, device_name="mux-rfin")
        self.lo_mux = genmux(uri, device_name="mux-doubler")

        for i in range(1, 9):
            self.frontend[i - 1] = adl5960(uri, device_name=f"adl5960-{i}")

        ad9083.__init__(self, uri)
        one_bit_adc_dac.__init__(self, uri)

        self._rxadc.set_kernel_buffers_count(1)
