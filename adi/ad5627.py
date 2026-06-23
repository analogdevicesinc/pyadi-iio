# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad5627(tx, context_manager):
    """ AD5627 Low Power Dual nanoDAC """

    _complex_data = False
    _tx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._txdac = self._ctx.find_device("ad5627")
        tx.__init__(self)

    @staticmethod
    def _adp_bias_volts_to_raw_convert(value, inverse):
        """Convert ADP bias from user values to internal values (or reverse)."""
        ret = 0.0
        if inverse:
            ret = -((value * 5 * 18.18) / 4096) + 122
        else:
            ret = ((-122 - value) * 4096) / (5 * 18.18)
        return ret

    @property
    def apdbias(self):
        """Get the APD Bias."""
        bias = self._get_iio_attr("voltage0", "raw", True, self._txdac)
        return self._adp_bias_volts_to_raw_convert(bias, True)

    @apdbias.setter
    def apdbias(self, value):
        """Set the APD Bias."""
        bias = self._adp_bias_volts_to_raw_convert(value, False)
        self._set_iio_attr_float("voltage0", "raw", True, bias, self._txdac)

    @staticmethod
    def _tilt_volts_to_raw_convert(value, inverse):
        """Convert tilt voltage from user values to internal values (or reverse)."""
        ret = 0.0
        if inverse:
            ret = (value * 5) / 4096
        else:
            ret = (value * 4096) / 5
        return ret

    @property
    def tiltvoltage(self):
        """Get the Tilt Voltage."""
        voltage = self._get_iio_attr("voltage1", "raw", True, self._txdac)
        return self._tilt_volts_to_raw_convert(voltage, True)

    @tiltvoltage.setter
    def tiltvoltage(self, voltage):
        """Set the Tilt Voltage."""
        voltage = self._tilt_volts_to_raw_convert(voltage, False)
        self._set_iio_attr_float("voltage1", "raw", True, voltage, self._txdac)
