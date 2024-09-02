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

import argparse

import numpy as np
from adi.ad7091rx import ad7091rx


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AD7091R Example Script")
    parser.add_argument(
        "--uri",
        type=str,
        help="The URI for the AD7091R device",
        default="serial:COM7,230400,8n1",
    )
    parser.add_argument(
        "--device_name",
        type=str,
        choices=["ad7091r-2", "ad7091r-4", "ad7091r-8"],
        help="The device name (Supported devices are ad7091r-2, ad7091r-4, ad7091r-8)",
        default="ad7091r-8",
    )

    # Parse arguments
    args = parser.parse_args()

    # Set up AD7091R device
    ad7091r_dev = ad7091rx(uri=args.uri, device_name=args.device_name)

    # Get ADC channel 0 raw value and print it
    raw = ad7091r_dev.channel[0].raw
    print(f"Raw value read from channel0 is {raw}")

    # Capture a buffer of 100 samples from channel 0 and display them
    chn = 0
    ad7091r_dev._rx_data_type = np.int32
    ad7091r_dev.rx_output_type = "raw"
    ad7091r_dev.rx_enabled_channels = [chn]
    ad7091r_dev.rx_buffer_size = 100

    data = ad7091r_dev.rx()

    print(data)


if __name__ == "__main__":
    main()
