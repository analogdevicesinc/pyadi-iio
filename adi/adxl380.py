# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class adxl380_temp_channel(attribute):
    """adxl380 temperature channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize an ADXL380 temperature channel."""
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


class adxl380_channel(attribute):
    """adxl380 acceleration channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize an ADXL380 acceleration channel."""
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
        return self._get_iio_attr(self.name, "filter_high_pass_3db_frequency", False)

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
            self.name, "filter_low_pass_3db_frequency", False, str(Decimal(value).real),
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


class adxl380(rx_chan_comp):
    """ adxl380 3-axis accelerometer """

    _device_name = "adxl380"
    _rx_unbuffered_data = True
    _rx_data_si_type = float
    _complex_data = False
    _rx_channel_names = ["accel_x", "accel_y", "accel_z"]
    compatible_parts = ["adxl380", "adxl382"]

    def __init__(self, uri="", device_name=None, device_index=0):
        """Initialize the first available compatible accelerometer."""
        # The device may report as any of the compatible parts. Try each in
        # turn so the class works whether an adxl380 or adxl382 is present.
        if device_name and device_name not in self.compatible_parts:
            raise Exception(
                f"Not a compatible device: {device_name}. Supported device names "
                f"are: {','.join(self.compatible_parts)}"
            )

        requested_part = device_name or self.compatible_parts[0]
        parts = [requested_part] + [
            part for part in self.compatible_parts if part != requested_part
        ]
        last_exception = None
        for part in parts:
            self.__dict__["_control_device_name"] = None
            self.__dict__["_rx_data_device_name"] = None
            try:
                super().__init__(uri=uri, device_name=part, device_index=device_index)
                return
            except Exception as exc:  # noqa: BLE001
                last_exception = exc
        if last_exception is not None:
            raise last_exception
        raise Exception("No compatible device found")  # pragma: no cover

    def __post_init__(self):
        """Set a small default receive-buffer size."""
        self.rx_buffer_size = 16  # Make default buffer smaller

    def _channel_def(self, ctrl, name):
        if name == "temp":
            return adxl380_temp_channel(ctrl, name)
        return adxl380_channel(ctrl, name)

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
