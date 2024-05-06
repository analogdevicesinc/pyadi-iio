# Copyright (C) 2023 Analog Devices, Inc.
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

import time

import adi
import matplotlib.pyplot as plt


vna = adi.fmc_8p_vna("ip:192.168.0.44")

print("--Setting up chip")

# Capture all 16 channels
vna.rx_enabled_channels = [0, 1, 2, 3, 4, 5, 6, 7,
                           8, 9, 10, 11, 12, 13, 14, 15]
vna.rx_buffer_size = 2 ** 12
fs = int(vna.rx_sample_rate)

vna.active_port  = "d2"
vna.lo.frequency = 3e9
vna.lo.rfaux8_vco_output_enable = False

vna.hsdac0_mux.select = "rf_dac0_direct"
vna.hsdac1_mux.select = "rf_lo_direct"
vna.freq_src_sel_mux.select = "rf_dac0_direct"

vna.hsdac.modulation_switch_mode = 0

vna.hsdac.channel0_nco_frequency = 1000
vna.hsdac.channel1_nco_frequency = 1000

vna.hsdac.main0_nco_frequency   = 1000000000
vna.hsdac.main1_nco_frequency   = 1000000000

# push shifted DC out of spectrum
if_frequency = fs
vna.nco0_frequency = if_frequency

# Rev. D: Switch freq source (example)
vna.dac_sw3_in_mux      = "rf-dac02-out"    # rf-dac02-out/rf-dac0-out
vna.lf_hf_sw_out_mux    = "rf-amp-out"      # rf-dac02-out/rf-amp-out

for i in range(0, 8):
    vna.frontend[i].lo_mode = "x1"
    vna.frontend[i].offset_mode = "off"
    vna.frontend[i].if_frequency = if_frequency
    vna.frontend[i].forward_gain = 6
    vna.frontend[i].reflected_gain = 6
    vna.frontend[i].if_filter_cutoff = vna.frontend[i].if_frequency
    print("ADL5960-", i, "Temperature", vna.frontend[i].temperature, "°C")
    print("ADL5960-", i, "REG 0x25 =", vna.frontend[i].reg_read(0x25))

vna.bpf.mode = "bypass"

vna.gpio_adl5960x_sync = 1
vna.gpio_adl5960x_sync = 0

print("AD9083    NCO0", vna.nco0_frequency, "Hz")
print("ADL5960-1 IF frequency", vna.frontend[0].if_frequency, "Hz")
print("ADL5960-1 OFFSET frequency", vna.frontend[0].offset_frequency, "Hz")
print("ADL5960-1 OFFSET mode", vna.frontend[0].offset_mode)

