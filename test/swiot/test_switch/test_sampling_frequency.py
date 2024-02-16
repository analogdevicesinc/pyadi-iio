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

import pytest
import adi
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
def test_input_channels_sampling_frequency_and_scan_element(configuration: list):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)

    ad74413r = None
    for device in swiot.ctx.devices:
        if device.name == "ad74413r":
            ad74413r = device
            break

    if ad74413r is None:
        assert False, "Could not find ad74413r"

    for channel in ad74413r.channels:
        # all input channels should be scan-elements and have the sampling_frequency attribute
        if channel.output is False:
            if channel.id != constants.FAULT_CHANNEL_ID:
                assert channel.scan_element
                assert "sampling_frequency" in channel.attrs


@pytest.mark.parametrize(
    "configuration",
    [[
        ["ad74413r", "voltage_in"],
        ["ad74413r", "current_in_loop_hart"],
        ["ad74413r", "digital_input_loop"],
        ["ad74413r", "voltage_out"]
    ]]
)
@pytest.mark.parametrize("sampling_frequency_available", [
    [20, 4800, 10, 1200]
])
def test_sampling_frequency(configuration: list, sampling_frequency_available):
    swiot_utils.setup_config_mode(configuration=configuration)

    ad74413r = adi.ad74413r(uri=constants.URI)

    # get first (random) input channel and set the sampling frequency,
    # after that all channels should change their sampling frequency
    frequency = sampling_frequency_available[0]
    ad74413r.rx_channel[list(ad74413r.rx_channel.items())[0][0]].sampling_frequency = frequency

    for input_channel in ad74413r.rx_channel.values():
        if input_channel.name != constants.FAULT_CHANNEL_ID:
            assert input_channel.sampling_frequency == frequency
