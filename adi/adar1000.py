# Copyright (C) 2020 Analog Devices, Inc.
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

from math import pi, sin

from adi.attribute import attribute
from adi.context_manager import context_manager


class adar1000(attribute, context_manager):
    """ ADAR1000 Beamformer

    parameters:
        uri: type=string
            Optional parameter for the URI of IIO context with ADAR1000(s). If
            not given,
        context: type=iio.Context
            Optional parameter for IIO Context handle for the device. Don't use if
            instantiating the adar1000 class directly. The adar1000_array class
            will handle this if creating an array instance.
        chip_id: type=string
            Required string identifying the desired chip select and hardware ID
            for the ADAR1000. If creating a single adar1000 instance, you can
            typically leave the default value of "csb1_chip1" as long as the
            device tree label matches. If creating an adar1000_array instance,
            the array class will handle the instantiation of individual adar1000
            handles.
        device_number: type=int
            Required integer indicating the device number in the array. If creating
            a single adar1000 instance, this value should be 1. If creating an
            adar1000_array instance, the array class will handle the instantiation
            of individual adar1000 handles.
        array_element_map: type=list[list[int]]
            Required list of lists with the map of where the array elements are
            located in the physical array. Each entry in the map represents a
            row of elements referenced by element number. For example, a map:

                | [[1, 5, 9, 13],
                | [2, 6, 10, 14],
                | [3, 7, 11, 15],
                | [4, 8, 12, 16]]

            represents an array of 16 elements (4 ADAR1000s) in a 4x4 array.
            If creating a single adar1000 instance, the elements should be 1-4 in
            whatever configuration the physical array is (1x4, 2x2, 4x1, etc.). If
            creating an adar1000_array instance, the array class will handle the
            instantiation of individual adar1000 handles.
        channel_element_map: type=list[int]
            Required list of integers relating the array element numbers to the
            channels of the ADAR1000 instance. Each number in the list is the
            element number in the larger array, in order of the ADAR1000's channels.
            For example, a list [10, 14, 13, 9] indicates that the ADAR1000's
            channels are the following elements in the full array:

                | Channel 1: Element # 10
                | Channel 2: Element # 14
                | Channel 3: Element # 13
                | Channel 4: Element # 9

            If creating a single adar1000 instance, the elements should be 1-4 in
            order of the ADAR1000's channels related to the array elements. If
            creating an adar1000_array instance, the array class will handle the
            instantiation of individual adar1000 handles.
    """

    _device_name = ""
    _BIAS_CODE_TO_VOLTAGE_SCALE = -0.018824

    class adar1000_channel:
        """Class for each channel of the ADAR1000. This class is not meant
        to be instantiated directly. adar1000 objects will create their
        own handles of this class, one for each channel

        parameters:
            adar1000_parent: type=adar1000
                Parent ADAR1000 instance
            adar_channel: type=int
                Channel number of the parent corresponding to this channel
            array_element: type=int
                Element number of the array corresponding to this channel
            row: int
                Row number in the array
            column: int
                Column number in the array
        """

        def __init__(self, adar_parent, adar_channel, array_element, row, column):
            self._adar1000_parent = adar_parent
            self._adar1000_channel = adar_channel
            self._array_element_number = array_element
            self._row = row
            self._column = column

            self._BIAS_CODE_TO_VOLTAGE_SCALE = adar1000._BIAS_CODE_TO_VOLTAGE_SCALE

        def __repr__(self):
            """ Representation of the ADAR1000 element class """
            return f"ADAR1000 array element #{self.array_element_number}"

        """ Channel Properties """

        @property
        def adar1000_channel(self):
            return self._adar1000_channel

        @property
        def adar1000_parent(self):
            return self._adar1000_parent

        @property
        def array_element_number(self):
            """ Element number in the array """
            return self._array_element_number

        @property
        def column(self):
            """ Element column number in the array """
            return self._column

        @property
        def _detector_enable(self):
            """ Get/Set the detector enable bit for the associated channel """
            return bool(
                self.adar1000_parent._get_iio_attr(
                    f"voltage{self.adar1000_channel}", "detector_en", True
                )
            )

        @_detector_enable.setter
        def _detector_enable(self, value):
            """ Get/Set Channel 1 detector enable bit """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "detector_en", True, int(value)
            )

        @property
        def detector_power(self):
            """ Get the detector power reading for the associated channel """

            self._detector_enable = True

            readback = self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "raw", True
            )

            self._detector_enable = False

            return readback

        @property
        def pa_bias_off(self):
            """ Get/Set PA_BIAS_OFF in voltage for the associated channel """
            dac_code = self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "pa_bias_off", True
            )
            return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

        @pa_bias_off.setter
        def pa_bias_off(self, value):
            """ Get/Set PA_BIAS_OFF in voltage for the associated channel """
            dac_code = int(value / self._BIAS_CODE_TO_VOLTAGE_SCALE)
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "pa_bias_off", True, dac_code
            )

        @property
        def pa_bias_on(self):
            """ Get/Set PA_BIAS_ON in voltage for the associated channel """
            dac_code = self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "pa_bias_on", True
            )
            return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

        @pa_bias_on.setter
        def pa_bias_on(self, value):
            """ Get/Set PA_BIAS_ON in voltage for the associated channel """
            dac_code = int(value / self._BIAS_CODE_TO_VOLTAGE_SCALE)
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "pa_bias_on", True, dac_code
            )

        @property
        def row(self):
            """ Element row number in the array """
            return self._row

        @property
        def rx_attenuator(self):
            """ Get/Set Rx Attenuator state for the associated channel """
            return bool(
                1
                - self.adar1000_parent._get_iio_attr(
                    f"voltage{self.adar1000_channel}", "attenuation", False
                )
            )

        @rx_attenuator.setter
        def rx_attenuator(self, value):
            """ Get/Set Rx Attenuator state for the associated channel """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "attenuation", False, 1 - int(value)
            )

        @property
        def rx_beam_state(self):
            """Get/Set the Channel Rx beam position used by RAM when
            all channels point to individual states. Valid states are 0-120."""
            return self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "beam_pos_load", False
            )

        @rx_beam_state.setter
        def rx_beam_state(self, value):
            """Get/Set the Channel Rx beam position used by RAM when
            all channels point to individual states. Valid states are 0-120."""
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "beam_pos_load", False, value
            )

        @property
        def rx_enable(self):
            """ Get/Set the Rx enable state for the associated channel """
            return bool(
                1
                - self.adar1000_parent._get_iio_attr(
                    f"voltage{self.adar1000_channel}", "powerdown", False
                )
            )

        @rx_enable.setter
        def rx_enable(self, value):
            """ Get/Set the Rx enable state for the associated channel """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "powerdown", False, 1 - int(value)
            )

        @property
        def rx_gain(self):
            """ Get/Set the Rx Gain for the associated channel """
            return self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "hardwaregain", False
            )

        @rx_gain.setter
        def rx_gain(self, value):
            """ Get/Set the Rx Gain for the associated channel """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "hardwaregain", False, value
            )

        @property
        def rx_phase(self):
            """ Get/Set the Rx Phase for the associated channel """
            return self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "phase", False
            )

        @rx_phase.setter
        def rx_phase(self, value):
            """ Get/Set the Rx Phase for the associated channel """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "phase", False, value
            )

        @property
        def tx_attenuator(self):
            """ Get/Set the Tx Attenuator state for the associated channel """
            return bool(
                1
                - self.adar1000_parent._get_iio_attr(
                    f"voltage{self.adar1000_channel}", "attenuation", True
                )
            )

        @tx_attenuator.setter
        def tx_attenuator(self, value):
            """ Get/Set the Tx Attenuator state for the associated channel """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "attenuation", True, 1 - int(value)
            )

        @property
        def tx_beam_state(self):
            """Get/Set the Channel Tx beam position used by RAM when
            all channels point to individual states. Valid states are 0-120."""
            return self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "beam_pos_load", True
            )

        @tx_beam_state.setter
        def tx_beam_state(self, value):
            """Get/Set the Channel Tx beam position used by RAM when
            all channels point to individual states. Valid states are 0-120."""
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "beam_pos_load", True, value
            )

        @property
        def tx_enable(self):
            """ Get/Set the Tx enable state for the associated channel """
            return bool(
                1
                - self.adar1000_parent._get_iio_attr(
                    f"voltage{self.adar1000_channel}", "powerdown", True
                )
            )

        @tx_enable.setter
        def tx_enable(self, value):
            """ Get/Set the Tx enable state for the associated channel """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "powerdown", True, 1 - int(value)
            )

        @property
        def tx_gain(self):
            """ Get/Set the Tx Gain for the associated channel """
            return self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "hardwaregain", True
            )

        @tx_gain.setter
        def tx_gain(self, value):
            """ Get/Set the Tx Gain for the associated channel """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "hardwaregain", True, value
            )

        @property
        def tx_phase(self):
            """ Get/Set the Tx Phase for the associated channel """
            return self.adar1000_parent._get_iio_attr(
                f"voltage{self.adar1000_channel}", "phase", True
            )

        @tx_phase.setter
        def tx_phase(self, value):
            """ Get/Set the Tx Phase for the associated channel """
            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "phase", True, value
            )

        """ Public Methods """

        def save_rx_beam(self, state, attenuator, gain, phase):
            """Save a beam to an Rx memory position

            parameters:
                state: int
                    State number to save. Valid options are 0 to 120
                attenuator: bool
                    Attenuator state for the beam position. True means the attenuator is in place.
                gain: int
                    Gain value for the beam position. Valid settings are 0 to 127.
                phase: float
                    Phase value for the beam position.
            """
            save_string = f"{state}, {1 - int(attenuator)}, {gain}, {phase}"

            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "beam_pos_save", False, save_string
            )

        def save_tx_beam(self, state, attenuator, gain, phase):
            """Save a beam to a Tx memory position

            parameters:
                state: int
                    State number to save. Valid options are 0 to 120
                attenuator: bool
                    Attenuator state for the beam position. True means the attenuator is in place.
                gain: int
                    Gain value for the beam position. Valid settings are 0 to 127.
                phase: float
                    Phase value for the beam position.
            """
            save_string = f"{state}, {1 - int(attenuator)}, {gain}, {phase}"

            self.adar1000_parent._set_iio_attr(
                f"voltage{self.adar1000_channel}", "beam_pos_save", True, save_string
            )

    def __init__(
        self,
        uri="",
        context=None,
        chip_id="csb1_chip1",
        device_number=1,
        array_element_map=None,
        channel_element_map=None,
    ):

        # Use the given context if possible, otherwise lookup the context
        if context is None:
            context_manager.__init__(self, uri, self._device_name)
        else:
            self._ctx = context

        self._ctrl = None
        self._chip_id = chip_id
        self._array_device_number = device_number

        # Check for the presence of array and channel element maps
        if array_element_map is None:
            raise Exception('"array_element_map" argument must be provided!')
        if channel_element_map is None:
            raise Exception('"channel_element_map" argument must be provided!')

        # Look for the matching device in the context
        for dev in self._ctx.devices:
            if (
                "label" in dev.attrs
                and dev.attrs["label"].value.lower() == chip_id.lower()
            ) or (
                hasattr(dev, "label")
                and dev.label
                and dev.label.lower() == chip_id.lower()
            ):
                self._ctrl = dev
                break

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception(f"Device not found for {chip_id}")

        # Determine the row and column numbers for the elements using the maps given
        element_numbers = channel_element_map
        element_rows_cols = {}
        for element_number in element_numbers:
            for r, row in enumerate(array_element_map):
                for c, map_value in enumerate(row):
                    if map_value == element_number:
                        element_rows_cols[element_number] = (r, c)

        # Create the channel instances
        self._channels = []
        for i in range(4):
            element_number = element_numbers[i]
            row, column = element_rows_cols[element_number]
            self._channels.append(
                self.adar1000_channel(self, i, element_number, row, column)
            )

    def __repr__(self):
        """ Representation of the ADAR1000 class """
        return (
            f"ADAR1000 #{self.array_device_number} controlling array elements:\n"
            f"\t{', '.join([str(channel.array_element_number) for channel in self.channels])}"
        )

    """ Device Properties """

    @property
    def array_device_number(self):
        """ Device number in the array """
        return self._array_device_number

    @property
    def beam_mem_enable(self):
        """ Get/Set enable bit for RAM control vs. SPI control of the beam state """
        return bool(self._get_iio_dev_attr("beam_mem_enable", self._ctrl))

    @beam_mem_enable.setter
    def beam_mem_enable(self, value):
        """ Get/Set enable bit for RAM control vs. SPI control of the beam state """
        self._set_iio_dev_attr_str("beam_mem_enable", int(value), self._ctrl)

    @property
    def bias_dac_enable(self):
        """ Get/Set enable for bias DACs """
        return bool(self._get_iio_dev_attr("bias_enable", self._ctrl))

    @bias_dac_enable.setter
    def bias_dac_enable(self, value):
        """ Get/Set enable for bias DACs """
        self._set_iio_dev_attr_str("bias_enable", int(value), self._ctrl)

    @property
    def bias_dac_mode(self):
        """
        Get/Set BIAS_CTRL bit (Register 0x30[6]) which controls whether the bias DACs stay at "ON" value,
        or toggle with respect to T/R state.
        """
        value = bool(self._get_iio_dev_attr("bias_ctrl", self._ctrl))
        if value:
            return "toggle"
        else:
            return "on"

    @bias_dac_mode.setter
    def bias_dac_mode(self, value):
        """
        Get/Set BIAS_CTRL bit (Register 0x30[6]) which controls whether the bias DACs stay at "ON" value,
        or toggle with respect to T/R state.
        """
        if value.lower() == "toggle":
            set_value = 1
        elif value.lower() == "on":
            set_value = 0
        else:
            raise ValueError('bias_dac_mode should be "toggle" or "on"')

        self._set_iio_dev_attr_str("bias_ctrl", set_value, self._ctrl)

    @property
    def bias_mem_enable(self):
        """ Get/Set enable bit for RAM control vs. SPI control of the bias state """
        return bool(self._get_iio_dev_attr("bias_mem_enable", self._ctrl))

    @bias_mem_enable.setter
    def bias_mem_enable(self, value):
        """ Get/Set enable bit for RAM control vs. SPI control of the bias state """
        self._set_iio_dev_attr_str("bias_mem_enable", int(value), self._ctrl)

    @property
    def channel1(self):
        """ Handle for the ADAR1000's channel 1 object """
        return self._channels[0]

    @property
    def channel2(self):
        """ Handle for the ADAR1000's channel 2 object """
        return self._channels[1]

    @property
    def channel3(self):
        """ Handle for the ADAR1000's channel 3 object """
        return self._channels[2]

    @property
    def channel4(self):
        """ Handle for the ADAR1000's channel 4 object """
        return self._channels[3]

    @property
    def channels(self):
        """ List of the ADAR1000's channels, in order from 1 to 4 """
        return self._channels

    @property
    def chip_id(self):
        """
        Chip ID including CSB and hardware address. Of the form "csbX_chipX" where csbX indicates the CSB
        line for the IC and chipX indicating the hardware address of the chip, 1-4.
        """
        return self._chip_id

    @property
    def common_mem_enable(self):
        """
        Get/Set the CHX_RAM_BYPASS bits to use either a common beam state for all channels set by registers 0x39
        and 0x3A, or individual beam states set by registers 0x3D to 0x44.
        """
        return bool(self._get_iio_dev_attr("common_mem_enable", self._ctrl))

    @common_mem_enable.setter
    def common_mem_enable(self, value):
        """
        Get/Set the CHX_RAM_BYPASS bits to use either a common beam state for all channels set by registers 0x39
        and 0x3A, or individual beam states set by registers 0x3D to 0x44.
        """
        self._set_iio_dev_attr_str("bias_enable", int(value), self._ctrl)

    @property
    def common_rx_beam_state(self):
        """Get/Set the Rx beam position used by RAM when all
        channels point to a common state. Valid states are 0-120."""
        return self._get_iio_dev_attr_str("static_rx_beam_pos_load", self._ctrl)

    @common_rx_beam_state.setter
    def common_rx_beam_state(self, value):
        """Get/Set the Rx beam position used by RAM when all
        channels point to a common state. Valid states are 0-120."""
        self._set_iio_dev_attr_str("static_rx_beam_pos_load", value, self._ctrl)

    @property
    def common_tx_beam_state(self):
        """Get/Set the Tx beam position used by RAM when all
        channels point to a common state. Valid states are 0-120."""
        return self._get_iio_dev_attr_str("static_tx_beam_pos_load", self._ctrl)

    @common_tx_beam_state.setter
    def common_tx_beam_state(self, value):
        """Get/Set the Tx beam position used by RAM when all
        channels point to a common state. Valid states are 0-120."""
        self._set_iio_dev_attr_str("static_tx_beam_pos_load", value, self._ctrl)

    @property
    def external_tr_pin(self):
        """ Get/Set which external T/R switch driver is used ("positive" = TR_SW_POS, "negative" = TR_SW_NEG) """
        value = bool(self._get_iio_dev_attr("sw_drv_tr_mode_sel", self._ctrl))
        if value:
            return "negative"
        else:
            return "positive"

    @external_tr_pin.setter
    def external_tr_pin(self, value):
        """ Get/Set which external T/R switch driver is used ("positive" = TR_SW_POS, "negative" = TR_SW_NEG) """
        if value.lower() == "negative":
            set_value = 1
        elif value.lower() == "positive":
            set_value = 0
        else:
            raise ValueError('external_tr_pin should be "positive" or "negative"')

        self._set_iio_dev_attr_str("sw_drv_tr_mode_sel", set_value, self._ctrl)

    @property
    def external_tr_polarity(self):
        """
        Get/Set polarity of the T/R switch driver compared to the T/R state of the ADAR1000.
        True outputs 0V in Rx mode, False outputs either 3.3V or -5V, depending on which T/R switch driver is enabled.
        """
        return bool(self._get_iio_dev_attr("sw_drv_tr_state", self._ctrl))

    @external_tr_polarity.setter
    def external_tr_polarity(self, value):
        """
        Get/Set polarity of the T/R switch driver compared to the T/R state of the ADAR1000.
        True outputs 0V in Rx mode, False outputs either 3.3V or -5V, depending on which T/R switch driver is enabled.
        """
        self._set_iio_dev_attr_str("sw_drv_tr_state", int(value), self._ctrl)

    @property
    def lna_bias_off(self):
        """ Get/Set LNA_BIAS_OFF in voltage """
        dac_code = self._get_iio_dev_attr("lna_bias_off", self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @lna_bias_off.setter
    def lna_bias_off(self, value):
        """ Get/Set LNA_BIAS_OFF in voltage """
        dac_code = int(value / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        self._set_iio_dev_attr_str("lna_bias_off", dac_code, self._ctrl)

    @property
    def lna_bias_on(self):
        """ Get/Set LNA_BIAS_ON in voltage """
        dac_code = self._get_iio_dev_attr("lna_bias_on", self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @lna_bias_on.setter
    def lna_bias_on(self, value):
        """ Get/Set LNA_BIAS_ON in voltage """
        dac_code = int(value / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        self._set_iio_dev_attr_str("lna_bias_on", dac_code, self._ctrl)

    @property
    def lna_bias_out_enable(self):
        """ Get/Set enable for LNA bias DAC output. Disable to allow for always-on self-biased LNAs """
        return bool(self._get_iio_dev_attr("lna_bias_out_enable", self._ctrl))

    @lna_bias_out_enable.setter
    def lna_bias_out_enable(self, value):
        """ Get/Set enable for LNA bias DAC output. Disable to allow for always-on self-biased LNAs """
        self._set_iio_dev_attr_str("lna_bias_out_enable", int(value), self._ctrl)

    @property
    def mode(self):
        """ Get/Set the mode of operation for the device. Valid options are "rx", "tx", and "disabled" """

        # There are different paths for spi vs. external T/R control

        if self.tr_source == "external":
            return self._tr

        else:
            # Check for Rx mode
            if self._rx_enable and not self._tx_enable:
                if self._tr == "rx":
                    return "rx"
                else:
                    return "disabled"

            # Check for Tx mode
            elif self._tx_enable and not self._rx_enable:
                if self._tr == "tx":
                    return "tx"
                else:
                    return "disabled"

            # Check mode if both device enables are high
            elif self._rx_enable and self._tx_enable:
                return self._tr

            # Device is disabled
            else:
                return "disabled"

    @mode.setter
    def mode(self, value):
        """ Get/Set the mode of operation for the device. Valid options are "rx", "tx", and "disabled" """
        mode = value.strip().lower()
        if mode not in ("rx", "tx", "disabled"):
            raise ValueError(
                'Mode of operation must be either "rx", "tx", or "disabled"'
            )

        if mode == "disabled":
            self.tr_source = "spi"
            self._rx_enable = False
            self._tx_enable = False

        else:
            # Set the T/R state to the correct mode
            self._tr = mode

            if mode == "rx":
                self._rx_enable = True
                self._tx_enable = False

            # Tx mode
            else:
                self._rx_enable = False
                if self.tr_source == "spi":
                    self._tx_enable = True

    @property
    def pol_state(self):
        """ Get/Set polarity switch state. True outputs -5V, False outputs 0V """
        return bool(self._get_iio_dev_attr("pol", self._ctrl))

    @pol_state.setter
    def pol_state(self, value):
        """ Get/Set polarity switch state. True outputs -5V, False outputs 0V """
        self._set_iio_dev_attr_str("pol", int(value), self._ctrl)

    @property
    def pol_switch_enable(self):
        """ Get/Set polarity switch driver enable state """
        return bool(self._get_iio_dev_attr("sw_drv_en_pol", self._ctrl))

    @pol_switch_enable.setter
    def pol_switch_enable(self, value):
        """ Get/Set polarity switch driver enable state """
        self._set_iio_dev_attr_str("sw_drv_en_pol", int(value), self._ctrl)

    @property
    def rx_bias_state(self):
        """ Get/Set the Rx bias memory position when loading from RAM. Valid states are 1-7. """
        return self._get_iio_attr("voltage0", "bias_set_load", False, self._ctrl)

    @rx_bias_state.setter
    def rx_bias_state(self, value):
        """ Get/Set the Rx bias memory position when loading from RAM. Valid states are 1-7. """
        self._set_iio_attr("voltage0", "bias_set_load", False, value, self._ctrl)

    @property
    def _rx_enable(self):
        """ Get/Set enable for entire Rx chain. Should not be used directly, the mode property controls this. """
        return bool(self._get_iio_dev_attr("rx_en", self._ctrl))

    @_rx_enable.setter
    def _rx_enable(self, value):
        """ Get/Set enable for entire Rx chain. Should not be used directly, the mode property controls this. """
        self._set_iio_dev_attr_str("rx_en", int(value), self._ctrl)

    @property
    def rx_lna_bias_current(self):
        """ Get/Set Rx LNA bias current setting """
        return self._get_iio_dev_attr("bias_current_rx_lna", self._ctrl)

    @rx_lna_bias_current.setter
    def rx_lna_bias_current(self, value):
        """ Get/Set Rx LNA bias current setting """
        self._set_iio_dev_attr_str("bias_current_rx_lna", value, self._ctrl)

    @property
    def rx_lna_enable(self):
        """ Get/Set Rx LNA enable status """
        return bool(self._get_iio_dev_attr("rx_lna_enable", self._ctrl))

    @rx_lna_enable.setter
    def rx_lna_enable(self, value):
        """ Get/Set Rx LNA enable status """
        self._set_iio_dev_attr_str("rx_lna_enable", int(value), self._ctrl)

    @property
    def rx_sequencer_start(self):
        """ Get/Set the Rx Sequencer's starting position """
        return self._get_iio_attr("voltage0", "sequence_start", False)

    @rx_sequencer_start.setter
    def rx_sequencer_start(self, value):
        """ Get/Set the Rx Sequencer's starting position """
        self._set_iio_attr("voltage0", "sequence_start", False, value)

    @property
    def rx_sequencer_stop(self):
        """ Get/Set the Rx Sequencer's ending position """
        return self._get_iio_attr("voltage0", "sequence_end", False)

    @rx_sequencer_stop.setter
    def rx_sequencer_stop(self, value):
        """ Get/Set the Rx Sequencer's ending position """
        self._set_iio_attr("voltage0", "sequence_end", False, value)

    @property
    def rx_to_tx_delay_1(self):
        """ Get/Set Rx to Tx Delay 1 """
        return self._get_iio_dev_attr("rx_to_tx_delay_1", self._ctrl)

    @rx_to_tx_delay_1.setter
    def rx_to_tx_delay_1(self, value):
        """ Get/Set Rx to Tx Delay 1 """
        self._set_iio_dev_attr_str("rx_to_tx_delay_1", int(value), self._ctrl)

    @property
    def rx_to_tx_delay_2(self):
        """ Get/Set Rx to Tx Delay 2 """
        return self._get_iio_dev_attr("rx_to_tx_delay_2", self._ctrl)

    @rx_to_tx_delay_2.setter
    def rx_to_tx_delay_2(self, value):
        """ Get/Set Rx to Tx Delay 2 """
        self._set_iio_dev_attr_str("rx_to_tx_delay_2", int(value), self._ctrl)

    @property
    def rx_vga_enable(self):
        """ Get/Set Rx VGA enable status """
        return bool(self._get_iio_dev_attr("rx_vga_enable", self._ctrl))

    @rx_vga_enable.setter
    def rx_vga_enable(self, value):
        """ Get/Set Rx VGA enable status """
        self._set_iio_dev_attr_str("rx_vga_enable", int(value), self._ctrl)

    @property
    def rx_vga_vm_bias_current(self):
        """ Get/Set Rx VGA/Vector Modulator bias current setting """
        return self._get_iio_dev_attr("bias_current_rx", self._ctrl)

    @rx_vga_vm_bias_current.setter
    def rx_vga_vm_bias_current(self, value):
        """ Get/Set Rx VGA/Vector Modulator bias current setting """
        self._set_iio_dev_attr_str("bias_current_rx", value, self._ctrl)

    @property
    def rx_vm_enable(self):
        """ Get/Set Rx Vector Modulator enable status """
        return bool(self._get_iio_dev_attr("rx_vm_enable", self._ctrl))

    @rx_vm_enable.setter
    def rx_vm_enable(self, value):
        """ Get/Set Rx Vector Modulator enable status """
        self._set_iio_dev_attr_str("rx_vm_enable", int(value), self._ctrl)

    @property
    def sequencer_enable(self):
        """ Get/Set sequencer enable status """
        return bool(self._get_iio_dev_attr("sequencer_enable", self._ctrl))

    @sequencer_enable.setter
    def sequencer_enable(self, value):
        """ Get/Set sequencer enable status """
        self._set_iio_dev_attr_str("sequencer_enable", int(value), self._ctrl)

    @property
    def temperature(self):
        """ Get the temperature reading from the device """
        return self._get_iio_attr("temp0", "raw", False)

    @property
    def _tr(self):
        """Get/Set the status of the T/R input to the device. Valid options are "tx" or "rx". This property must be
        overwritten to use the external T/R input, as GPIO control is not included in this wrapper. This property
        should not be used directly, as it is controlled by the "mode" property.
        """

        if self.tr_source == "external":
            raise NotImplementedError(
                "External T/R control is not implemented in this wrapper. Overwrite this "
                "property in a subclass to allow for GPIO control of the ADAR1000's T/R input pin"
            )

        else:
            return self.tr_spi

    @_tr.setter
    def _tr(self, value):
        """Get/Set the status of the T/R input to the device. Valid options are "tx" or "rx". This property must be
        overwritten to use the external T/R input, as GPIO control is not included in this wrapper. This property
        should not be used directly, as it is controlled by the "mode" property.
        """

        if self.tr_source == "external":
            raise NotImplementedError(
                "External T/R control is not implemented in this wrapper. Overwrite this "
                "property in a subclass to allow for GPIO control of the ADAR1000's T/R input pin"
            )

        else:
            self.tr_spi = value

    @property
    def tr_source(self):
        """ Get/Set TR source for the chip. Valid options are "external" or "spi" """
        value = bool(self._get_iio_dev_attr("tr_source", self._ctrl))
        if value:
            return "external"
        else:
            return "spi"

    @tr_source.setter
    def tr_source(self, value):
        """ Get/Set TR source for the chip. Valid options are "external" or "spi" """
        if value.lower() == "external":
            set_value = 1
        elif value.lower() == "spi":
            set_value = 0
        else:
            raise ValueError('tr_source should be "external" or "spi"')

        self._set_iio_dev_attr_str("tr_source", set_value, self._ctrl)

    @property
    def tr_spi(self):
        """ Get/Set T/R state using the SPI bit. Valid options are "tx" or "rx" """
        value = bool(self._get_iio_dev_attr("tr_spi", self._ctrl))
        if value:
            return "tx"
        else:
            return "rx"

    @tr_spi.setter
    def tr_spi(self, value):
        """ Get/Set T/R state using the SPI bit. Valid options are "tx" or "rx" """
        if value.lower() == "tx":
            set_value = 1
        elif value.lower() == "rx":
            set_value = 0
        else:
            raise ValueError('tr_spi should be "tx" or "rx"')

        self._set_iio_dev_attr_str("tr_spi", set_value, self._ctrl)

    @property
    def tr_switch_enable(self):
        """ Get/Set T/R switch driver enable state """
        return bool(self._get_iio_dev_attr("sw_drv_en_tr", self._ctrl))

    @tr_switch_enable.setter
    def tr_switch_enable(self, value):
        """ Get/Set T/R switch driver enable state """
        self._set_iio_dev_attr_str("sw_drv_en_tr", int(value), self._ctrl)

    @property
    def tx_bias_state(self):
        """ Get/Set the Tx bias memory position when loading from RAM. Valid states are 1-7. """
        return self._get_iio_attr("voltage0", "bias_set_load", True, self._ctrl)

    @tx_bias_state.setter
    def tx_bias_state(self, value):
        """ Get/Set the Tx bias memory position when loading from RAM. Valid states are 1-7. """
        self._set_iio_attr("voltage0", "bias_set_load", True, value, self._ctrl)

    @property
    def _tx_enable(self):
        """ Get/Set enable for entire Tx chain. Should not be used directly, the mode property controls this. """
        return bool(self._get_iio_dev_attr("tx_en", self._ctrl))

    @_tx_enable.setter
    def _tx_enable(self, value):
        """ Get/Set enable for entire Tx chain. Should not be used directly, the mode property controls this. """
        self._set_iio_dev_attr_str("tx_en", int(value), self._ctrl)

    @property
    def tx_pa_bias_current(self):
        """ Get/Set Tx PA bias current setting """
        return self._get_iio_dev_attr("bias_current_tx_drv", self._ctrl)

    @tx_pa_bias_current.setter
    def tx_pa_bias_current(self, value):
        """ Get/Set Tx PA bias current setting """
        self._set_iio_dev_attr_str("bias_current_tx_drv", value, self._ctrl)

    @property
    def tx_pa_enable(self):
        """ Get/Set Tx PA enable status """
        return bool(self._get_iio_dev_attr("tx_drv_enable", self._ctrl))

    @tx_pa_enable.setter
    def tx_pa_enable(self, value):
        """ Get/Set Tx PA enable status """
        self._set_iio_dev_attr_str("tx_drv_enable", int(value), self._ctrl)

    @property
    def tx_sequencer_start(self):
        """ Get/Set the Tx Sequencer's starting position """
        return self._get_iio_attr("voltage0", "sequence_start", True)

    @tx_sequencer_start.setter
    def tx_sequencer_start(self, value):
        """ Get/Set the Tx Sequencer's starting position """
        self._set_iio_attr("voltage0", "sequence_start", True, value)

    @property
    def tx_sequencer_stop(self):
        """ Get/Set the Tx Sequencer's ending position """
        return self._get_iio_attr("voltage0", "sequence_end", True)

    @tx_sequencer_stop.setter
    def tx_sequencer_stop(self, value):
        """ Get/Set the Tx Sequencer's ending position """
        self._set_iio_attr("voltage0", "sequence_end", True, value)

    @property
    def tx_to_rx_delay_1(self):
        """ Get/Set Tx to Rx Delay 1 """
        return self._get_iio_dev_attr("tx_to_rx_delay_1", self._ctrl)

    @tx_to_rx_delay_1.setter
    def tx_to_rx_delay_1(self, value):
        """ Get/Set Tx to Rx Delay 1 """
        self._set_iio_dev_attr_str("tx_to_rx_delay_1", int(value), self._ctrl)

    @property
    def tx_to_rx_delay_2(self):
        """ Get/Set Tx to Rx Delay 2 """
        return self._get_iio_dev_attr("tx_to_rx_delay_2", self._ctrl)

    @tx_to_rx_delay_2.setter
    def tx_to_rx_delay_2(self, value):
        """ Get/Set Tx to Rx Delay 2 """
        self._set_iio_dev_attr_str("tx_to_rx_delay_2", int(value), self._ctrl)

    @property
    def tx_vga_enable(self):
        """ Get/Set Tx VGA enable status """
        return bool(self._get_iio_dev_attr("tx_vga_enable", self._ctrl))

    @tx_vga_enable.setter
    def tx_vga_enable(self, value):
        """ Get/Set Tx VGA enable status """
        self._set_iio_dev_attr_str("tx_vga_enable", int(value), self._ctrl)

    @property
    def tx_vga_vm_bias_current(self):
        """ Get/Set Tx VGA/Vector Modulator bias current setting """
        return self._get_iio_dev_attr("bias_current_tx", self._ctrl)

    @tx_vga_vm_bias_current.setter
    def tx_vga_vm_bias_current(self, value):
        """ Get/Set Tx VGA/Vector Modulator bias current setting """
        self._set_iio_dev_attr_str("bias_current_tx", value, self._ctrl)

    @property
    def tx_vm_enable(self):
        """ Get/Set Tx Vector Modulator enable status """
        return bool(self._get_iio_dev_attr("tx_vm_enable", self._ctrl))

    @tx_vm_enable.setter
    def tx_vm_enable(self, value):
        """ Get/Set Tx Vector Modulator enable status """
        self._set_iio_dev_attr_str("tx_vm_enable", int(value), self._ctrl)

    """ Public Methods """

    def generate_clocks(self):
        """ Generate CLK cycles before pulsing RX_LOAD or TX_LOAD """
        self._set_iio_dev_attr_str("gen_clk_cycles", "", self._ctrl)

    def initialize(self, pa_off=-2.5, pa_on=-2.5, lna_off=-2, lna_on=-2):
        """Suggested initialization routine after powerup

        parameters:
            pa_off: float
                Voltage to set the PA_BIAS_OFF values to during initialization
            pa_on: float
                Voltage to set the PA_BIAS_ON values to during initialization
            lna_off: float
                Voltage to set the LNA_BIAS_OFF values to during initialization
            lna_on: float
                Voltage to set the LNA_BIAS_ON values to during initialization
        """
        # Put the part in a known state
        self.reset()

        # Set the bias currents to nominal
        self.rx_lna_bias_current = 0x08
        self.rx_vga_vm_bias_current = 0x55
        self.tx_vga_vm_bias_current = 0x2D
        self.tx_pa_bias_current = 0x06

        # Disable RAM control
        self.beam_mem_enable = False
        self.bias_mem_enable = False
        self.common_mem_enable = False

        # Enable all internal amplifiers
        self.rx_vga_enable = True
        self.rx_vm_enable = True
        self.rx_lna_enable = True
        self.tx_vga_enable = True
        self.tx_vm_enable = True
        self.tx_pa_enable = True

        # Disable Tx/Rx paths for the device
        self.mode = "disabled"

        # Enable the PA/LNA bias DACs
        self.lna_bias_out_enable = True
        self.bias_dac_enable = True
        self.bias_dac_mode = "toggle"

        # Configure the external switch control
        self.external_tr_polarity = True
        self.tr_switch_enable = True

        # Set the default LNA bias
        self.lna_bias_off = lna_off
        self.lna_bias_on = lna_on

        # Settings for each channel
        for channel in self.channels:
            # Default channel enable
            channel.rx_enable = False
            channel.tx_enable = False

            # Default PA bias
            channel.pa_bias_off = pa_off
            channel.pa_bias_on = pa_on

            # Default attenuator, gain, and phase
            channel.rx_attenuator = False
            channel.rx_gain = 0x7F
            channel.rx_phase = 0
            channel.tx_attenuator = False
            channel.tx_gain = 0x7F
            channel.tx_phase = 0

        # Latch in the new settings
        self.latch_rx_settings()
        self.latch_tx_settings()

    def latch_rx_settings(self):
        """ Latch in new Gain/Phase settings for the Rx """
        self._set_iio_dev_attr_str("rx_load_spi", 1, self._ctrl)

    def latch_tx_settings(self):
        """ Latch in new Gain/Phase settings for the Tx """
        self._set_iio_dev_attr_str("tx_load_spi", 1, self._ctrl)

    def reset(self):
        """ Reset ADAR1000 to default settings """
        self._set_iio_dev_attr("reset", 1, self._ctrl)

    def save_rx_bias(
        self,
        state,
        lna_bias_off,
        lna_bias_on,
        rx_vga_vm_bias_current,
        rx_lna_bias_current,
    ):
        """Save a bias setting to an Rx memory position

        parameters:
            state: int
                State number to save. Valid options are 1 to 7
            lna_bias_off: float
                LNA_BIAS_OFF voltage
            lna_bias_on: float
                LNA_BIAS_ON voltage
            rx_vga_vm_bias_current: int
                Bias current setting for the Rx VGA and Vector Modulator
            rx_lna_bias_current: int
                Bias current setting for the Rx LNA
        """

        # Convert the LNA bias settings to dac codes:
        lna_off_dac_code = int(lna_bias_off / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        lna_on_dac_code = int(lna_bias_on / self._BIAS_CODE_TO_VOLTAGE_SCALE)

        save_string = f"{state}, {lna_off_dac_code}, {lna_on_dac_code}, {rx_vga_vm_bias_current}, {rx_lna_bias_current}"

        self._set_iio_attr("voltage0", "bias_set_save", False, save_string, self._ctrl)

    def save_tx_bias(
        self,
        state,
        pa1_bias_off,
        pa2_bias_off,
        pa3_bias_off,
        pa4_bias_off,
        pa1_bias_on,
        pa2_bias_on,
        pa3_bias_on,
        pa4_bias_on,
        tx_vga_vm_bias_current,
        tx_pa_bias_current,
    ):
        """Save a bias setting to a Tx memory position

        parameters:
            state: int
                State number to save. Valid options are 1 to 7
            pa1_bias_off: float
                PA1_BIAS_OFF voltage
            pa2_bias_off: float
                PA2_BIAS_OFF voltage
            pa3_bias_off: float
                PA3_BIAS_OFF voltage
            pa4_bias_off: float
                PA4_BIAS_OFF voltage
            pa1_bias_on: float
                PA1_BIAS_ON voltage
            pa2_bias_on: float
                PA2_BIAS_ON voltage
            pa3_bias_on: float
                PA3_BIAS_ON voltage
            pa4_bias_on: float
                PA4_BIAS_ON voltage
            tx_vga_vm_bias_current: int
                Bias current setting for the Tx VGA and Vector Modulator
            tx_lna_bias_current: int
                Bias current setting for the Tx PA
        """

        # Convert the PA bias settings to dac codes:
        pa1_off_dac_code = int(pa1_bias_off / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        pa2_off_dac_code = int(pa2_bias_off / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        pa3_off_dac_code = int(pa3_bias_off / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        pa4_off_dac_code = int(pa4_bias_off / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        pa1_on_dac_code = int(pa1_bias_on / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        pa2_on_dac_code = int(pa2_bias_on / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        pa3_on_dac_code = int(pa3_bias_on / self._BIAS_CODE_TO_VOLTAGE_SCALE)
        pa4_on_dac_code = int(pa4_bias_on / self._BIAS_CODE_TO_VOLTAGE_SCALE)

        save_string = (
            f"{state}, {pa1_off_dac_code}, {pa2_off_dac_code}, {pa3_off_dac_code}, {pa4_off_dac_code}, "
            f"{pa1_on_dac_code}, {pa2_on_dac_code}, {pa3_on_dac_code}, {pa4_on_dac_code}, {tx_vga_vm_bias_current}, "
            f"{tx_pa_bias_current}"
        )

        self._set_iio_attr("voltage0", "bias_set_save", True, save_string, self._ctrl)


class adar1000_array(context_manager):
    """ADAR1000 Beamformer Array

    parameters:
        uri: type=string
            URI of IIO context with ADAR1000 array
        chip_ids: type=list[string]
            List of strings identifying desired chip select and hardware ID
            for the ADAR1000. These strings are the labels coinciding with
            each chip select and hardware address and are typically in the
            form csbX_chipX. The csb line can be any number depending on how
            many are used in the system. The chip number will typically be
            1-4 because each CSB line can control up to four ADAR1000s. Note
            that the order of the devices listed will correspond to the
            device numbers in the array map directly.
        device_map: type=list[list[int]]
            List with the map of where the ADAR1000s are in the array. Each
            entry in the map represents a row of ADAR1000s referenced by
            device number. For example, a map:

                | [[1, 3, 5, 7],
                | [2, 4, 6, 8]]

            represents an array of 8 ADAR1000s 4 wide and 2 tall.
        element_map: type=list[list[int]]
            List of lists with the map of where the array elements are in the
            physical array. Each entry in the map represents a row of array
            channels referenced by element number. For example, a map:

                | [[1, 5, 9, 13],
                | [2, 6, 10, 14],
                | [3, 7, 11, 15],
                | [4, 8, 12, 16]]

            represents an array of 16 elements (4 ADAR1000s) in a square array.
        device_element_map: type=dict[int, list[int]]
            Dictionary with the map of ADAR1000 to array element references. Each
            key in the map is a device number. The corresponding list of integers
            represents the array element numbers connected to that ADAR1000, in
            order of the ADAR1000's channels. For example, an entry of
            {3: [10, 14, 13, 9]} connects ADAR1000 #3 to array elements 10, 14, 13,
            and 9. Element #10 is on the ADAR1000's channel 1 while element #13 is
            on the ADAR1000's channel 3.
    """

    _device_name = ""

    def __init__(
        self,
        uri="",
        chip_ids=None,
        device_map=None,
        element_map=None,
        device_element_map=None,
    ):
        # Check that the number of chips matches for all the inputs
        chip_ids_len = len(chip_ids)
        adar1000_map_len = len([num for row in device_map for num in row])
        element_map_len = len([num for row in element_map for num in row]) / 4
        device_element_map_len = len(device_element_map)
        if not (
            chip_ids_len
            == adar1000_map_len
            == element_map_len
            == device_element_map_len
        ):
            raise ValueError("The number of chips must match for all the inputs")

        # Get the context
        context_manager.__init__(self, uri, self._device_name)

        # Initialize the devices dictionary
        self._devices = {}

        # Get an ADAR1000 handle for each chip ID using the context already found
        for i, chip_id in enumerate(chip_ids):
            device_number = i + 1
            self._devices[chip_id] = adar1000(
                uri,
                self._ctx,
                chip_id,
                device_number,
                element_map,
                device_element_map[device_number],
            )

        if len(self.devices) != len(chip_ids):
            raise Exception(
                f"Couldn't find all devices in the array {', '.join(chip_ids)}"
            )

        # Initialize some class fields
        self._chip_ids = chip_ids
        self._device_map = device_map
        self._element_map = element_map
        self._element_spacing = 0.015
        self._frequency = 10e9
        self._rx_azimuth = 0
        self._rx_azimuth_phi = 0
        self._rx_elevation = 0
        self._rx_elevation_phi = 0
        self._tx_azimuth = 0
        self._tx_azimuth_phi = 0
        self._tx_elevation = 0
        self._tx_elevation_phi = 0

    def __repr__(self):
        """ Representation of the ADAR1000 array class """
        return f"ADAR1000 array containing {len(self.devices)} ADAR1000 instances:\n\t{', '.join(self._chip_ids)}"

    """ Array Properties """

    @property
    def all_rx_attenuators(self):
        """Get/Set all Rx Attenuator settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        attenuator_map = []
        for r, row in enumerate(self.element_map):
            attenuator_map.append([])
            for element in row:
                attenuator_map[r].append(self.elements[element].rx_attenuator)

        return attenuator_map

    @all_rx_attenuators.setter
    def all_rx_attenuators(self, value):
        """Get/Set all Rx Attenuator settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        for r, row in enumerate(self.element_map):
            for e, element in enumerate(row):
                self.elements[element].rx_attenuator = value[r][e]

    @property
    def all_rx_gains(self):
        """Get/Set all Rx Gain settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        gain_map = []
        for r, row in enumerate(self.element_map):
            gain_map.append([])
            for element in row:
                gain_map[r].append(self.elements[element].rx_gain)

        return gain_map

    @all_rx_gains.setter
    def all_rx_gains(self, value):
        """Get/Set all Rx Gain settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        for r, row in enumerate(self.element_map):
            for e, element in enumerate(row):
                self.elements[element].rx_gain = value[r][e]

    @property
    def all_rx_phases(self):
        """Get/Set all Rx Phase settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        phase_map = []
        for r, row in enumerate(self.element_map):
            phase_map.append([])
            for element in row:
                phase_map[r].append(self.elements[element].rx_phase)

        return phase_map

    @all_rx_phases.setter
    def all_rx_phases(self, value):
        """Get/Set all Rx Phase settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        for r, row in enumerate(self.element_map):
            for e, element in enumerate(row):
                self.elements[element].rx_phase = value[r][e]

    @property
    def all_tx_attenuators(self):
        """Get/Set all Tx Attenuator settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        attenuator_map = []
        for r, row in enumerate(self.element_map):
            attenuator_map.append([])
            for element in row:
                attenuator_map[r].append(self.elements[element].tx_attenuator)

        return attenuator_map

    @all_tx_attenuators.setter
    def all_tx_attenuators(self, value):
        """Get/Set all Tx Attenuator settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        for r, row in enumerate(self.element_map):
            for e, element in enumerate(row):
                self.elements[element].tx_attenuator = value[r][e]

    @property
    def all_tx_gains(self):
        """Get/Set all Tx Gain settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        gain_map = []
        for r, row in enumerate(self.element_map):
            gain_map.append([])
            for element in row:
                gain_map[r].append(self.elements[element].tx_gain)

        return gain_map

    @all_tx_gains.setter
    def all_tx_gains(self, value):
        """Get/Set all Tx Gain settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        for r, row in enumerate(self.element_map):
            for e, element in enumerate(row):
                self.elements[element].tx_gain = value[r][e]

    @property
    def all_tx_phases(self):
        """Get/Set all Tx Phase settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        phase_map = []
        for r, row in enumerate(self.element_map):
            phase_map.append([])
            for element in row:
                phase_map[r].append(self.elements[element].tx_phase)

        return phase_map

    @all_tx_phases.setter
    def all_tx_phases(self, value):
        """Get/Set all Tx Phase settings in the array.
        The format is a list of lists where each row in the
        array is a list entry in the larger list."""
        for r, row in enumerate(self.element_map):
            for e, element in enumerate(row):
                self.elements[element].tx_phase = value[r][e]

    @property
    def devices(self):
        """
        Dictionary representing all of the connected ADAR1000s.
        The dictionary key is the chip_id for each device.
        """
        return {device.array_device_number: device for device in self._devices.values()}

    @property
    def device_map(self):
        """ Get the map of ADAR1000s in the array """
        return self._device_map

    @property
    def elements(self):
        """
        Dictionary representing all of the connected ADAR1000 elements sorted by element number.
        The dictionary key is the element number for each device.
        """
        dictionary = {
            el.array_element_number: el
            for dev in self.devices.values()
            for el in dev.channels
        }
        return {k: v for k, v in sorted(dictionary.items(), key=lambda x: x[0])}

    @property
    def element_map(self):
        """ Get the map of elements in the array """
        return self._element_map

    @property
    def element_spacing(self):
        """ Get/Set the element spacing for the array in meters """
        return self._element_spacing

    @element_spacing.setter
    def element_spacing(self, value):
        """ Get/Set the element spacing for the array in meters """
        self._element_spacing = value

    @property
    def frequency(self):
        """ Get/Set the board frequency in Hz """
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        """ Get/Set the board frequency in Hz """
        self._frequency = value

    @property
    def rx_azimuth(self):
        """ Get the Rx azimuth angle for the array in degrees """
        return self._rx_azimuth

    @property
    def rx_azimuth_phi(self):
        """ Get the Rx azimuth phi angle for the array in degrees """
        return self._rx_azimuth_phi

    @property
    def rx_elevation(self):
        """ Get the Rx elevation angle for the array in degrees """
        return self._rx_elevation

    @property
    def rx_elevation_phi(self):
        """ Get the Rx elevation phi angle for the array in degrees """
        return self._rx_elevation_phi

    @property
    def temperatures(self):
        """ Get the temperature readings of the ADAR1000s in a dictionary """
        return {chip_id: device.temperature for chip_id, device in self.devices.items()}

    @property
    def tx_azimuth(self):
        """ Get the Tx azimuth angle for the array in degrees """
        return self._tx_azimuth

    @property
    def tx_azimuth_phi(self):
        """ Get the Tx azimuth phi angle for the array in degrees """
        return self._tx_azimuth_phi

    @property
    def tx_elevation(self):
        """ Get the Tx elevation angle for the array in degrees """
        return self._tx_elevation

    @property
    def tx_elevation_phi(self):
        """ Get the Tx elevation phi angle for the array in degrees """
        return self._tx_elevation_phi

    def _steer(self, rx_or_tx, azimuth, elevation):
        """Steer the array
        parameters:
            rx_or_tx: string
                Sets which parameters are updated, Rx or Tx.
            azimuth: float
                Desired beam angle in degrees for the horizontal direction
            elevation: float
                Desired beam angle in degrees for the vertical direction
        """

        # Clean up the rx_or_tx variable
        rx_or_tx = rx_or_tx.strip().lower()

        # Calculate the Φ angles for each element in both directions (in degrees)
        azimuth_phi, elevation_phi = self.calculate_phi(azimuth, elevation)

        # Update the class variables
        if rx_or_tx == "rx":
            self._rx_azimuth = azimuth
            self._rx_elevation = elevation
            self._rx_azimuth_phi = azimuth_phi
            self._rx_elevation_phi = elevation_phi
        else:
            self._tx_azimuth = azimuth
            self._tx_elevation = elevation
            self._tx_azimuth_phi = azimuth_phi
            self._tx_elevation_phi = elevation_phi

        # Steer the elements in the array
        for element in self.elements.values():
            # Calculate the row and column phases
            column_phase = element.column * azimuth_phi
            row_phase = element.row * elevation_phi

            if rx_or_tx == "rx":
                element.rx_phase = column_phase + row_phase
            else:
                element.tx_phase = column_phase + row_phase

        # Latch in the new phases
        if rx_or_tx == "rx":
            self.latch_rx_settings()
        else:
            self.latch_tx_settings()

    """ Public Methods """

    def calculate_phi(self, azimuth, elevation):
        """Calculate the Φ angles to steer the array in a particular direction. This method assumes that the entire
            array is one analog beam.
        parameters:
            azimuth: float
                Desired beam angle in degrees for the horizontal direction.
            elevation: float
                Desired beam angle in degrees for the vertical direction.
        """

        # Convert the input angles to radians
        az_rads = azimuth * pi / 180
        el_rads = elevation * pi / 180

        # Calculate the phase increment (Φ) for each element in the array in both directions (in degrees)
        az_phi = 2 * self.frequency * self.element_spacing * sin(az_rads) * 180 / 3e8
        el_phi = 2 * self.frequency * self.element_spacing * sin(el_rads) * 180 / 3e8

        return az_phi, el_phi

    def initialize_devices(self, pa_off=-2.5, pa_on=-2.5, lna_off=-2, lna_on=-2):
        """Suggested initialization routine after powerup

        parameters:
            pa_off: float
                Voltage to set the PA_BIAS_OFF values to during initialization
            pa_on: float
                Voltage to set the PA_BIAS_ON values to during initialization
            lna_off: float
                Voltage to set the LNA_BIAS_OFF values to during initialization
            lna_on: float
                Voltage to set the LNA_BIAS_ON values to during initialization
        """
        for device in self.devices.values():
            device.initialize(
                pa_off=pa_off, pa_on=pa_on, lna_off=lna_off, lna_on=lna_on
            )

    def latch_rx_settings(self):
        """ Latch in new Gain/Phase settings for the Rx """
        for device in self.devices.values():
            device.latch_rx_settings()

    def latch_tx_settings(self):
        """ Latch in new Gain/Phase settings for the Tx """
        for device in self.devices.values():
            device.latch_tx_settings()

    def steer_rx(self, azimuth, elevation):
        """Steer the Rx array in a particular direction. This method assumes that the entire array is one analog beam.

        parameters:
            azimuth: float
                Desired beam angle in degrees for the horizontal direction.
            elevation: float
                Desired beam angle in degrees for the vertical direction.
        """

        self._steer("rx", azimuth, elevation)

    def steer_tx(self, azimuth, elevation):
        """Steer the Tx array in a particular direction. This method assumes that the entire array is one analog beam.

        parameters:
            azimuth: float
                Desired beam angle in degrees for the horizontal direction.
            elevation: float
                Desired beam angle in degrees for the vertical direction.
        """

        self._steer("tx", azimuth, elevation)
