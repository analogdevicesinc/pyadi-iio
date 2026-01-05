# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import numpy as np

from adi.ad9166 import ad9166 as ad9166_adi  # pyadi-iio library
from adi.context_manager import context_manager

try:
    import ad9166 as libad9166  # helper library for calibration function
except (ImportError, AttributeError):
    libad9166 = None


class cn0511(ad9166_adi):
    """ CN0511 Raspberry Pi Hat Signal Generator """

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        ad9166_adi.__init__(self, uri=uri)
        self._trim_dac_ch = "voltage0"
        self._trim_dac = self._ctx.find_device("ad5693r")
        self._amp = self._ctx.find_device("ad9166-amp")
        self.__calibrated_dev = self._ctx.find_device("ad9166")
        self.__ch = self.__calibrated_dev.find_channel("altvoltage0", True)
        if libad9166:
            self.__calibration_data = libad9166.find_calibration_data(
                self._ctx, "cn0511"
            )

        self.FIR85_enable = True
        self.sample_rate = 6000000000

    @property
    def trim_frequency_raw(self):
        """ trim_frequency_raw: modify output frequency of cn0511 in small steps"""
        return self._get_iio_attr(self._trim_dac_ch, "raw", True, self._trim_dac)

    @trim_frequency_raw.setter
    def trim_frequency_raw(self, value):
        self._set_iio_attr(self._trim_dac_ch, "raw", True, value, self._trim_dac)

    @property
    def amp_enable(self):
        """ amp_enable: Enable or Disable the CN0511 ad9166 amplifier """
        return True if (self._get_iio_dev_attr("en", _ctrl=self._amp) == 1) else False

    @amp_enable.setter
    def amp_enable(self, value=True):
        if value:
            val = 1
        else:
            val = 0
        self._set_iio_dev_attr_str("en", val, _ctrl=self._amp)

    @property
    def amplitude_cal(self):
        """amplitude_cal: CN0511 amplitude calibration

           Options:
               True: If you set this to true, the output is calibrated.
               False: Nothing happens.
        """
        return None

    @amplitude_cal.setter
    def amplitude_cal(self, value=True):
        if libad9166:
            if value:
                libad9166.device_set_iofs(
                    self.__calibrated_dev, self.__calibration_data, self.frequency
                )
        else:
            print("Warning: Missing libad9166, calibration failed.")

    @property
    def calibrated_output(self):
        """calibrated_output: ["desired_output_amplitude_in_dbm", "desired_output_frequency_in_Hz"]]"""
        if libad9166:
            return [int(20 * np.log10(self.raw / (2 ** 15))), self.frequency]
        print("Warning: Missing libad9166, calibration failed.")

    @calibrated_output.setter
    def calibrated_output(self, value):
        if libad9166:
            libad9166.set_amplitude(self.__calibrated_dev, value[0])
            libad9166.set_frequency(self.__ch, value[1])
            libad9166.device_set_iofs(
                self.__calibrated_dev, self.__calibration_data, value[1]
            )
        else:
            print("Warning: Missing libad9166, calibration failed.")

    @property
    def board_calibrated(self):
        """ board_calibrated: 1 if board was calibrated in production, 0 if board was not calibrated in production"""
        if libad9166:
            return libad9166.device_is_calibrated(self.__calibration_data)
        print("Warning: Missing libad9166, calibration failed.")
