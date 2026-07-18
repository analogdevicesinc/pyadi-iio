# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

from adi.cn0540 import cn0540, reset_buffer


class cn0532(cn0540):
    """CN0532 vibration sensor board with an ADXL1002 accelerometer.

    This interface inherits CN0540 buffered acquisition and board controls and
    adds automatic offset calibration for the ADXL1002 signal path.
    """

    @reset_buffer
    def calibrate(self):
        """Tune the LTC2606 until the AD7768-1 ADC codes approach zero mean.

        Run calibration with the sensor connected and stationary. The method
        performs 20 correction iterations, clamps the DAC code to its valid
        range, and prints a warning if the required correction would exceed
        that range.
        """
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
