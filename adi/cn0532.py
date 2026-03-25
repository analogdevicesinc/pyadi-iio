# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

from adi.cn0540 import cn0540, reset_buffer


class cn0532(cn0540):
    """CN0532: Custom board with ADXL1002 Low Noise, High Frequency +/-50g MEMS Accelerometer"""

    def __init__(self, uri=""):

        cn0540.__init__(self, uri=uri)

    @reset_buffer
    def calibrate(self):
        """Tune LTC2606 to make AD7768-1 ADC codes zero mean"""
        adc_chan = self._rxadc
        dac_chan = self._ltc2606
        adc_scale = float(self._get_iio_attr("voltage0", "scale", False, adc_chan))
        dac_scale = float(self._get_iio_attr("voltage0", "scale", True, dac_chan))

        for _ in range(20):
            raw = self._get_iio_attr("voltage0", "raw", False, adc_chan)
            adc_voltage = raw * adc_scale

            raw = self._get_iio_attr("voltage0", "raw", True, dac_chan)
            dac_voltage = (raw * dac_scale - adc_voltage) / dac_scale

            e = int(dac_voltage * dac_scale)

            if int(dac_voltage) > 2 ** 16 - 1:
                print(
                    "Warning: DAC voltage at upper limit, "
                    + f"calibration may not converge (Error: {e - (2**16 - 1)} codes).\n"
                    + "Make sure sensor is connected."
                )
                dac_voltage = 2 ** 16 - 1
            elif int(dac_voltage) < 0:
                print(
                    "Warning: DAC voltage at lower limit, "
                    + f"calibration may not converge (Error: {e} codes).\n"
                    + "Make sure sensor is connected."
                )
                dac_voltage = 0

            self._set_iio_attr_float(
                "voltage0", "raw", True, int(dac_voltage), dac_chan
            )
            time.sleep(0.01)
