# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx


class maxm86161(rx, context_manager):
    """MAXM86161 Integrated Optical Data Acquisition System (PPG AFE)

    Args:
        uri:
            URI of the IIO context (e.g. ``serial:/dev/ttyACM0,115200,8n1``
            or ``serial:COM149,115200,8n1`` for Windows).
        device_name:
            Name of the IIO device (default: ``maxm86161``).
    """

    _complex_data = False
    _device_name = "maxm86161"
    _rx_unbuffered_data = False
    _rx_channel_names = ["voltage0"]
    channel = []

    def __init__(self, uri="", device_name=""):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["maxm86161"]
        self._ctrl = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(f"Not a compatible device: {device_name}")

        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._rxadc = device
                break

        if not self._ctrl:
            raise Exception("Error in finding MAXM86161 device")

        rx.__init__(self)

    @property
    def sample_rate(self):
        """Get/set PPG sample-rate selection code."""
        return self._get_iio_debug_attr("sample_rate")

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_debug_attr_str("sample_rate", value)

    @property
    def integration_time(self):
        """Get/set PPG ADC integration-time selection.

        0=14.8us, 1=29.4us, 2=58.7us, 3=117.3us.
        """
        return self._get_iio_debug_attr("integration_time")

    @integration_time.setter
    def integration_time(self, value):
        self._set_iio_debug_attr_str("integration_time", value)

    @property
    def adc_range(self):
        """Get/set PPG ADC full-scale range selection.

        0=4uA, 1=8uA, 2=16uA, 3=32uA.
        """
        return self._get_iio_debug_attr("adc_range")

    @adc_range.setter
    def adc_range(self, value):
        self._set_iio_debug_attr_str("adc_range", value)

    @property
    def sample_averaging(self):
        """Get/set number of samples averaged per FIFO data point.

        0=1, 1=2, 2=4, 3=8, 4=16, 5=32, 6=64, 7=128.
        """
        return self._get_iio_debug_attr("sample_averaging")

    @sample_averaging.setter
    def sample_averaging(self, value):
        self._set_iio_debug_attr_str("sample_averaging", value)

    @property
    def alc_disable(self):
        """Get/set ambient-light cancellation disable flag (0=ALC on)."""
        return self._get_iio_debug_attr("alc_disable")

    @alc_disable.setter
    def alc_disable(self, value):
        self._set_iio_debug_attr_str("alc_disable", value)

    @property
    def add_offset(self):
        """Get/set ADC add-offset enable flag."""
        return self._get_iio_debug_attr("add_offset")

    @add_offset.setter
    def add_offset(self, value):
        self._set_iio_debug_attr_str("add_offset", value)

    @property
    def led_settling(self):
        """Get/set LED settling-time selection.

        0=4us, 1=6us, 2=8us, 3=12us.
        """
        return self._get_iio_debug_attr("led_settling")

    @led_settling.setter
    def led_settling(self, value):
        self._set_iio_debug_attr_str("led_settling", value)

    @property
    def dig_filter(self):
        """Get/set PPG digital-filter selection (0=CDM, 1=FDM)."""
        return self._get_iio_debug_attr("dig_filter")

    @dig_filter.setter
    def dig_filter(self, value):
        self._set_iio_debug_attr_str("dig_filter", value)

    @property
    def pd_bias(self):
        """Get/set photodiode bias selection.

        1=0-65pF, 5=65-130pF, 6=130-260pF, 7=260-520pF.
        """
        return self._get_iio_debug_attr("pd_bias")

    @pd_bias.setter
    def pd_bias(self, value):
        self._set_iio_debug_attr_str("pd_bias", value)

    @property
    def fifo_watermark(self):
        """Get/set FIFO almost-full watermark threshold."""
        return self._get_iio_debug_attr("fifo_watermark")

    @fifo_watermark.setter
    def fifo_watermark(self, value):
        self._set_iio_debug_attr_str("fifo_watermark", value)

    @property
    def fifo_rollover(self):
        """Get/set FIFO roll-over-on-full enable (0=stop, 1=overwrite)."""
        return self._get_iio_debug_attr("fifo_rollover")

    @fifo_rollover.setter
    def fifo_rollover(self, value):
        self._set_iio_debug_attr_str("fifo_rollover", value)

    @property
    def fifo_a_full_type(self):
        """Get/set FIFO almost-full interrupt assertion behavior."""
        return self._get_iio_debug_attr("fifo_a_full_type")

    @fifo_a_full_type.setter
    def fifo_a_full_type(self, value):
        self._set_iio_debug_attr_str("fifo_a_full_type", value)

    @property
    def fifo_count(self):
        """Get number of samples currently in the FIFO (read-only)."""
        return self._get_iio_debug_attr("fifo_count")

    @property
    def fifo_overflow_count(self):
        """Get number of samples lost to FIFO overflow (read-only)."""
        return self._get_iio_debug_attr("fifo_overflow_count")

    def get_led_sequence(self, slot):
        """Get the LED/measurement source for a sequence slot.

        Args:
            slot:
                Sequence slot number (1-6).

        Source codes: 0=none, 1=green, 2=IR, 3=red,
        8=pilot green, 9=direct ambient.
        """
        return self._get_iio_debug_attr(f"led_seq{slot}")

    def set_led_sequence(self, slot, value):
        """Set the LED/measurement source for a sequence slot.

        Args:
            slot:
                Sequence slot number (1-6).
            value:
                LED source code (0=none, 1=green, 2=IR, 3=red,
                8=pilot green, 9=direct ambient).
        """
        self._set_iio_debug_attr_str(f"led_seq{slot}", value)

    def get_led_pa(self, led):
        """Get the pulse amplitude (drive current code) of an LED.

        Args:
            led:
                LED number (1=green, 2=IR, 3=red).
        """
        return self._get_iio_debug_attr(f"led{led}_pa")

    def set_led_pa(self, led, value):
        """Set the pulse amplitude (drive current code) of an LED.

        Args:
            led:
                LED number (1=green, 2=IR, 3=red).
            value:
                8-bit pulse-amplitude code (0-255).
        """
        self._set_iio_debug_attr_str(f"led{led}_pa", value)

    @property
    def led_pilot_pa(self):
        """Get/set pilot LED pulse amplitude used in proximity mode."""
        return self._get_iio_debug_attr("led_pilot_pa")

    @led_pilot_pa.setter
    def led_pilot_pa(self, value):
        self._set_iio_debug_attr_str("led_pilot_pa", value)

    def get_led_range(self, led):
        """Get the full-scale current range of an LED driver.

        Args:
            led:
                LED number (1=green, 2=IR, 3=red).
        """
        return self._get_iio_debug_attr(f"led{led}_range")

    def set_led_range(self, led, value):
        """Set the full-scale current range of an LED driver.

        Args:
            led:
                LED number (1=green, 2=IR, 3=red).
            value:
                Range code (0=31mA, 1=62mA, 2=93mA, 3=124mA).
        """
        self._set_iio_debug_attr_str(f"led{led}_range", value)

    @property
    def prox_threshold(self):
        """Get/set proximity-mode entry threshold."""
        return self._get_iio_debug_attr("prox_threshold")

    @prox_threshold.setter
    def prox_threshold(self, value):
        self._set_iio_debug_attr_str("prox_threshold", value)

    @property
    def picket_fence_enable(self):
        """Get/set picket-fence detect-and-replace enable flag."""
        return self._get_iio_debug_attr("picket_fence_enable")

    @picket_fence_enable.setter
    def picket_fence_enable(self, value):
        self._set_iio_debug_attr_str("picket_fence_enable", value)

    @property
    def picket_fence_order(self):
        """Get/set picket-fence ordering flag."""
        return self._get_iio_debug_attr("picket_fence_order")

    @picket_fence_order.setter
    def picket_fence_order(self, value):
        self._set_iio_debug_attr_str("picket_fence_order", value)

    @property
    def picket_fence_iir_tc(self):
        """Get/set picket-fence IIR time-constant selection."""
        return self._get_iio_debug_attr("picket_fence_iir_tc")

    @picket_fence_iir_tc.setter
    def picket_fence_iir_tc(self, value):
        self._set_iio_debug_attr_str("picket_fence_iir_tc", value)

    @property
    def picket_fence_iir_init(self):
        """Get/set picket-fence IIR initialization value."""
        return self._get_iio_debug_attr("picket_fence_iir_init")

    @picket_fence_iir_init.setter
    def picket_fence_iir_init(self, value):
        self._set_iio_debug_attr_str("picket_fence_iir_init", value)

    @property
    def picket_fence_threshold_sigma(self):
        """Get/set picket-fence threshold sigma multiplier."""
        return self._get_iio_debug_attr("picket_fence_threshold_sigma")

    @picket_fence_threshold_sigma.setter
    def picket_fence_threshold_sigma(self, value):
        self._set_iio_debug_attr_str("picket_fence_threshold_sigma", value)

    @property
    def shutdown(self):
        """Get/set device shutdown (power-down) state."""
        return self._get_iio_debug_attr("shutdown")

    @shutdown.setter
    def shutdown(self, value):
        self._set_iio_debug_attr_str("shutdown", value)

    @property
    def low_power_mode(self):
        """Get/set low-power-mode enable flag (for <=256 sps)."""
        return self._get_iio_debug_attr("low_power_mode")

    @low_power_mode.setter
    def low_power_mode(self, value):
        self._set_iio_debug_attr_str("low_power_mode", value)

    @property
    def burst_enable(self):
        """Get/set burst-sampling enable flag."""
        return self._get_iio_debug_attr("burst_enable")

    @burst_enable.setter
    def burst_enable(self, value):
        self._set_iio_debug_attr_str("burst_enable", value)

    @property
    def burst_rate(self):
        """Get/set burst-sampling rate selection.

        0=8Hz, 1=32Hz, 2=84Hz, 3=256Hz.
        """
        return self._get_iio_debug_attr("burst_rate")

    @burst_rate.setter
    def burst_rate(self, value):
        self._set_iio_debug_attr_str("burst_rate", value)

    @property
    def buffer_enable(self):
        """Get/set data capture (exit/enter shutdown and reset buffer)."""
        return self._get_iio_debug_attr("buffer_enable")

    @buffer_enable.setter
    def buffer_enable(self, value):
        self._set_iio_debug_attr_str("buffer_enable", value)

    @property
    def part_id(self):
        """Get device part ID (read-only, hex string, expected 0x36)."""
        return self._get_iio_debug_attr_str("part_id")

    @property
    def rev_id(self):
        """Get device revision ID (read-only, hex string)."""
        return self._get_iio_debug_attr_str("rev_id")

    @property
    def interrupt_status(self):
        """Get combined 16-bit interrupt status (read-only, hex string)."""
        return self._get_iio_debug_attr_str("interrupt_status")

    @property
    def die_temperature(self):
        """Get die temperature in micro-degrees Celsius (read-only)."""
        return self._get_iio_debug_attr("die_temperature")
