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


def test_switch_runtime_config():
    swiot = swiot_utils.get_runtime_swiot(uri=constants.URI)
    assert swiot.mode == "runtime"

    swiot = swiot_utils.get_config_swiot(uri=constants.URI)
    assert swiot.mode == "config"


@pytest.mark.parametrize(
    "configuration",
    [[
        ["ad74413r", "current_in_loop"],
        ["ad74413r", "voltage_out"],
        ["ad74413r", "current_out"],
        ["ad74413r", "voltage_in"]
    ]]
)
@pytest.mark.parametrize(
    "fault_channel_id",
    ["voltage"]
)
def test_switch_config_runtime_all_ad74413r(configuration: list, fault_channel_id: str):
    """
    Basic hardcoded test for the specified configuration only with ad74413r
    :param configuration:
    :param fault_channel_id:
    """
    # configure and switch to runtime
    swiot_utils.setup_config_mode(configuration=configuration)

    # reconnect to the new context
    ad74413r = adi.ad74413r(uri=constants.URI)

    ad74413r_channels = list(ad74413r.channel.keys())

    # verify that the channels selected in config mode appear in runtime mode
    assert "current0" in ad74413r_channels
    assert "current1" in ad74413r_channels
    assert "voltage2" in ad74413r_channels
    assert "voltage3" in ad74413r_channels
    assert "current0" in ad74413r_channels
    assert "voltage1" in ad74413r_channels
    assert "current2" in ad74413r_channels

    # check diag channels
    assert "voltage4" in ad74413r_channels
    assert "voltage5" in ad74413r_channels
    assert "voltage6" in ad74413r_channels
    assert "voltage7" in ad74413r_channels

@pytest.mark.parametrize(
    "configuration",
    [[
        ["max14906", "output"],
        ["max14906", "input"],
        ["max14906", "output"],
        ["max14906", "input"]
    ]]
)
def test_switch_config_runtime_all_max14906(configuration: list):
    """
    Basic hardcoded test for the specified configuration only with max14906
    :param configuration:
    """
    swiot_utils.setup_config_mode(configuration=configuration)

    # reconnect to the new context
    swiot_utils.get_runtime_swiot(uri=constants.URI)
    ad74413r = adi.ad74413r(uri=constants.URI)
    max14906 = adi.max14906(uri=constants.URI)

    # verify that the channels selected in config mode appear in runtime mode
    assert "voltage0" in max14906.channel
    assert "voltage1" in max14906.channel
    assert "voltage2" in max14906.channel
    assert "voltage3" in max14906.channel

    # check diag channels
    assert "voltage4" in ad74413r.channel
    assert "voltage5" in ad74413r.channel
    assert "voltage6" in ad74413r.channel
    assert "voltage7" in ad74413r.channel


@pytest.mark.parametrize(
    "configuration",
    [[
        ["max14906", "output"],
        ["max14906", "input"],
        ["ad74413r", "voltage_out"],
        ["ad74413r", "voltage_in"]
    ]]
)
def test_switch_config_runtime_mixt(configuration: list):
    """
    Basic hardcoded test for the specified configuration with both ad74413r and max14906
    :param configuration:
    """
    swiot_utils.setup_config_mode(configuration=configuration)

    # reconnect to the new context
    ad74413r = adi.ad74413r(uri=constants.URI)
    max14906 = adi.max14906(uri=constants.URI)

    # verify that the channels selected in config mode appear in runtime mode
    assert "current2" in ad74413r.channel
    assert "voltage3" in ad74413r.channel
    assert "voltage2" in ad74413r.channel

    assert "voltage0" in max14906.channel
    assert "voltage1" in max14906.channel

    # check diag channels
    assert "voltage4" in ad74413r.channel
    assert "voltage5" in ad74413r.channel
    assert "voltage6" in ad74413r.channel
    assert "voltage7" in ad74413r.channel
