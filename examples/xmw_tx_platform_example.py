# Copyright (C) 2023 Analog if_devices, Inc.
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

import adi

# Set up MxFE chip to generate Intermediate Frequency (refer to ad9081_example.py)
if_dev = adi.ad9081(uri="ip:analog.local")
print("--Setting up MxFE chip")

# Configure TX properties
if_dev.tx_channel_nco_frequencies = [0] * 2

# Set Intermediate Frequency to 4.5 GHz on Channel 0
if_dev.tx_main_nco_frequencies = [4500000000, 0]
print(
    f"Intermediate frequency is set to {if_dev.tx_main_nco_frequencies[0] / 1000000} MHz."
)

fs = 0
# Set single DDS tone for TX on one transmitter
if_dev.dds_single_tone(fs / 10, 0.5, channel=0)

# Set up RF front end system and configure properties
rf_system = adi.xmw_tx_platform(uri="ip:analog.local")
print("--Setting up RF platform")

# Set up IF Attenuation (0dB)
rf_system.if_attenuation_decimal = 0

# Set up Output Frequency to transmit (2~24 GHz)
rf_system.output_freq_MHz = 12500

# Observe output on Spectrum Analyzer
input(
    f"Observe RF output at {rf_system.output_freq_MHz} MHz on the Spectrum Analyzer. Press Enter to end program."
)
