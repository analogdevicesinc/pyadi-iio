# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

import numpy as np

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


def _sign_extend(value, nbits):
    sign_bit = 1 << (nbits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


def _bitmask(nbits):
    mask = 0
    for i in range(0, nbits):
        mask = (mask << 1) | 1
    return mask


class ad4630(rx, context_manager, attribute):

    """ AD4630 is low power 24-bit precision SAR ADC """

    _compatible_parts = ["ad4630-24", "ad4030-24", "ad4630-16"]
    _complex_data = False
    _data_type = np.uint32
    _device_name = ""
    _rx_channel_names = []

    """ Default part to initialize is ad4630-24. If you don't hardware test fails"""

    def __init__(self, uri="", device_name="ad4630-24"):

        context_manager.__init__(self, uri, self._device_name)

        if device_name not in self._compatible_parts:
            raise Exception(
                "Not a compatible device: "
                + str(device_name)
                + ". Please select from "
                + str(self.self._compatible_parts)
            )
        else:
            self._ctrl = self._ctx.find_device(device_name)
            self._rxadc = self._ctx.find_device(device_name)

        _channels = []
        self.output_bits = []
        for ch in self._ctrl.channels:
            self.output_bits.append(ch.data_format.bits)
            self._rx_channel_names.append(ch.id)
            _channels.append((ch.id, self._channel(self._ctrl, ch.id)))
            if "0" in ch.id:
                self.chan0 = self._channel(self._ctrl, ch.id)
            if "1" in ch.id:
                self.chan1 = self._channel(self._ctrl, ch.id)

        rx.__init__(self)

    def rx(self):
        data = self._rx_buffered_data()
        temp = []
        if self._num_rx_channels != 2:
            for ch in range(0, self._num_rx_channels):
                nbits = self._ctrl.channels[ch].data_format.bits
                shift = self._ctrl.channels[ch].data_format.shift
                ch_data = np.zeros(data[int(ch / 2)].shape, dtype=np.uint32)
                for index in range(0, len(data[int(ch / 2)])):
                    ch_data[index] = (data[int(ch / 2)][index] >> shift) & _bitmask(
                        nbits
                    )
                temp.append(np.vectorize(_sign_extend)(ch_data, nbits))
            data = temp
        else:
            for idx, ch_data in enumerate(data):
                nbits = self._ctrl.channels[idx].data_format.bits
                temp.append(np.vectorize(_sign_extend)(ch_data, nbits))
            data = np.vectorize(_sign_extend)(data, nbits)

        return data

    def output_data_mode(self):
        """Determine the output data mode in which device is configured."""
        if self.output_bits[0] == 30:
            return "30bit_avg"
        if self.output_bits[0] == 32:
            return "32bit_test_pattern"
        if self.output_bits[0] == 16:
            return "16bit_diff_8bit_cm"
        if len(self.output_bits) == 1 and self.output_bits[0] == 24:
            return "24bit_diff"
        if len(self.output_bits) == 2 and self.output_bits[0] == self.output_bits[1]:
            return "24bit_diff"
        else:
            return "24bit_diff_8bit_cm"

    @property
    def sample_rate(self):
        """Get the sampling frequency."""
        return self._get_iio_dev_attr("sampling_frequency")

    @sample_rate.setter
    def sample_rate(self, rate):
        """Set the sampling frequency."""
        self._set_iio_dev_attr("sampling_frequency", str(rate))

    @property
    def sample_averaging_avail(self):
        """Get list of all the sample averaging values available. Only available in 30bit averaged mode."""
        return self._get_iio_dev_attr("sample_averaging_available")

    @property
    def sample_averaging(self):
        """Get the sample averaging. Only available in 30bit averaged mode."""
        return self._get_iio_dev_attr_str("sample_averaging")

    @sample_averaging.setter
    def sample_averaging(self, n_sample):
        """Set the sample averaging. Only available in 30bit averaged mode."""
        if str(self.sample_averaging) != "OFF":
            if str(n_sample) in str(self.sample_averaging_avail):
                self._set_iio_dev_attr("sample_averaging", str(n_sample))
            else:
                raise ValueError(
                    "Error: Number of avg samples not supported \nUse one of: "
                    + str(self.sample_averaging_avail)
                )
        else:
            raise Exception("Sample Averaging only available in 30bit averaged mode.")

    class _channel(attribute):
        """AD4x30 differential channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def calibbias(self):
            """Get calibration bias/offset value."""
            return self._get_iio_attr(self.name, "calibbias", False, self._ctrl)

        @calibbias.setter
        def calibbias(self, calibbias):
            """Set calibration bias/offset value."""
            self._set_iio_attr(
                self.name, "calibbias", False, int(calibbias), self._ctrl
            )

        @property
        def calibscale(self):
            """Get calibration scale value."""
            return self._get_iio_attr(self.name, "calibscale", False, self._ctrl)

        @calibscale.setter
        def calibscale(self, calibscale):
            """Set calibration scale value."""
            self._set_iio_attr(self.name, "calibscale", False, calibscale, self._ctrl)


class adaq42xx(ad4630):

    """ ADAQ4224 is a 24-bit precision SAR ADC data acquisition module """

    _compatible_parts = ["adaq4224", "adaq4216", "adaq4220"]

    def __init__(self, uri="", device_name="adaq4224"):
        super().__init__(uri, device_name)

    class _channel(ad4630._channel):
        """ADAQ42xx differential channel."""

        @property
        def scale_available(self):
            """Provides all available scale(gain) settings for the ADAQ42xx channel"""
            return self._get_iio_attr(self.name, "scale_available", False)

        @property
        def scale(self):
            """ADAQ42xx channel scale"""
            return float(self._get_iio_attr_str(self.name, "scale", False))

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", False, str(Decimal(value).real))
