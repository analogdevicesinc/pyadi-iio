# Copyright (C) 2025 Analog Devices, Inc.
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

import argparse

from adi.ad5710r import ad5710r


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AD5710R Example Script")
    parser.add_argument(
        "--uri",
        type=str,
        help="The URI for the AD5710R device",
        default="serial:COM7,230400,8n1",
    )
    parser.add_argument(
        "--device_name",
        type=str,
        choices=["ad5710r"],
        help="The device name (Supported devices are ad5710r)",
        default="ad5710r",
    )

    # Parse arguments
    args = parser.parse_args()

    # Set up AD5710R
    ad5710r_dev = ad5710r(uri=args.uri)
    ad5710r_dev.all_ch_operating_mode = "normal_operation"

    ad5710r_dev.reference_select = "internal_ref"

    # Configure channel 0
    chn_num = 0
    ad5710r_chan = ad5710r_dev.channel[chn_num]

    # Set channel 0 to Voltage mode
    ad5710r_chan.ch_mode = "VMODE"

    # Update dac output for channel 0 instantaneously using the 'raw' attribute
    ad5710r_chan.raw = 25000

    # Update dac output for channel 0 using software LDAC operation
    ad5710r_chan.input_register = 5000
    ad5710r_dev.sw_ldac_trigger = "ldac_trigger"

    # Update dac output of channel 0 using hardware LDAC operation
    ad5710r_chan.input_register = 40000
    ad5710r_dev.hw_ldac_trigger = "ldac_trigger"

    # Set mux value to "vout0" to monitor vout0 value on the mux_out pin
    ad5710r_dev.mux_out_select = "VOUT0"

    # Set 0 to 2Vref as output range
    ad5710r_dev.range = "0_to_2VREF"

    # Determine output voltage using scale and offset
    raw = int(ad5710r_chan.raw)
    scale = float(ad5710r_chan.scale)
    offset = int(ad5710r_chan.offset)
    print(f"Channel{chn_num} voltage in Volts: {(raw + offset) * scale/1000}")


if __name__ == "__main__":
    main()
