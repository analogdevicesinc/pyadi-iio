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


@pytest.mark.parametrize("config_swiot_attributes", [[
    "reset", "serial_id", "mode", "mode_available", "signal_mse", "identify", "ext_psu",
    "ch0_enable", "ch1_enable", "ch2_enable", "ch3_enable",
    "ch0_function", "ch1_function", "ch2_function", "ch3_function",
    "ch0_device", "ch1_device", "ch2_device", "ch3_device",
    "ch0_function_available", "ch1_function_available",
    "ch2_function_available", "ch3_function_available",
    "ch0_device_available", "ch1_device_available",
    "ch2_device_available", "ch3_device_available"
]])
def test_config_swiot_attributes_list(config_swiot_attributes: list) -> None:
    """
    Checks if the config mode has all attributes specified in config_swiot_attributes
    :param config_swiot_attributes: list of attributes
    """
    context = swiot_utils.get_config_swiot(uri=constants.URI)

    # initial value
    swiot: iio.Device = context.ctx.devices[0]

    # search for swiot device
    for device in context.ctx.devices:
        if device.name == "swiot":
            swiot = device
            break

    # convert to list the attribute keys
    attributes: list = list(swiot.attrs.keys())

    # check that every config swiot attribute from constants.py is present in the swiot config context
    for attribute in config_swiot_attributes:
        assert attribute in attributes
        attributes.remove(attribute)

    # check that all attributes were used
    assert not attributes


def test_rw_channel_enable():
    """
    Tests the read/write from each channel enable
    """
    context = swiot_utils.get_config_swiot(uri=constants.URI)

    context.ch0_enable = '1'
    assert context.ch0_enable == '1'
    context.ch0_enable = '0'
    assert context.ch0_enable == '0'

    context.ch1_enable = '1'
    assert context.ch1_enable == '1'
    context.ch1_enable = '0'
    assert context.ch1_enable == '0'

    context.ch2_enable = '1'
    assert context.ch2_enable == '1'
    context.ch2_enable = '0'
    assert context.ch2_enable == '0'

    context.ch3_enable = '1'
    assert context.ch3_enable == '1'
    context.ch3_enable = '0'
    assert context.ch3_enable == '0'


def test_rw_channel_device():
    """
    Tests the read/write for each device
    """
    context = swiot_utils.get_config_swiot(uri=constants.URI)

    context.ch0_device = "ad74413r"
    assert context.ch0_device == "ad74413r"
    context.ch0_device = "max14906"
    assert context.ch0_device == "max14906"

    context.ch1_device = "ad74413r"
    assert context.ch1_device == "ad74413r"
    context.ch1_device = "max14906"
    assert context.ch1_device == "max14906"

    context.ch2_device = "ad74413r"
    assert context.ch2_device == "ad74413r"
    context.ch2_device = "max14906"
    assert context.ch2_device == "max14906"

    context.ch3_device = "ad74413r"
    assert context.ch3_device == "ad74413r"
    context.ch3_device = "max14906"
    assert context.ch3_device == "max14906"


@pytest.mark.parametrize("ad74413r_functions", [
    ["high_z", "voltage_out", "current_out", "voltage_in",
     "current_in_ext", "current_in_loop", "resistance", "digital_input",
     "digital_input_loop", "current_in_ext_hart", "current_in_loop_hart"]
])
def test_rw_channel_function_ad74413r(ad74413r_functions: list) -> None:
    """
    Tests the read/write for each function from the ad74413r device
    :param ad74413r_functions: list of functions that can be set to ad74413r
    """
    context = swiot_utils.get_config_swiot(uri=constants.URI)

    context.ch0_device = "ad74413r"
    for function in ad74413r_functions:
        context.ch0_function = function
        assert context.ch0_function == function

    context.ch1_device = "ad74413r"
    for function in ad74413r_functions:
        context.ch1_function = function
        assert context.ch1_function == function

    context.ch2_device = "ad74413r"
    for function in ad74413r_functions:
        context.ch2_function = function
        assert context.ch2_function == function

    context.ch3_device = "ad74413r"
    for function in ad74413r_functions:
        context.ch3_function = function
        assert context.ch3_function == function


@pytest.mark.parametrize("max14906_functions", [
    ["output", "input", "high_z"]
])
def test_rw_channel_function_max14906(max14906_functions: list) -> None:
    """
    Tests the read/write for each function from the max14906 device
    :param max14906_functions: list of functions that can be set to max14906
    """
    context = swiot_utils.get_config_swiot(uri=constants.URI)

    context.ch0_device = "max14906"
    for function in max14906_functions:
        context.ch0_function = function
        assert context.ch0_function == function

    context.ch1_device = "max14906"
    for function in max14906_functions:
        context.ch1_function = function
        assert context.ch1_function == function

    context.ch2_device = "max14906"
    for function in max14906_functions:
        context.ch2_function = function
        assert context.ch2_function == function

    context.ch3_device = "max14906"
    for function in max14906_functions:
        context.ch3_function = function
        assert context.ch3_function == function
