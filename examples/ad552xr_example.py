# Copyright (C) 2026 Analog Devices, Inc.
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


from adi.ad552xr import ad552xr

if __name__ == "__main__":
    ######## User configuration ##########
    # Configure the backend for PC to IIOD interface
    uri = "serial:COM34,230400"
    device_name = "ad5529r"
    ######################################

    # Create an IIO device context
    ad552xr_dev = ad552xr(uri, device_name)

    ######## User configuration ##########
    # Sampling frequency
    ad552xr_dev.sampling_frequency = 500000

    # Configure channel 0
    chn_num = 0
    ad552xr_chan = ad552xr_dev.channel[chn_num]

    # Configure output range
    ad552xr_chan.range_sel = "bipolar_10V"

    # Update raw value and enable the channel output
    ad552xr_chan.raw = 0xFFFF
    ad552xr_chan.output_state = "enable"

    # Configure LDAC settings
    ad552xr_chan.hw_sw_sel = "hw"

    ad552xr_chan.hw_ldac_edge_sel = "rising_edge"
    ad552xr_chan.hw_ldac_pin_sel = "ldac_toggle_0"

    ad552xr_chan.input_register_a = 0x7FFF
    ad552xr_chan.input_register_b = 0x0000

    # Configure function generator
    ad552xr_chan.func_sel = "ldac_toggle"

    # Determine output voltage using scale and offset
    raw = int(ad552xr_chan.raw)
    scale = float(ad552xr_chan.scale)
    offset = int(ad552xr_chan.offset)
    print(f"Channel{chn_num} voltage in Volts: {(raw + offset) * scale / 1E3}")

    ######################################

    # Delete the context
    del ad552xr_dev._ctx
    del ad552xr_dev
