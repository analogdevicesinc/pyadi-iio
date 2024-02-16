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


@pytest.mark.parametrize("double_functions", [
    ["digital_input_loop", "voltage_out", "current_out"]
])
def test_switch_config_runtime_double_channels_cv(double_functions: list):
    """
    Test that for each of the double_functions channels, 2 channels are created voltage and current
    :param double_functions:
    """
    for function in double_functions:
        swiot = swiot_utils.get_config_swiot(uri=constants.URI)

        swiot.ch0_enable = "1"
        swiot.ch0_device = "ad74413r"
        swiot.ch0_function = function

        # switch to runtime and check the modified properties
        swiot_utils.get_runtime_swiot(uri=constants.URI)

        ad74413r = adi.ad74413r(uri=constants.URI)
        assert "voltage0" in ad74413r.channel, f"could not find voltage0 on ad74413r with {function} function"
        assert "current0" in ad74413r.channel, f"could not find current0 on ad74413r with {function} function"


@pytest.mark.parametrize("double_functions", [
    ["current_in_loop_hart", "current_in_loop"]
])
def test_switch_config_runtime_double_channels_cc(double_functions: list):
    """
    Test that for each of the double_functions channels, 2 channels are created current (tx) and current (rx)
    :param double_functions:
    """
    for function in double_functions:
        swiot = swiot_utils.get_config_swiot(uri=constants.URI)

        swiot.ch0_enable = "1"
        swiot.ch0_device = "ad74413r"
        swiot.ch0_function = function

        # switch to runtime and check the modified properties
        swiot_utils.get_runtime_swiot(uri=constants.URI)

        ad74413r = adi.ad74413r(uri=constants.URI)

        channel_output = ad74413r.tx_channel["current0"]
        channel_input = ad74413r.rx_channel["current0"]

        assert channel_input is not None, f"could not find input current0 on ad74413r with {function} function"
        assert channel_output is not None, f"could not find output current0 on ad74413r with {function} function"
