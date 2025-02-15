# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
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

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad353xr(tx, context_manager):
    """ AD353xr DAC """

    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Constructor for AD353xr class."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad3530r"]

        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(
                    f"Not a compatible device: {device_name}. Supported device names "
                    f"are: {','.join(compatible_parts)}"
                )

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._txdac = device
                break

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        if not self._txdac:
            raise Exception("Error in selecting matching device")

        self.output_bits = []
        for ch in self._ctrl.channels:
            name = ch.id
            self.output_bits.append(ch.data_format.bits)
            self._tx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))
            setattr(self, name, self._channel(self._ctrl, name))

        tx.__init__(self)

    ### Add device attributes here ###

    @property
    def sampling_frequency(self):
        """AD353xr sampling frequency config"""
        return self._get_iio_dev_attr_str("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def all_ch_operating_mode_avail(self):
        """AD353xr all channels operating mode available"""
        return self._get_iio_dev_attr_str("all_ch_operating_mode_available")

    @property
    def all_ch_operating_mode(self):
        """AD353xr all channels operating mode config"""
        return self._get_iio_dev_attr_str("all_ch_operating_mode")

    @all_ch_operating_mode.setter
    def all_ch_operating_mode(self, value):
        if value in self.all_ch_operating_mode_avail:
            self._set_iio_dev_attr_str("all_ch_operating_mode", value)
        else:
            raise ValueError(
                "Error: Operating mode not supported \nUse one of: "
                + str(self.all_ch_operating_mode_avail)
            )

    @property
    def all_ch_input_registers(self):
        """AD353xr all input registers config"""
        return self._get_iio_dev_attr_str("all_ch_input_registers")

    @all_ch_input_registers.setter
    def all_input_registers(self, value):
        self._set_iio_dev_attr_str("all_ch_input_registers", value)

    @property
    def all_ch_raw(self):
        """AD353xr all dac registers config"""
        return self._get_iio_dev_attr_str("all_ch_raw")

    @all_ch_raw.setter
    def all_ch_raw(self, value):
        self._set_iio_dev_attr_str("all_ch_raw", value)

    @property
    def reference_select_available(self):
        """AD353xr reference voltage available"""
        return self._get_iio_dev_attr_str("reference_select_available")

    @property
    def reference_select(self):
        """AD353xr reference voltage config"""
        return self._get_iio_dev_attr_str("reference_select")

    @reference_select.setter
    def reference_select(self, value):
        if value in self.reference_select_available:
            self._set_iio_dev_attr_str("reference_select", value)
        else:
            raise ValueError(
                "Error: Reference select not supported \nUse one of: "
                + str(self.reference_select_available)
            )

    @property
    def sw_ldac_trigger_avail(self):
        """AD353xr sw_ldac_trigger available"""
        return self._get_iio_dev_attr_str("sw_ldac_trigger_available")

    @property
    def sw_ldac_trigger(self):
        """AD353xr software ldac trigger config"""
        return self._get_iio_dev_attr_str("sw_ldac_trigger")

    @sw_ldac_trigger.setter
    def sw_ldac_trigger(self, value):
        if value in self.sw_ldac_trigger_avail:
            self._set_iio_dev_attr_str("sw_ldac_trigger", value)
        else:
            raise ValueError(
                "Error: Trigger value not supported \nUse one of: "
                + str(self.sw_ldac_trigger_avail)
            )

    @property
    def hw_ldac_trigger_avail(self):
        """AD353xr hw_ldac_trigger available"""
        return self._get_iio_dev_attr_str("hw_ldac_trigger_available")

    @property
    def hw_ldac_trigger(self):
        """AD353xr hardware ldac trigger config"""
        return self._get_iio_dev_attr_str("hw_ldac_trigger")

    @hw_ldac_trigger.setter
    def hw_ldac_trigger(self, value):
        if value in self.hw_ldac_trigger_avail:
            self._set_iio_dev_attr_str("hw_ldac_trigger", value)
        else:
            raise ValueError(
                "Error: Trigger value not supported \nUse one of: "
                + str(self.hw_ldac_trigger_avail)
            )

    @property
    def range_avail(self):
        """AD353xr range available"""
        return self._get_iio_dev_attr_str("range_available")

    @property
    def range(self):
        """AD353xr range config"""
        return self._get_iio_dev_attr_str("range")

    @range.setter
    def range(self, value):
        if value in self.range_avail:
            self._set_iio_dev_attr_str("range", value)
        else:
            raise ValueError(
                "Error: Range option not supported \nUse one of: "
                + str(self.range_avail)
            )

    @property
    def mux_out_select_avail(self):
        """AD353xr mux_out_select available"""
        return self._get_iio_dev_attr_str("mux_out_select_available")

    @property
    def mux_out_select(self):
        """AD353xr mux out select"""
        return self._get_iio_dev_attr_str("mux_out_select")

    @mux_out_select.setter
    def mux_out_select(self, value):
        if value in self.mux_out_select_avail:
            self._set_iio_dev_attr_str("mux_out_select", value)
        else:
            raise ValueError(
                "Error: Mux output option not supported \nUse one of: "
                + str(self.mux_out_select_avail)
            )

    ############################################################################

    class _channel(attribute):
        """AD353xr channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        ### Add channel attributes here ###
        @property
        def input_register(self):
            """AD353xr channel input register value"""
            return self._get_iio_attr(self.name, "input_register", True)

        @input_register.setter
        def input_register(self, value):
            self._set_iio_attr(self.name, "input_register", True, str(int(value)))

        @property
        def raw(self):
            """AD353xr channel raw value"""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            self._set_iio_attr(self.name, "raw", True, str(int(value)))

        @property
        def offset(self):
            """AD353xr channel offset"""
            return self._get_iio_attr(self.name, "offset", True)

        @property
        def scale(self):
            """AD353xr channel scale"""
            return self._get_iio_attr(self.name, "scale", True)

        @property
        def operating_mode_avail(self):
            """AD353xr channel operating mode settings"""
            return self._get_iio_attr_str(self.name, "operating_mode_available", True)

        @property
        def operating_mode(self):
            """AD353xr channel operating mode"""
            return self._get_iio_attr_str(self.name, "operating_mode", True)

        @operating_mode.setter
        def operating_mode(self, value):
            if value in self.operating_mode_avail:
                self._set_iio_attr(self.name, "operating_mode", True, value)
            else:
                raise ValueError(
                    "Error: Operating mode not supported \nUse one of: "
                    + str(self.operating_mode_avail)
                )

        #####################################################################
