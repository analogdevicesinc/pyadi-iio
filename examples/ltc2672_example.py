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

from adi.ltc2672 import ltc2672

# Set up LTC2672
ltc2672_dev = ltc2672(uri="serial:COM34,230400,8n1", device_name="ltc2672-16")

# Set all channels span to 50mA
ltc2672_dev.all_chns_span = "50mA"

# Configure channel 0 and update dac output using the 'raw' attribute
chn_num = 0
ltc2672_chan = ltc2672_dev.channel[chn_num]
ltc2672_chan.raw = 25000

# Get the current value of channel 0 in mA for the corresponding raw value set
current_val_ma = ltc2672_chan.input_register_and_update
print(f"Channel{chn_num} current in mA: {current_val_ma}")

# Set current value for channel 0 in mA
ltc2672_chan.input_register_and_update = 45

# Set mux value to "iout0" to monitor iout0 value on the mux_out pin
ltc2672_dev.mux = "iout0"

# Powerdown all the channels of the DAC
ltc2672_dev.powerdown_chip = "powerdown"
