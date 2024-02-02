# Copyright (C) 2023-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adf4382(attribute, context_manager):
    """ADF4382 Microwave Wideband Synthesizer with Integrated VCO

    parameters:
        uri: type=string
            URI of IIO context with ADF4382
    """

    _device_name = "adf4382"
    _charge_pump_options = (
        "0.700000",
        "0.900000",
        "1.100000",
        "1.300000",
        "1.500000",
        "1.900000",
        "2.300000",
        "2.700000",
        "3.100000",
        "3.900000",
        "4.700000",
        "5.500000",
        "6.300000",
        "7.900000",
        "9.500000",
        "11.100000",
    )

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)

        # Find the device
        self._ctrl = self._ctx.find_device(self._device_name)

        # Raise an exception if the device isn't found
        if not self._ctrl:
            raise Exception("ADF4355 device not found")

    @property
    def altvolt0_en(self):
        return bool(self._get_iio_attr("altvoltage0", "en", True, self._ctrl))

    @altvolt0_en.setter
    def altvolt0_en(self, value):
        self._set_iio_attr("altvoltage0", "en", True, int(value), self._ctrl)

    @property
    def altvolt0_output_power(self):
        return self._get_iio_attr("altvoltage0", "output_power", True, self._ctrl)

    @altvolt0_output_power.setter
    def altvolt0_output_power(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "output_power", True, int(value), self._ctrl
        )

    @property
    def altvolt0_frequency(self):
        return self._get_iio_attr("altvoltage0", "frequency", True, self._ctrl)

    @altvolt0_frequency.setter
    def altvolt0_frequency(self, value):
        self._set_iio_attr_int("altvoltage0", "frequency", True, value, self._ctrl)

    @property
    def altvolt0_phase(self):
        return self._get_iio_attr("altvoltage0", "phase", True, self._ctrl)

    @altvolt0_phase.setter
    def altvolt0_phase(self, value):
        self._set_iio_attr_int("altvoltage0", "phase", True, value, self._ctrl)

    @property
    def altvolt1_en(self):
        return bool(self._get_iio_attr("altvoltage1", "en", True, self._ctrl))

    @altvolt1_en.setter
    def altvolt1_en(self, value):
        self._set_iio_attr("altvoltage1", "en", True, int(value), self._ctrl)

    @property
    def altvolt1_output_power(self):
        return self._get_iio_attr("altvoltage1", "output_power", True, self._ctrl)

    @altvolt1_output_power.setter
    def altvolt1_output_power(self, value):
        self._set_iio_attr_int(
            "altvoltage1", "output_power", True, int(value), self._ctrl
        )

    @property
    def altvolt1_frequency(self):
        return self._get_iio_attr("altvoltage1", "frequency", True, self._ctrl)

    @altvolt1_frequency.setter
    def altvolt1_frequency(self, value):
        self._set_iio_attr_int("altvoltage1", "frequency", True, value, self._ctrl)

    @property
    def altvolt1_phase(self):
        return self._get_iio_attr("altvoltage1", "phase", True, self._ctrl)

    @altvolt1_phase.setter
    def altvolt1_phase(self, value):
        self._set_iio_attr_int("altvoltage1", "phase", True, value, self._ctrl)

    @property
    def bleed_current(self):
        return self._get_iio_dev_attr("bleed_current", self._ctrl)

    @bleed_current.setter
    def bleed_current(self, value):
        self._set_iio_dev_attr("bleed_current", value, self._ctrl)

    @property
    def charge_pump_current(self):
        return self._get_iio_dev_attr("charge_pump_current", self._ctrl)

    @charge_pump_current.setter
    def charge_pump_current(self, value):
        # Check that the value is valid
        if value.lower().strip() not in self._charge_pump_options:
            raise ValueError(
                f"charge_pump_current of \"{value}\" is invalid. Valid options: {', '.join(self._charge_pump_options)}"
            )

        self._set_iio_dev_attr("charge_pump_current", value, self._ctrl)

    @property
    def reference_divider(self):
        return self._get_iio_dev_attr("reference_divider", self._ctrl)

    @reference_divider.setter
    def reference_divider(self, value):
        self._set_iio_dev_attr("reference_divider", value, self._ctrl)

    @property
    def reference_doubler_en(self):
        return self._get_iio_dev_attr("reference_doubler_en", self._ctrl)

    @reference_doubler_en.setter
    def reference_doubler_en(self, value):
        self._set_iio_dev_attr("reference_doubler_en", value, self._ctrl)

    @property
    def reference_frequency(self):
        return self._get_iio_dev_attr("reference_frequency", self._ctrl)

    @reference_frequency.setter
    def reference_frequency(self, value):
        self._set_iio_dev_attr("reference_frequency", value, self._ctrl)

    @property
    def sync_en(self):
        return self._get_iio_dev_attr("sync_en", self._ctrl)

    @sync_en.setter
    def sync_en(self, value):
        self._set_iio_dev_attr("sync_en", value, self._ctrl)
