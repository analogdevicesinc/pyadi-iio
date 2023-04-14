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


class cn0554:
    """ CN0554 Mixed Signal Raspberry Pi Hat """

    _in_range_available = ["+/-13.75", "+27.5", "+2.5"]
    _out_reference_available = [4.096, 2.5]
    _out_channels = 16
    _in_channels = 8
    _scale_res_div = 11

    def __init__(self, uri="ip:analog.local"):
        """adc_in_channels: ADC channel names derived from onboard AD7124."""
        self.adc_in_channels = []

        """dac_out_channels: DAC channel names derived from onboard LTC2688."""
        self.dac_out_channels = []

        self.adc = adi.ad7124(uri=uri)
        self.adc._rx_unbuffered_data = False
        self.adc._rx_output_type = "SI"
        self.rx_buffer_size = 1024
        self.adc.sample_rate = 19200

        for in_ch in self.adc.channel:
            in_name = "voltage"
            for char in in_ch.name:
                if char.isnumeric():
                    in_name += char

            """Default channels range is set to '+/-13.75'"""
            setattr(self, in_name + "_in_range", self._in_range_available[0])

            self.adc_in_channels.append(in_name)

        self.dac = adi.ltc2688(uri=uri)
        self.dac_out_channels = self.dac.channel_names

        """out_reference: DAC voltage reference in Volts. Valid values are 4.096 and 2.5."""
        self.out_reference = self._out_reference_available[0]

    @property
    def in_scale(self):
        """in_scale: unitless scale factor based on onboard resistor divider"""
        return self._scale_res_div

    @in_scale.setter
    def in_scale(self, value):
        """in_scale property setter"""
        if value <= 0:
            raise Exception("Scale Factor must be greater than 0")

        self._scale_res_div = value

    @property
    def rx_output_type(self):
        """Get value of CN0554's rx output type (raw or SI)"""
        return self.adc._rx_output_type

    @rx_output_type.setter
    def rx_output_type(self, value):
        """Set value of CN0554's rx output type (raw or SI)"""
        self.adc._rx_output_type = value

    @property
    def rx_enabled_channels(self):
        """Get list of enabled input adc channels"""
        return self.adc.rx_enabled_channels

    @rx_enabled_channels.setter
    def rx_enabled_channels(self, value):
        """Set list of enabled input adc channels"""
        self.adc.rx_enabled_channels = value

    @property
    def out_channels(self):
        """Get number of DAC output channels"""
        return self._out_channels

    @property
    def in_channels(self):
        """Get number of ADC input channels"""
        return self._in_channels

    @property
    def out_reference(self):
        """Get voltage reference used for DAC channels"""
        return self.dac.vref

    @out_reference.setter
    def out_reference(self, value):
        """Set voltage reference used for DAC channels"""
        if value not in self._out_reference_available:
            raise Exception("out_reference value must be 4.096 or 2.5")

        self.dac.vref = value

    @property
    def sample_rate(self):
        """Get CN0554's AD7124 sampling rate"""
        return self.adc.sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        """Set CN0554's AD7124 sampling rate"""
        self.adc.sample_rate = value

    @property
    def rx_buffer_size(self):
        """Get number of datapoints used during capture"""
        return self.adc.rx_buffer_size

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        """Set number of datapoints used during capture"""
        self.adc.rx_buffer_size = value

    def rx(self):
        """Get data from enabled ADC channels"""
        return self.adc.rx()

    def convert_to_volts(self, in_voltage, channel):
        """Convert ADC data using scale factors based on header configuration"""
        ch_range = eval("self." + str(channel) + "_in_range")
        try:
            ch_index = self._in_range_available.index(ch_range)

        except ValueError:
            raise Exception(
                "Invalid _in_range detected. Valid values are '+/-13.75', '+27.5', and '+2.5'."
            )

        if ch_index < 2:
            scale_sig = []

            for sigs in in_voltage:
                scale_sig.append(sigs * self.in_scale)

            return scale_sig

        return in_voltage
