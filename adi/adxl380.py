# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class adxl380(rx, context_manager, attribute):
    """ adxl380 3-axis accelerometer """

    _device_name = "adxl380"
    _rx_unbuffered_data = True
    _rx_data_si_type = float

    def __init__(self, uri="", device_name=None):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["adxl380", "adxl382"]

        if not device_name:
            device_name = compatible_parts[0]

        if device_name not in compatible_parts:
            raise Exception(
                "Not a compatible device:"
                + str(device_name)
                + ".Please select from:"
                + str(compatible_parts)
            )
        else:
            print("Device found: ", device_name)
            self._ctrl = self._ctx.find_device(device_name)
            self._rxadc = self._ctx.find_device(device_name)

            if self._ctrl is None:
                print(
                    "No device found with device_name = "
                    + device_name
                    + ". Searching for a device found in the compatible list."
                )
                for i in compatible_parts:
                    self._ctrl = self._ctx.find_device(i)
                    self._rxadc = self._ctx.find_device(i)
                    if self._ctrl is not None:
                        print("Found device = " + i + ". Will use this device instead.")
                        break
                if self._ctrl is None:
                    raise Exception("No compatible device found")

            self.accel_x = self._channel(self._ctrl, "accel_x")
            self.accel_y = self._channel(self._ctrl, "accel_y")
            self.accel_z = self._channel(self._ctrl, "accel_z")
            self.temp = self._tempchannel(self._ctrl, "temp")
            self._rx_channel_names = ["accel_x", "accel_y", "accel_z"]
            rx.__init__(self)
            self.rx_buffer_size = 16  # Make default buffer smaller

    @property
    def sampling_frequency(self):
        """Device sampling frequency"""
        return self._get_iio_dev_attr_str("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", str(Decimal(value).real))

    @property
    def sampling_frequency_available(self):
        """Device available sampling frequency"""
        return self._get_iio_dev_attr_str("sampling_frequency_available")

    @property
    def waiting_for_supplier(self):
        """Device waiting for supplier"""
        return self._get_iio_dev_attr_str("waiting_for_supplier")

    def to_degrees(self, raw):
        """Convert raw to degrees Celsius"""
        return (raw + self.temp.offset) * self.temp.scale / 1000.0

    class _tempchannel(attribute):
        """adxl380 temperature channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def offset(self):
            """adxl380 temperature offset value"""
            return self._get_iio_attr(self.name, "offset", False)

        @property
        def raw(self):
            """adxl380 temperature raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """adxl380 channel scale value"""
            return self._get_iio_attr(self.name, "scale", False)

    class _channel(attribute):
        """adxl380 acceleration channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def calibbias(self):
            """adxl380 channel offset"""
            return self._get_iio_attr(self.name, "calibbias", False)

        @calibbias.setter
        def calibbias(self, value):
            self._set_iio_attr(self.name, "calibbias", False, value)

        @property
        def filter_high_pass_3db_frequency(self):
            """adxl380 highpass filter cutoff frequency"""
            return self._get_iio_attr(
                self.name, "filter_high_pass_3db_frequency", False
            )

        @filter_high_pass_3db_frequency.setter
        def filter_high_pass_3db_frequency(self, value):
            self._set_iio_attr(
                self.name,
                "filter_high_pass_3db_frequency",
                False,
                str(Decimal(value).real),
            )

        @property
        def filter_high_pass_3db_frequency_available(self):
            """Provides all available highpass filter cutoff frequency settings for the adxl380 channels"""
            return self._get_iio_attr(
                self.name, "filter_high_pass_3db_frequency_available", False
            )

        @property
        def filter_low_pass_3db_frequency(self):
            """adxl380 lowpass filter cutoff frequency"""
            return self._get_iio_attr(self.name, "filter_low_pass_3db_frequency", False)

        @filter_low_pass_3db_frequency.setter
        def filter_low_pass_3db_frequency(self, value):
            self._set_iio_attr(
                self.name,
                "filter_low_pass_3db_frequency",
                False,
                str(Decimal(value).real),
            )

        @property
        def filter_low_pass_3db_frequency_available(self):
            """Provides all available lowpass filter cutoff frequency settings for the adxl380 channels"""
            return self._get_iio_attr(
                self.name, "filter_low_pass_3db_frequency_available", False
            )

        @property
        def raw(self):
            """adxl380 channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def scale(self):
            """adxl380 channel scale(gain)"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(
                self.name, "scale", False, str(Decimal(value).real),
            )

        @property
        def scale_available(self):
            """Provides all available scale settings for the adxl380 channels"""
            return self._get_iio_attr(self.name, "scale_available", False)
