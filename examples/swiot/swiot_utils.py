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

import adi
import iio

from examples.swiot import constants

AD74413R_INPUT_CHANNEL_ATTRIBUTES = ["sampling_frequency", "sampling_frequency_available", "raw", "scale", "offset"]
AD74413R_INPUT_CHANNEL_ATTRIBUTES_VALUES = {
    "sampling_frequency": [20, 4800, 10, 1200],
    "raw": [4, 1]
}

AD74413R_INPUT_CHANNEL_ATTRIBUTES_DIO_IN = ["sampling_frequency", "sampling_frequency_available", "raw", "threshold"]
AD74413R_INPUT_CHANNEL_ATTRIBUTES_DIO_IN_VALUES = {
    "sampling_frequency": [20, 4800, 10, 1200],
    "raw": [4, 1]
}
# threshold already has its own test, no need to test again

AD74413R_OUTPUT_CHANNEL_ATTRIBUTES = ["raw", "scale", "offset", "slew_en", "slew_rate", "slew_rate_available",
                                      "slew_step", "slew_step_available"]
AD74413R_OUTPUT_CHANNEL_ATTRIBUTES_VALUES = {
    "raw": [4, 1],
    "slew_en": [0, 1],
    "slew_rate": [4, 64, 150, 240],
    "slew_step": [64, 120, 500, 1820]
}

AD74413R_DIAG_CHANNEL_ATTRIBUTES = ["sampling_frequency", "sampling_frequency_available", "diag_function",
                                    "diag_function_available", "raw", "scale", "offset"]
AD74413R_DIAG_CHANNEL_ATTRIBUTES_VALUES = {
    "sampling_frequency": [20, 4800, 10, 1200],
    "diag_function": ["agnd", "temp", "avdd", "avss", "refout", "aldo_5v", "aldo_1v8", "dldo_1v8", "dvcc", "iovdd",
                      "sensel_a", "sensel_b", "sensel_c", "sensel_d"],
    "raw": [4, 1]
}

AD74413R_FUNCTION_AVAILABLE = ["voltage_out", "current_out", "voltage_in", "current_in_ext",
                               "current_in_loop", "resistance", "digital_input", "digital_input_loop",
                               "current_in_ext_hart", "current_in_loop_hart"]

MAX14906_INPUT_CHANNEL_ATTRIBUTES = ["raw", "offset", "scale", "IEC_type", "IEC_type_available"]
MAX14906_OUTPUT_CHANNEL_ATTRIBUTES = ["raw", "offset", "scale", "do_mode", "do_mode_available", "current_limit",
                                      "current_limit_available"]


def get_runtime_swiot(uri: str) -> adi.swiot:
    """
    Assures that the adi.swiot device returned is set to runtime mode
    :param uri: string containing the uri
    :return: adi.swiot device
    """
    swiot = adi.swiot(uri=uri)

    # make sure the device is in runtime mode
    if swiot.mode == "config":
        swiot.mode = "runtime"

        # reconnect to the new context
        swiot = adi.swiot(uri=uri)

    assert swiot.mode == "runtime", "SWIOT could not be set to runtime mode"

    # return the new SWIOT context
    return swiot


def get_config_swiot(uri: str) -> adi.swiot:
    """
    Assures that the adi.swiot device returned is set to config mode
    :param uri: string containing the uri
    :return: adi.swiot device
    """
    swiot = adi.swiot(uri=uri)

    # make sure the device is in config mode
    if swiot.mode == "runtime":
        swiot.mode = "config"
        # reconnect to the new context
        swiot = adi.swiot(uri=uri)

    assert swiot.mode == "config", "SWIOT could not be set to config mode"

    # return the new SWIOT context
    return swiot


def verify_output_channel_ad74413r(channel: iio.Channel) -> None:
    """
    Tests if the channel received as parameter has all specific output attributes and performs a read/write with
    random attribute specific variables
    :param channel: iio.Channel
    """
    attribute_names = list(channel.attrs.keys())

    # check that all attributes are in the channel
    for attribute in AD74413R_OUTPUT_CHANNEL_ATTRIBUTES:
        assert attribute in attribute_names

        if attribute in AD74413R_OUTPUT_CHANNEL_ATTRIBUTES_VALUES:
            # perform a read/write test on the current channel
            values = AD74413R_OUTPUT_CHANNEL_ATTRIBUTES_VALUES[attribute]
            for value in values:
                channel.attrs[attribute] = value
                assert channel.attrs[attribute] == value

        attribute_names.remove(attribute)

    # check that there are no extra attributes added
    assert not attribute_names


