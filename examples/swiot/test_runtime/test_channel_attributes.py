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

import iio
import pytest

from examples.swiot import swiot_utils, constants


@pytest.mark.parametrize(
    "configuration",
    [[
        ["ad74413r", "voltage_in"],
        ["ad74413r", "current_in_loop_hart"],
        ["ad74413r", "digital_input_loop"],
        ["ad74413r", "voltage_out"]
    ]]
)
def test_ad74413r_channel_attrs(configuration):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)

    # initial value
    ad74413r = swiot.ctx.devices[0]

    # search for ad74413r in context
    for device in swiot.ctx.devices:
        if device.name == "ad74413r":
            ad74413r = device
            break

    # execute a check for each channel type and it's attributes
    for channel in ad74413r.channels:
        channel: iio.Channel
        if channel.output:
            swiot_utils.verify_output_channel_ad74413r(channel)
        else:
            if channel.name is not None:
                if "diag" in channel.name:
                    swiot_utils.verify_diag_channel_ad74413r(channel)
            else:
                swiot_utils.verify_input_channel_ad74413r(channel)


@pytest.mark.parametrize(
    "configuration",
    [[
        ["max14906", "output"],
        ["max14906", "input"],
        ["max14906", "output"],
        ["max14906", "input"]
    ]]
)
def test_max14906_channel_attrs(configuration):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)

    # initial value
    max14906 = swiot.ctx.devices[0]

    # search for ad74413r in context
    for device in swiot.ctx.devices:
        if device.name == "max14906":
            max14906 = device
            break

    # execute a check for each channel type and it's attributes
    for channel in max14906.channels:
        channel: iio.Channel
        if channel.id != constants.FAULT_CHANNEL_ID:
            if channel.output:
                swiot_utils.verify_output_channel_max14906(channel)
            else:
                swiot_utils.verify_input_channel_max14906(channel)
