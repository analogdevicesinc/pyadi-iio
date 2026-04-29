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

import matplotlib.pyplot as plt

from adi import ad4692


def main():
    ######## User configuration ##########
    # Configure the backend for PC to IIOD interface
    uri = "serial:COM21,230400"  # For UART, baud rate must be same as set in the FW. COM port is physical Or VCOM.
    device_name = "ad4692"  # Name of the device must be same as set in the FW.
    ######################################

    # Create an IIO device context
    device = ad4692(uri, device_name)
    device._ctx.set_timeout(100000)

    ######## User configuration ##########
    # Channels to be captured e.g. ["voltage0"]: 1chn, ["voltage0, voltage1"]: 2chns
    device.rx_enabled_channels = [
        "voltage0",
    ]

    device.rx_buffer_size = (
        400  # Size of the IIO buffer (buffer is submitted during call to rx() method)
    )
    # Get voltage converted data as output
    device.rx_output_type = "SI"
    ######################################

    # Receive data from device
    data = device.rx()

    del device  # Close the device context

    plt.plot(range(0, len(data)), data, label="voltage0")
    plt.xlabel("Data Point")
    plt.ylabel("Voltage (mV)")
    plt.legend(
        bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
        loc="lower left",
        ncol=4,
        mode="expand",
        borderaxespad=0.0,
    )

    plt.show()


if __name__ == "__main__":
    main()