def verify_diag_channel_ad74413r(channel: iio.Channel) -> None:
    """
    Tests if the channel received as parameter has all specific diag attributes and performs a read/write with
    random attribute specific variables
    :param channel: iio.Channel
    """
    attribute_names = list(channel.attrs.keys())

    # check that all attributes are in the channel
    for attribute in AD74413R_DIAG_CHANNEL_ATTRIBUTES:
        assert attribute in attribute_names

        if attribute in AD74413R_DIAG_CHANNEL_ATTRIBUTES_VALUES:
            # perform a read/write test on the current channel
            values = AD74413R_DIAG_CHANNEL_ATTRIBUTES_VALUES[attribute]
            for value in values:
                channel.attrs[attribute] = value
                assert channel.attrs[attribute] == value

        attribute_names.remove(attribute)

    # check that there are no extra attributes added
    assert not attribute_names


def verify_input_channel_ad74413r(channel: iio.Channel) -> None:
    """
    Tests if the channel received as parameter has all specific input attributes and performs a read/write with
    random attribute specific variables
    :param channel: iio.Channel
    """
    attribute_names = list(channel.attrs.keys())

    if "threshold" in attribute_names:
        # check that all attributes are in the channel
        for attribute in AD74413R_INPUT_CHANNEL_ATTRIBUTES_DIO_IN:
            assert attribute in attribute_names

            if attribute in AD74413R_INPUT_CHANNEL_ATTRIBUTES_DIO_IN_VALUES:
                # perform a read/write test on the current channel
                values = AD74413R_INPUT_CHANNEL_ATTRIBUTES_DIO_IN_VALUES[attribute]
                for value in values:
                    channel.attrs[attribute] = value
                    assert channel.attrs[attribute] == value

            attribute_names.remove(attribute)
    else:
        # check that all attributes are in the channel
        for attribute in AD74413R_INPUT_CHANNEL_ATTRIBUTES:
            assert attribute in attribute_names

            if attribute in AD74413R_INPUT_CHANNEL_ATTRIBUTES_VALUES:
                # perform a read/write test on the current channel
                values = AD74413R_INPUT_CHANNEL_ATTRIBUTES_VALUES[attribute]
                for value in values:
                    channel.attrs[attribute] = value
                    assert channel.attrs[attribute] == value

            attribute_names.remove(attribute)

    # check that there are no extra attributes added
    assert not attribute_names


def verify_input_channel_max14906(channel: iio.Channel) -> None:
    """
    Tests if the channel received as parameter has all specific input attributes and performs a read/write with
    random attribute specific variables
    :param channel: iio.Channel
    """
    attribute_names = list(channel.attrs.keys())

    for attribute in MAX14906_INPUT_CHANNEL_ATTRIBUTES:
        assert attribute in attribute_names
        attribute_names.remove(attribute)

    assert not attribute_names


def verify_output_channel_max14906(channel: iio.Channel) -> None:
    """
    Tests if the channel received as parameter has all specific output attributes and performs a read/write with
    random attribute specific variables
    :param channel: iio.Channel
    """
    attribute_names = list(channel.attrs.keys())

    for attribute in MAX14906_OUTPUT_CHANNEL_ATTRIBUTES:
        assert attribute in attribute_names
        attribute_names.remove(attribute)

    assert not attribute_names


def setup_config_mode(configuration: list) -> adi.swiot:
    """
    Sets the specified configuration as parameter, all channels will be enabled and switch to runtime
    :param configuration: 4x2 matrix where the first index is the channel index and the second one is either
    0 - device, 1 - device function
    :return adi.swiot object in runtime mode
    """
    swiot = get_config_swiot(uri=constants.URI)

    swiot.ch0_enable = "1"
    swiot.ch0_device = configuration[0][0]
    swiot.ch0_function = configuration[0][1]

    swiot.ch1_enable = "1"
    swiot.ch1_device = configuration[1][0]
    swiot.ch1_function = configuration[1][1]

    swiot.ch2_enable = "1"
    swiot.ch2_device = configuration[2][0]
    swiot.ch2_function = configuration[2][1]

    swiot.ch3_enable = "1"
    swiot.ch3_device = configuration[3][0]
    swiot.ch3_function = configuration[3][1]

    # switch to runtime and check the modified properties
    return get_runtime_swiot(uri=constants.URI)
