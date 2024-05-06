# Copyright (C) 2024 Analog Devices, Inc.
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

#####################################################
################## 8p VNA Rev. D ####################
#####################################################

from adi.ad9083 import ad9083
from adi.ad9173 import ad9173
from adi.adf4371 import adf4371
from adi.adl5960 import adl5960
from adi.admv8818 import admv8818
from adi.adrf5720 import adrf5720
from adi.adrf6780 import adrf6780
from adi.ad5664 import ad5664
from adi.ad4696 import ad4696
from adi.gen_mux import genmux
from adi.one_bit_adc_dac import one_bit_adc_dac

NUM_PORTS = 8

class fmc_8p_vna(adrf5720, ad9083, admv8818, genmux, adf4371,
                 adrf6780, adl5960, ad5664, one_bit_adc_dac):
    """ FMCVNA Scalable 8-port Vector Network Analyzer Board """

    def __init__(self, uri):
        self.hsdac  = ad9173(uri)
        self.lo     = adf4371(uri)
        self.bpf    = admv8818(uri, device_name="admv8818")
        self.ndac   = ad5664(3.3, uri, device_name="ad5664r5")
        self.adcmon = ad4696(uri, device_name="ad4696")
        self.rfin_attenuator    = adrf5720(uri, device_name="adrf5720-rfin")
        self.rfin2_attenuator   = adrf5720(uri, device_name="adrf5720-rfin2")
        self.sig_upconv         = adrf6780(uri, device_name="adrf6780-sig")
        self.lo_upconv          = adrf6780(uri, device_name="adrf6780-lo")

        self.frontend = []
        for i in range(0, NUM_PORTS):
            fe = adl5960(uri, device_name=f"adl5960-{i+1}")
            self.frontend.append(fe)

        ####### MUX ########
        self.rfin_group_mux = genmux(uri, device_name="mux-rfin-group")
        self.rfin1_mux      = genmux(uri, device_name="mux-rfin1")
        self.rfin2_mux      = genmux(uri, device_name="mux-rfin2")
        self.prten_mux      = genmux(uri, device_name="mux-prten")
        self.port_rfin_en   = one_bit_adc_dac(uri, name="port-rfin-en")

        self.dac_sw3_in_mux    = genmux(uri, device_name="mux-rf-dac-sw3-in")
        self.lf_hf_sw_out_mux  = genmux(uri, device_name="mux-lf-hf-sw-out")

        self.siglo_mux      = genmux(uri, device_name="mux-adf4371-siglo")
        self.dbrlo_mux      = genmux(uri, device_name="mux-adf4371-dbrlo")

        self.freq_src_sel_mux = genmux(uri, device_name="mux-freq-src-sel")
        self.lo_rfin_p1       = genmux(uri, device_name="mux-lo-rfin-p1")
        self.lo_rfin_p2       = genmux(uri, device_name="mux-lo-rfin-p2")

        self.hsdac0_mux = genmux(uri, device_name="mux-dac0-rfout")
        self.hsdac1_mux = genmux(uri, device_name="mux-dac1-rfout")
        #######################

        ad9083.__init__(self, uri)
        one_bit_adc_dac.__init__(self, uri, name="misc-gpio-ctrl")

        self._rxadc.set_kernel_buffers_count(1)

    @property
    def active_port(self) -> str:
        # assume the enabled LED designates the active port
        return self.prten_mux.select

    @active_port.setter
    def active_port(self, port: str) -> None:
        # Parse out port number
        port_num = int(port[1])

        group      = "d1-d4"
        config_mux = self.rfin2_mux
        if port_num >= 5 and port_num <= 8:
            group = "d5-d8"
            config_mux = self.rfin1_mux

        self.rfin_group_mux.select = group
        self.prten_mux.select      = port
        config_mux.select          = port

        # turn of rfin to all ports except the desired port
        for i in range(0, 8):
            enabled = 0
            cur_port = f"d{i+1}"
            if port == cur_port:
                enabled = 1

            setattr(self.port_rfin_en, f"gpio_{cur_port}", enabled)

