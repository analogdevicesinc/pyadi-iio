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

from adi.attribute import attribute
from adi.context_manager import context_manager


class adar1000(attribute, context_manager):
    """ADAR1000 Beamformer

    parameters:
        uri: type=string
            URI of IIO context with ADAR1000(s)
        chip_id: type=string
            String identifying desired chip select and hardware ID for the
            ADAR1000. This string is the label coinciding with each chip
            select and hardware address and are typically in the form csbX_chipX.
            The csb line can be any number depending on how many are used in the
            system. The chip number will typically be 1-4 because each CSB line
            can control up to four ADAR1000s.
        context_handle: type=iio.Context
            IIO context handle. Not used unless creating an array of chips.
    """

    _device_name = ""
    _BIAS_CODE_TO_VOLTAGE_SCALE = -0.018824

    def __init__(self, uri="", chip_id="csb1_chip1", context_handle=None):

        # Use the given context if possible, otherwise lookup the context
        if context_handle is not None:
            self._ctx = context_handle
        else:
            context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None
        self._chip_id = chip_id

        # Raise an error if the chip_id is a list. Suggest using the array class
        if isinstance(chip_id, (list, tuple, set)):
            raise Exception(
                '"chip_id" can\'t be an iterable. '
                "Please use the adar1000_array class for instantiating multiple devices"
            )

        # Look for the matching device in the context
        for dev in self._ctx.devices:
            if (
                "label" in dev.attrs
                and dev.attrs["label"].value.lower() == chip_id.lower()
            ):
                self._ctrl = dev
                break

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception(f"Device not found for {chip_id}")

    @property
    def chip_id(self):
        """
        Chip ID including CSB and hardware address. Of the form "csbX_chipX" where csbX indicates the CSB
        line for the IC and chipX indicating the hardware address of the chip, 1-4.
        """
        return self._chip_id

    """ Device attributes """

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
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_dev_attr_str("lna_bias_off", dac_code, self._ctrl)

    @property
    def lna_bias_on(self):
        """ Get/Set LNA_BIAS_ON in voltage """
        dac_code = self._get_iio_dev_attr("lna_bias_on", self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @lna_bias_on.setter
    def lna_bias_on(self, value):
        """ Get/Set LNA_BIAS_ON in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
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
    def rx_enable(self):
        """ Get/Set enable for entire Rx chain """
        return bool(self._get_iio_dev_attr("rx_en", self._ctrl))

    @rx_enable.setter
    def rx_enable(self, value):
        """ Get/Set enable for entire Rx chain """
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
    def tx_enable(self):
        """ Get/Set enable for entire Tx chain """
        return bool(self._get_iio_dev_attr("tx_en", self._ctrl))

    @tx_enable.setter
    def tx_enable(self, value):
        """ Get/Set enable for entire Tx chain """
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

    """ Channel attributes """

    @property
    def ch1_detector_enable(self):
        """ Get/Set Channel 1 detector enable bit """
        return bool(self._get_iio_attr("voltage0", "detector_en", True, self._ctrl))

    @ch1_detector_enable.setter
    def ch1_detector_enable(self, value):
        """ Get/Set Channel 1 detector enable bit """
        self._set_iio_attr("voltage0", "detector_en", True, int(value), self._ctrl)

    @property
    def ch2_detector_enable(self):
        """ Get/Set Channel 2 detector enable bit """
        return bool(self._get_iio_attr("voltage1", "detector_en", True, self._ctrl))

    @ch2_detector_enable.setter
    def ch2_detector_enable(self, value):
        """ Get/Set Channel 2 detector enable bit """
        self._set_iio_attr("voltage1", "detector_en", True, int(value), self._ctrl)

    @property
    def ch3_detector_enable(self):
        """ Get/Set Channel 3 detector enable bit """
        return bool(self._get_iio_attr("voltage2", "detector_en", True, self._ctrl))

    @ch3_detector_enable.setter
    def ch3_detector_enable(self, value):
        """ Get/Set Channel 3 detector enable bit """
        self._set_iio_attr("voltage2", "detector_en", True, int(value), self._ctrl)

    @property
    def ch4_detector_enable(self):
        """ Get/Set Channel 4 detector enable bit """
        return bool(self._get_iio_attr("voltage3", "detector_en", True, self._ctrl))

    @ch4_detector_enable.setter
    def ch4_detector_enable(self, value):
        """ Get/Set Channel 4 detector enable bit """
        self._set_iio_attr("voltage3", "detector_en", True, int(value), self._ctrl)

    @property
    def ch1_detector_power(self):
        """ Get Channel 1 detector power reading """
        return self._get_iio_attr("voltage0", "raw", True, self._ctrl)

    @property
    def ch2_detector_power(self):
        """ Get Channel 2 detector power reading """
        return self._get_iio_attr("voltage1", "raw", True, self._ctrl)

    @property
    def ch3_detector_power(self):
        """ Get Channel 3 detector power reading """
        return self._get_iio_attr("voltage2", "raw", True, self._ctrl)

    @property
    def ch4_detector_power(self):
        """ Get Channel 4 detector power reading """
        return self._get_iio_attr("voltage3", "raw", True, self._ctrl)

    @property
    def ch1_pa_bias_off(self):
        """ Get/Set Channel 1 PA_BIAS_OFF in voltage """
        dac_code = self._get_iio_attr("voltage0", "pa_bias_off", True, self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @ch1_pa_bias_off.setter
    def ch1_pa_bias_off(self, value):
        """ Get/Set Channel 1 PA_BIAS_OFF in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_attr("voltage0", "pa_bias_off", True, dac_code, self._ctrl)

    @property
    def ch2_pa_bias_off(self):
        """ Get/Set Channel 2 PA_BIAS_OFF in voltage """
        dac_code = self._get_iio_attr("voltage1", "pa_bias_off", True, self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @ch2_pa_bias_off.setter
    def ch2_pa_bias_off(self, value):
        """ Get/Set Channel 2 PA_BIAS_OFF in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_attr("voltage1", "pa_bias_off", True, dac_code, self._ctrl)

    @property
    def ch3_pa_bias_off(self):
        """ Get/Set Channel 3 PA_BIAS_OFF in voltage """
        dac_code = self._get_iio_attr("voltage2", "pa_bias_off", True, self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @ch3_pa_bias_off.setter
    def ch3_pa_bias_off(self, value):
        """ Get/Set Channel 3 PA_BIAS_OFF in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_attr("voltage2", "pa_bias_off", True, dac_code, self._ctrl)

    @property
    def ch4_pa_bias_off(self):
        """ Get/Set Channel 4 PA_BIAS_OFF in voltage """
        dac_code = self._get_iio_attr("voltage3", "pa_bias_off", True, self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @ch4_pa_bias_off.setter
    def ch4_pa_bias_off(self, value):
        """ Get/Set Channel 4 PA_BIAS_OFF in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_attr("voltage3", "pa_bias_off", True, dac_code, self._ctrl)

    @property
    def ch1_pa_bias_on(self):
        """ Get/Set Channel 1 PA_BIAS_ON in voltage """
        dac_code = self._get_iio_attr("voltage0", "pa_bias_on", True, self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @ch1_pa_bias_on.setter
    def ch1_pa_bias_on(self, value):
        """ Get/Set Channel 1 PA_BIAS_ON in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_attr("voltage0", "pa_bias_on", True, dac_code, self._ctrl)

    @property
    def ch2_pa_bias_on(self):
        """ Get/Set Channel 2 PA_BIAS_ON in voltage """
        dac_code = self._get_iio_attr("voltage1", "pa_bias_on", True, self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @ch2_pa_bias_on.setter
    def ch2_pa_bias_on(self, value):
        """ Get/Set Channel 2 PA_BIAS_ON in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_attr("voltage1", "pa_bias_on", True, dac_code, self._ctrl)

    @property
    def ch3_pa_bias_on(self):
        """ Get/Set Channel 3 PA_BIAS_ON in voltage """
        dac_code = self._get_iio_attr("voltage2", "pa_bias_on", True, self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @ch3_pa_bias_on.setter
    def ch3_pa_bias_on(self, value):
        """ Get/Set Channel 3 PA_BIAS_ON in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_attr("voltage2", "pa_bias_on", True, dac_code, self._ctrl)

    @property
    def ch4_pa_bias_on(self):
        """ Get/Set Channel 4 PA_BIAS_ON in voltage """
        dac_code = self._get_iio_attr("voltage3", "pa_bias_on", True, self._ctrl)
        return dac_code * self._BIAS_CODE_TO_VOLTAGE_SCALE

    @ch4_pa_bias_on.setter
    def ch4_pa_bias_on(self, value):
        """ Get/Set Channel 4 PA_BIAS_ON in voltage """
        dac_code = value / self._BIAS_CODE_TO_VOLTAGE_SCALE
        self._set_iio_attr("voltage3", "pa_bias_on", True, dac_code, self._ctrl)

    @property
    def ch1_rx_attenuator(self):
        """ Get/Set Channel 1 Rx Attenuator state """
        return bool(
            1 - self._get_iio_attr("voltage0", "attenuation", False, self._ctrl)
        )

    @ch1_rx_attenuator.setter
    def ch1_rx_attenuator(self, value):
        """ Get/Set Channel 1 Rx Attenuator state """
        self._set_iio_attr("voltage0", "attenuation", False, 1 - int(value), self._ctrl)

    @property
    def ch2_rx_attenuator(self):
        """ Get/Set Channel 2 Rx Attenuator state """
        return bool(
            1 - self._get_iio_attr("voltage1", "attenuation", False, self._ctrl)
        )

    @ch2_rx_attenuator.setter
    def ch2_rx_attenuator(self, value):
        """ Get/Set Channel 2 Rx Attenuator state """
        self._set_iio_attr("voltage1", "attenuation", False, 1 - int(value), self._ctrl)

    @property
    def ch3_rx_attenuator(self):
        """ Get/Set Channel 3 Rx Attenuator state """
        return bool(
            1 - self._get_iio_attr("voltage2", "attenuation", False, self._ctrl)
        )

    @ch3_rx_attenuator.setter
    def ch3_rx_attenuator(self, value):
        """ Get/Set Channel 3 Rx Attenuator state """
        self._set_iio_attr("voltage2", "attenuation", False, 1 - int(value), self._ctrl)

    @property
    def ch4_rx_attenuator(self):
        """ Get/Set Channel 4 Rx Attenuator state """
        return bool(
            1 - self._get_iio_attr("voltage3", "attenuation", False, self._ctrl)
        )

    @ch4_rx_attenuator.setter
    def ch4_rx_attenuator(self, value):
        """ Get/Set Channel 4 Rx Attenuator state """
        self._set_iio_attr("voltage3", "attenuation", False, 1 - int(value), self._ctrl)

    @property
    def ch1_rx_gain(self):
        """ Get/Set Channel 1 Rx Gain """
        return self._get_iio_attr("voltage0", "hardwaregain", False, self._ctrl)

    @ch1_rx_gain.setter
    def ch1_rx_gain(self, value):
        """ Get/Set Channel 1 Rx Gain """
        self._set_iio_attr("voltage0", "hardwaregain", False, value, self._ctrl)

    @property
    def ch2_rx_gain(self):
        """ Get/Set Channel 2 Rx Gain """
        return self._get_iio_attr("voltage1", "hardwaregain", False, self._ctrl)

    @ch2_rx_gain.setter
    def ch2_rx_gain(self, value):
        """ Get/Set Channel 2 Rx Gain """
        self._set_iio_attr("voltage1", "hardwaregain", False, value, self._ctrl)

    @property
    def ch3_rx_gain(self):
        """ Get/Set Channel 3 Rx Gain """
        return self._get_iio_attr("voltage2", "hardwaregain", False, self._ctrl)

    @ch3_rx_gain.setter
    def ch3_rx_gain(self, value):
        """ Get/Set Channel 3 Rx Gain """
        self._set_iio_attr("voltage2", "hardwaregain", False, value, self._ctrl)

    @property
    def ch4_rx_gain(self):
        """ Get/Set Channel 4 Rx Gain """
        return self._get_iio_attr("voltage3", "hardwaregain", False, self._ctrl)

    @ch4_rx_gain.setter
    def ch4_rx_gain(self, value):
        """ Get/Set Channel 4 Rx Gain """
        self._set_iio_attr("voltage3", "hardwaregain", False, value, self._ctrl)

    @property
    def ch1_rx_phase(self):
        """ Get/Set Channel 1 Rx Phase """
        return self._get_iio_attr("voltage0", "phase", False, self._ctrl)

    @ch1_rx_phase.setter
    def ch1_rx_phase(self, value):
        """ Get/Set Channel 1 Rx Phase """
        self._set_iio_attr("voltage0", "phase", False, value, self._ctrl)

    @property
    def ch2_rx_phase(self):
        """ Get/Set Channel 2 Rx Phase """
        return self._get_iio_attr("voltage1", "phase", False, self._ctrl)

    @ch2_rx_phase.setter
    def ch2_rx_phase(self, value):
        """ Get/Set Channel 2 Rx Phase """
        self._set_iio_attr("voltage1", "phase", False, value, self._ctrl)

    @property
    def ch3_rx_phase(self):
        """ Get/Set Channel 3 Rx Phase """
        return self._get_iio_attr("voltage2", "phase", False, self._ctrl)

    @ch3_rx_phase.setter
    def ch3_rx_phase(self, value):
        """ Get/Set Channel 3 Rx Phase """
        self._set_iio_attr("voltage2", "phase", False, value, self._ctrl)

    @property
    def ch4_rx_phase(self):
        """ Get/Set Channel 4 Rx Phase """
        return self._get_iio_attr("voltage3", "phase", False, self._ctrl)

    @ch4_rx_phase.setter
    def ch4_rx_phase(self, value):
        """ Get/Set Channel 4 Rx Phase """
        self._set_iio_attr("voltage3", "phase", False, value, self._ctrl)

    @property
    def ch1_rx_powerdown(self):
        """ Get/Set Channel 1 Rx Powerdown """
        return bool(self._get_iio_attr("voltage0", "powerdown", False, self._ctrl))

    @ch1_rx_powerdown.setter
    def ch1_rx_powerdown(self, value):
        """ Get/Set Channel 1 Rx Powerdown """
        self._set_iio_attr("voltage0", "powerdown", False, int(value), self._ctrl)

    @property
    def ch2_rx_powerdown(self):
        """ Get/Set Channel 2 Rx Powerdown """
        return bool(self._get_iio_attr("voltage1", "powerdown", False, self._ctrl))

    @ch2_rx_powerdown.setter
    def ch2_rx_powerdown(self, value):
        """ Get/Set Channel 2 Rx Powerdown """
        self._set_iio_attr("voltage1", "powerdown", False, int(value), self._ctrl)

    @property
    def ch3_rx_powerdown(self):
        """ Get/Set Channel 3 Rx Powerdown """
        return bool(self._get_iio_attr("voltage2", "powerdown", False, self._ctrl))

    @ch3_rx_powerdown.setter
    def ch3_rx_powerdown(self, value):
        """ Get/Set Channel 3 Rx Powerdown """
        self._set_iio_attr("voltage2", "powerdown", False, int(value), self._ctrl)

    @property
    def ch4_rx_powerdown(self):
        """ Get/Set Channel 4 Rx Powerdown """
        return bool(self._get_iio_attr("voltage3", "powerdown", False, self._ctrl))

    @ch4_rx_powerdown.setter
    def ch4_rx_powerdown(self, value):
        """ Get/Set Channel 4 Rx Powerdown """
        self._set_iio_attr("voltage3", "powerdown", False, int(value), self._ctrl)

    @property
    def ch1_tx_attenuator(self):
        """ Get/Set Channel 1 Tx Attenuator state """
        return bool(1 - self._get_iio_attr("voltage0", "attenuation", True, self._ctrl))

    @ch1_tx_attenuator.setter
    def ch1_tx_attenuator(self, value):
        """ Get/Set Channel 1 Tx Attenuator state """
        self._set_iio_attr("voltage0", "attenuation", True, 1 - int(value), self._ctrl)

    @property
    def ch2_tx_attenuator(self):
        """ Get/Set Channel 2 Tx Attenuator state """
        return bool(1 - self._get_iio_attr("voltage1", "attenuation", True, self._ctrl))

    @ch2_tx_attenuator.setter
    def ch2_tx_attenuator(self, value):
        """ Get/Set Channel 2 Tx Attenuator state """
        self._set_iio_attr("voltage1", "attenuation", True, 1 - int(value), self._ctrl)

    @property
    def ch3_tx_attenuator(self):
        """ Get/Set Channel 3 Tx Attenuator state """
        return bool(1 - self._get_iio_attr("voltage2", "attenuation", True, self._ctrl))

    @ch3_tx_attenuator.setter
    def ch3_tx_attenuator(self, value):
        """ Get/Set Channel 3 Tx Attenuator state """
        self._set_iio_attr("voltage2", "attenuation", True, 1 - int(value), self._ctrl)

    @property
    def ch4_tx_attenuator(self):
        """ Get/Set Channel 4 Tx Attenuator state """
        return bool(1 - self._get_iio_attr("voltage3", "attenuation", True, self._ctrl))

    @ch4_tx_attenuator.setter
    def ch4_tx_attenuator(self, value):
        """ Get/Set Channel 4 Tx Attenuator state """
        self._set_iio_attr("voltage3", "attenuation", True, 1 - int(value), self._ctrl)

    @property
    def ch1_tx_gain(self):
        """ Get/Set Channel 1 Tx Gain """
        return self._get_iio_attr("voltage0", "hardwaregain", True, self._ctrl)

    @ch1_tx_gain.setter
    def ch1_tx_gain(self, value):
        """ Get/Set Channel 1 Tx Gain """
        self._set_iio_attr("voltage0", "hardwaregain", True, value, self._ctrl)

    @property
    def ch2_tx_gain(self):
        """ Get/Set Channel 2 Tx Gain """
        return self._get_iio_attr("voltage1", "hardwaregain", True, self._ctrl)

    @ch2_tx_gain.setter
    def ch2_tx_gain(self, value):
        """ Get/Set Channel 2 Tx Gain """
        self._set_iio_attr("voltage1", "hardwaregain", True, value, self._ctrl)

    @property
    def ch3_tx_gain(self):
        """ Get/Set Channel 3 Tx Gain """
        return self._get_iio_attr("voltage2", "hardwaregain", True, self._ctrl)

    @ch3_tx_gain.setter
    def ch3_tx_gain(self, value):
        """ Get/Set Channel 3 Tx Gain """
        self._set_iio_attr("voltage2", "hardwaregain", True, value, self._ctrl)

    @property
    def ch4_tx_gain(self):
        """ Get/Set Channel 4 Tx Gain """
        return self._get_iio_attr("voltage3", "hardwaregain", True, self._ctrl)

    @ch4_tx_gain.setter
    def ch4_tx_gain(self, value):
        """ Get/Set Channel 4 Tx Gain """
        self._set_iio_attr("voltage3", "hardwaregain", True, value, self._ctrl)

    @property
    def ch1_tx_phase(self):
        """ Get/Set Channel 1 Tx Phase """
        return self._get_iio_attr("voltage0", "phase", True, self._ctrl)

    @ch1_tx_phase.setter
    def ch1_tx_phase(self, value):
        """ Get/Set Channel 1 Tx Phase """
        self._set_iio_attr("voltage0", "phase", True, value, self._ctrl)

    @property
    def ch2_tx_phase(self):
        """ Get/Set Channel 2 Tx Phase """
        return self._get_iio_attr("voltage1", "phase", True, self._ctrl)

    @ch2_tx_phase.setter
    def ch2_tx_phase(self, value):
        """ Get/Set Channel 2 Tx Phase """
        self._set_iio_attr("voltage1", "phase", True, value, self._ctrl)

    @property
    def ch3_tx_phase(self):
        """ Get/Set Channel 3 Tx Phase """
        return self._get_iio_attr("voltage2", "phase", True, self._ctrl)

    @ch3_tx_phase.setter
    def ch3_tx_phase(self, value):
        """ Get/Set Channel 3 Tx Phase """
        self._set_iio_attr("voltage2", "phase", True, value, self._ctrl)

    @property
    def ch4_tx_phase(self):
        """ Get/Set Channel 4 Tx Phase """
        return self._get_iio_attr("voltage3", "phase", True, self._ctrl)

    @ch4_tx_phase.setter
    def ch4_tx_phase(self, value):
        """ Get/Set Channel 4 Tx Phase """
        self._set_iio_attr("voltage3", "phase", True, value, self._ctrl)

    @property
    def ch1_tx_powerdown(self):
        """ Get/Set Channel 1 Tx Powerdown """
        return bool(self._get_iio_attr("voltage0", "powerdown", True, self._ctrl))

    @ch1_tx_powerdown.setter
    def ch1_tx_powerdown(self, value):
        """ Get/Set Channel 1 Tx Powerdown """
        self._set_iio_attr("voltage0", "powerdown", True, int(value), self._ctrl)

    @property
    def ch2_tx_powerdown(self):
        """ Get/Set Channel 2 Tx Powerdown """
        return bool(self._get_iio_attr("voltage1", "powerdown", True, self._ctrl))

    @ch2_tx_powerdown.setter
    def ch2_tx_powerdown(self, value):
        """ Get/Set Channel 2 Tx Powerdown """
        self._set_iio_attr("voltage1", "powerdown", True, int(value), self._ctrl)

    @property
    def ch3_tx_powerdown(self):
        """ Get/Set Channel 3 Tx Powerdown """
        return bool(self._get_iio_attr("voltage2", "powerdown", True, self._ctrl))

    @ch3_tx_powerdown.setter
    def ch3_tx_powerdown(self, value):
        """ Get/Set Channel 3 Tx Powerdown """
        self._set_iio_attr("voltage2", "powerdown", True, int(value), self._ctrl)

    @property
    def ch4_tx_powerdown(self):
        """ Get/Set Channel 4 Tx Powerdown """
        return bool(self._get_iio_attr("voltage3", "powerdown", True, self._ctrl))

    @ch4_tx_powerdown.setter
    def ch4_tx_powerdown(self, value):
        """ Get/Set Channel 4 Tx Powerdown """
        self._set_iio_attr("voltage3", "powerdown", True, int(value), self._ctrl)

    @property
    def rx_sequencer_start(self):
        """ Get/Set the Rx Sequencer's starting position """
        return self._get_iio_attr("voltage0", "sequence_start", False, self._ctrl)

    @rx_sequencer_start.setter
    def rx_sequencer_start(self, value):
        """ Get/Set the Rx Sequencer's starting position """
        self._sequence_start("rx", value)

    @property
    def rx_sequencer_stop(self):
        """ Get/Set the Rx Sequencer's ending position """
        return self._get_iio_attr("voltage0", "sequence_end", False, self._ctrl)

    @rx_sequencer_stop.setter
    def rx_sequencer_stop(self, value):
        """ Get/Set the Rx Sequencer's ending position """
        self._sequence_stop("rx", value)

    @property
    def temperature(self):
        """ Get the temperature reading from the device """
        return self._get_iio_attr("temp0", "raw", False, self._ctrl)

    @property
    def tx_sequencer_start(self):
        """ Get/Set the Tx Sequencer's starting position """
        return self._get_iio_attr("voltage0", "sequence_start", True, self._ctrl)

    @tx_sequencer_start.setter
    def tx_sequencer_start(self, value):
        """ Get/Set the Tx Sequencer's starting position """
        self._sequence_start("tx", value)

    @property
    def tx_sequencer_stop(self):
        """ Get/Set the Tx Sequencer's ending position """
        return self._get_iio_attr("voltage0", "sequence_end", True, self._ctrl)

    @tx_sequencer_stop.setter
    def tx_sequencer_stop(self, value):
        """ Get/Set the Tx Sequencer's ending position """
        self._sequence_stop("tx", value)

    """ Private Methods """

    def _load_beam(self, rx_or_tx, channel, state):
        """Load a beam from a memory position

        parameters:
            rx_or_tx: string
                String indicating whether to load an Rx or Tx beam state. Valid options are "rx" and "tx"
            channel: int, string
                Channel number to load (1-4) or "X" to load from CHX_{rx_or_tx}
            state: int
                State number to load. Valid options are 0 to 120
        """

        if rx_or_tx.lower() == "rx":
            output = False
        else:
            output = True

        if isinstance(channel, int):
            self._set_iio_attr(
                f"voltage{channel - 1}", "beam_pos_load", output, state, self._ctrl
            )
        else:
            self._set_iio_dev_attr_str(
                f"static_{rx_or_tx.lower()}_beam_pos", state, self._ctrl
            )

    def _load_bias(self, rx_or_tx, state):
        """Load a bias from a memory position

        parameters:
            rx_or_tx: string
                String indicating whether to load an Rx or Tx bias state. Valid options are "rx" and "tx"
            state: int
                State number to load. Valid options are 1 to 7
        """

        if rx_or_tx.lower() == "rx":
            output = False
        else:
            output = True

        self._set_iio_attr("voltage0", "bias_set_load", output, state, self._ctrl)

    def _sequence_start(self, rx_or_tx, state):
        """Set the sequencer's start position

        parameters:
            rx_or_tx: string
                String indicating whether to load an Rx or Tx bias state. Valid options are "rx" and "tx"
            state: int
                State number to set. Valid options are 0 to 120
        """

        if rx_or_tx.lower() == "rx":
            output = False
        else:
            output = True

        self._set_iio_attr("voltage0", "sequence_start", output, state, self._ctrl)

    def _sequence_stop(self, rx_or_tx, state):
        """Set the sequencer's stop position

        parameters:
            rx_or_tx: string
                String indicating whether to load an Rx or Tx bias state. Valid options are "rx" and "tx"
            state: int
                State number to set. Valid options are 0 to 120
        """

        if rx_or_tx.lower() == "rx":
            output = False
        else:
            output = True

        self._set_iio_attr("voltage0", "sequence_end", output, state, self._ctrl)

    """ Public Methods """

    def generate_clocks(self):
        """ Generate CLK cycles before pulsing RX_LOAD or TX_LOAD """
        self._set_iio_dev_attr_str("gen_clk_cycles", "", self._ctrl)

    def latch_rx_settings(self):
        """ Latch in new Gain/Phase settings for the Rx """
        self._set_iio_dev_attr_str("rx_load_spi", 1, self._ctrl)

    def latch_tx_settings(self):
        """ Latch in new Gain/Phase settings for the Tx """
        self._set_iio_dev_attr_str("tx_load_spi", 1, self._ctrl)

    def load_rx_beam(self, channel, state):
        """Load an Rx beam from a memory position

        parameters:
            channel: int
                Channel number to load
            state: int
                State number to load. Valid options are 0 to 120
        """
        self._load_beam("rx", channel, state)

    def load_tx_beam(self, channel, state):
        """Load a Tx beam from a memory position

        parameters:
            channel: int
                Channel number to load
            state: int
                State number to load. Valid options are 0 to 120
        """
        self._load_beam("tx", channel, state)

    def load_rx_bias(self, state):
        """Load an Rx bias from a memory position

        parameters:
            state: int
                State number to load. Valid options are 1 to 7
        """
        self._load_bias("rx", state)

    def load_tx_bias(self, state):
        """Load a Tx bias from a memory position

        parameters:
            state: int
                State number to load. Valid options are 1 to 7
        """
        self._load_bias("tx", state)

    def reset(self):
        """ Reset ADAR1000 to default settings """
        self._set_iio_dev_attr_str("reset", "1", self._ctrl)


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
            1-4 because each CSB line can control up to four ADAR1000s. Use
            a list when multiple chips are to be controlled.
    """

    _device_name = ""

    def __init__(
        self, uri="", chip_ids=("csb1_chip1", "csb1_chip2", "csb1_chip3", "csb1_chip4")
    ):
        context_manager.__init__(self, uri, self._device_name)

        self._ctrls = []

        for chip_id in chip_ids:
            # Get an ADAR1000 handle for each chip ID using the context already found
            self._ctrls.append(adar1000(uri, chip_id, self._ctx))

        if len(self._ctrls) != len(chip_ids):
            raise Exception(f"Couldn't find all devices in {', '.join(chip_ids)}")

    def __repr__(self):
        """ Representation of the ADAR1000 array class """
        return f"ADAR1000 array containing {len(self.devices)} ADAR1000 instances:\n\t{', '.join(self.devices)}"

    @property
    def all_rx_gains(self):
        """ Get/Set all Rx Gain settings in the array. """
        return {
            f"{chip.chip_id}_ch{ch}": getattr(chip, f"ch{ch}_rx_gain")
            for chip in self.devices.values()
            for ch in range(1, 5)
        }

    @all_rx_gains.setter
    def all_rx_gains(self, value):
        """ Get/Set all Rx Gain settings in the array. """
        for id_string, gain in value.items():
            chip_id = "_".join(id_string.split("_")[:2])
            channel = id_string.split("_")[-1]
            setattr(self.devices[chip_id], f"{channel}_rx_gain", gain)

    @property
    def all_rx_phases(self):
        """ Get/Set all Rx Phase settings in the array. """
        return {
            f"{chip.chip_id}_ch{ch}": getattr(chip, f"ch{ch}_rx_phase")
            for chip in self.devices.values()
            for ch in range(1, 5)
        }

    @all_rx_phases.setter
    def all_rx_phases(self, value):
        """ Get/Set all Rx Phase settings in the array. """
        for id_string, gain in value.items():
            chip_id = "_".join(id_string.split("_")[:2])
            channel = id_string.split("_")[-1]
            setattr(self.devices[chip_id], f"{channel}_rx_phase", gain)

    @property
    def all_tx_gains(self):
        """ Get/Set all Tx Gain settings in the array. """
        return {
            f"{chip.chip_id}_ch{ch}": getattr(chip, f"ch{ch}_tx_gain")
            for chip in self.devices.values()
            for ch in range(1, 5)
        }

    @all_tx_gains.setter
    def all_tx_gains(self, value):
        """ Get/Set all Tx Gain settings in the array. """
        for id_string, gain in value.items():
            chip_id = "_".join(id_string.split("_")[:2])
            channel = id_string.split("_")[-1]
            setattr(self.devices[chip_id], f"{channel}_tx_gain", gain)

    @property
    def all_tx_phases(self):
        """ Get/Set all Tx Phase settings in the array. """
        return {
            f"{chip.chip_id}_ch{ch}": getattr(chip, f"ch{ch}_tx_phase")
            for chip in self.devices.values()
            for ch in range(1, 5)
        }

    @all_tx_phases.setter
    def all_tx_phases(self, value):
        """ Get/Set all Tx Phase settings in the array. """
        for id_string, gain in value.items():
            chip_id = "_".join(id_string.split("_")[:2])
            channel = id_string.split("_")[-1]
            setattr(self.devices[chip_id], f"{channel}_tx_phase", gain)

    @property
    def devices(self):
        """
        Dictionary representing all of the connected ADAR1000s.
        The dictionary key is the chip_id for each device.
        """
        return {chip.chip_id: chip for chip in self._ctrls}
