# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import zlib
from ctypes import c_char_p, c_size_t, c_ssize_t, c_void_p
from enum import Enum
from pathlib import Path

import iio
import numpy as np

from adi.compatible import compatible
from adi.rx_tx import tx


class ad9910(tx, compatible):
    """Driver for AD9910 1 GSPS 14-Bit DDS with integrated DAC"""

    class reg(Enum):
        """AD9910 Register Enumeration"""

        CFR1 = 0x00
        CFR2 = 0x01
        CFR3 = 0x02
        AUX_DAC = 0x03
        IO_UPDATE_RATE = 0x04
        FTW = 0x07
        POW = 0x08
        ASF = 0x09
        MULTICHIP_SYNC = 0x0A
        DRG_LIMIT = 0x0B
        DRG_STEP = 0x0C
        DRG_RATE = 0x0D
        PROFILE0 = 0x0E
        PROFILE1 = 0x0F
        PROFILE2 = 0x10
        PROFILE3 = 0x11
        PROFILE4 = 0x12
        PROFILE5 = 0x13
        PROFILE6 = 0x14
        PROFILE7 = 0x15

    class destination(Enum):
        """AD9910 Destination Enumeration

        Matches the CFR1 RAM playback destination and CFR2 DRG destination
        field encodings.
        """

        FREQUENCY = 0
        PHASE = 1
        AMPLITUDE = 2
        POLAR = 3

    class channel(Enum):
        """AD9910 IIO Channel Enumeration"""

        PHY = "altcurrent100"
        PROFILE_0 = "altcurrent110"
        PROFILE_1 = "altcurrent111"
        PROFILE_2 = "altcurrent112"
        PROFILE_3 = "altcurrent113"
        PROFILE_4 = "altcurrent114"
        PROFILE_5 = "altcurrent115"
        PROFILE_6 = "altcurrent116"
        PROFILE_7 = "altcurrent117"
        PARALLEL_AMP = "altcurrent120"
        PARALLEL_PHASE = "phase120"
        PARALLEL_FREQ = "frequency120"
        PARALLEL_POLAR_AMP = "altcurrent121"
        PARALLEL_POLAR_PHASE = "phase121"
        DRG_FREQ = "frequency130"
        DRG_PHASE = "phase130"
        DRG_AMP = "altcurrent130"
        DRG_FREQ_RAMP_UP = "frequency131"
        DRG_FREQ_RAMP_DOWN = "frequency132"
        DRG_PHASE_RAMP_UP = "phase131"
        DRG_PHASE_RAMP_DOWN = "phase132"
        DRG_AMP_RAMP_UP = "altcurrent131"
        DRG_AMP_RAMP_DOWN = "altcurrent132"
        RAM = "altcurrent140"
        OSK = "altcurrent150"

    class scan_index(Enum):
        """AD9910 Parallel Port Scan Element Enumeration"""

        AMP = 0
        PHASE = 1
        FREQ = 2
        POLAR_AMP = 3
        POLAR_PHASE = 4

    NUM_PROFILES = 8
    RAM_SIZE_MAX_WORDS = 1024
    ASF_MAX = 0x3FFF
    compatible_parts = ["ad9910"]

    _RAM_FW_MAGIC = 0x00AD9910
    _RAM_FW_V1 = 0x0001

    _PROFILE_CHANNELS = [
        channel.PROFILE_0,
        channel.PROFILE_1,
        channel.PROFILE_2,
        channel.PROFILE_3,
        channel.PROFILE_4,
        channel.PROFILE_5,
        channel.PROFILE_6,
        channel.PROFILE_7,
    ]

    _freq_scale = 1.0

    class single_tone:
        """Single Tone Channel Class"""

        class profile:
            """Single Tone Profile Class"""

            def __init__(self, dds: "ad9910", channel: "ad9910.channel"):
                self._dds = dds
                if channel not in ad9910._PROFILE_CHANNELS:
                    raise Exception(f"invalid single tone profile channel: {channel}")
                self._channel = channel

            @property
            def enable(self):
                """Get/Set the enable state of this single tone profile"""
                return self._dds._get_iio_attr(self._channel, "en")

            @enable.setter
            def enable(self, value):
                self._dds._set_iio_attr(self._channel, "en", int(value))

            @property
            def frequency(self) -> float:
                """Get/Set the frequency of single tone profile in Hz"""
                freq = self._dds._get_iio_attr(self._channel, "frequency")
                return freq * self._dds._freq_scale

            @frequency.setter
            def frequency(self, value: float):
                freq = value / self._dds._freq_scale
                self._dds._set_iio_attr(self._channel, "frequency", freq)

            @property
            def phase(self) -> float:
                """Get/Set the phase of single tone profile in radians"""
                return self._dds._get_iio_attr(self._channel, "phase")

            @phase.setter
            def phase(self, value: float):
                self._dds._set_iio_attr(self._channel, "phase", value)

            @property
            def raw(self) -> int:
                """Get/Set the raw amplitude scale factor (ASF) code [0, 16383]"""
                return int(self._dds._get_iio_attr(self._channel, "raw"))

            @raw.setter
            def raw(self, value: int):
                self._dds._set_iio_attr(self._channel, "raw", int(value))

            @property
            def scale(self) -> float:
                """Get the amplitude scale of the DAC in mA per LSB

                This attribute is shared by all amplitude channels and derives
                from the full scale output current of the DAC.
                """
                return self._dds._get_iio_attr(self._channel, "scale")

            @property
            def amplitude(self) -> float:
                """Get/Set the amplitude of single tone profile in mA"""
                return self.raw * self.scale

            @amplitude.setter
            def amplitude(self, value: float):
                self.raw = int(min(round(value / self.scale), ad9910.ASF_MAX))

        def __init__(self, dds: "ad9910"):
            self._dds = dds
            self.profiles = [
                ad9910.single_tone.profile(dds, ch) for ch in ad9910._PROFILE_CHANNELS
            ]

        @property
        def frequency(self):
            """Get/Set the frequency of currently selected single tone profile in Hz"""
            return self.profiles[self._dds.profile].frequency

        @frequency.setter
        def frequency(self, value):
            self.profiles[self._dds.profile].frequency = value

        @property
        def phase(self):
            """Get/Set the phase of currently selected single tone profile in radians"""
            return self.profiles[self._dds.profile].phase

        @phase.setter
        def phase(self, value):
            self.profiles[self._dds.profile].phase = value

        @property
        def raw(self):
            """Get/Set the raw ASF code of the currently selected profile"""
            return self.profiles[self._dds.profile].raw

        @raw.setter
        def raw(self, value):
            self.profiles[self._dds.profile].raw = value

        @property
        def scale(self):
            """Get the amplitude scale in mA per LSB"""
            return self.profiles[self._dds.profile].scale

        @property
        def amplitude(self):
            """Get/Set the amplitude of the currently selected profile in mA"""
            return self.profiles[self._dds.profile].amplitude

        @amplitude.setter
        def amplitude(self, value):
            self.profiles[self._dds.profile].amplitude = value

    class parallel_data_port:
        """Parallel Port Channel Class"""

        def __init__(self, dds: "ad9910"):
            self._dds = dds

        @property
        def frequency_offset(self):
            """Get/Set the frequency offset of the Parallel Port channel

            The value is expressed in parallel port LSBs (i.e. in the same
            units as the transmitted samples) and it reflects the content of
            the FTW register. Multiply by ``frequency_scale`` to get Hz.
            """
            return self._dds._get_iio_attr(ad9910.channel.PARALLEL_FREQ, "offset")

        @frequency_offset.setter
        def frequency_offset(self, value):
            self._dds._set_iio_attr(ad9910.channel.PARALLEL_FREQ, "offset", value)

        @property
        def frequency_scale(self):
            """Get/Set the frequency scale of the Parallel Port channel in Hz per LSB

            The device implements this as a power of two gain (FM gain) applied
            to the transmitted samples, so the value written is rounded up to
            the closest supported setting. Read the attribute back to get the
            effective scale.
            """
            scale = self._dds._get_iio_attr(ad9910.channel.PARALLEL_FREQ, "scale")
            return scale * self._dds._freq_scale

        @frequency_scale.setter
        def frequency_scale(self, value):
            scale = value / self._dds._freq_scale
            self._dds._set_iio_attr(ad9910.channel.PARALLEL_FREQ, "scale", scale)

        @property
        def phase_scale(self):
            """Get the phase scale of the Parallel Port channel in radians per LSB"""
            return self._dds._get_iio_attr(ad9910.channel.PARALLEL_PHASE, "scale")

        @property
        def amplitude_scale(self):
            """Get the amplitude scale of the Parallel Port channel in mA per LSB"""
            return self._dds._get_iio_attr(ad9910.channel.PARALLEL_AMP, "scale")

        @property
        def polar_amplitude_offset(self):
            """Get/Set the amplitude offset of the Parallel Port polar channel

            The value is expressed in polar parallel port LSBs and reflects the
            content of the 6 LSBs of the ASF register, therefore it is a
            fractional sub-LSB offset in the [0.0, 1.0) range.
            """
            return self._dds._get_iio_attr(ad9910.channel.PARALLEL_POLAR_AMP, "offset")

        @polar_amplitude_offset.setter
        def polar_amplitude_offset(self, value):
            self._dds._set_iio_attr(ad9910.channel.PARALLEL_POLAR_AMP, "offset", value)

        @property
        def polar_amplitude_scale(self):
            """Get the amplitude scale of the Parallel Port polar channel in mA per LSB"""
            return self._dds._get_iio_attr(ad9910.channel.PARALLEL_POLAR_AMP, "scale")

        @property
        def polar_phase_offset(self):
            """Get/Set the phase offset of the Parallel Port polar channel

            The value is expressed in polar parallel port LSBs and reflects the
            content of the 8 LSBs of the POW register, therefore it is a
            fractional sub-LSB offset in the [0.0, 1.0) range.
            """
            return self._dds._get_iio_attr(
                ad9910.channel.PARALLEL_POLAR_PHASE, "offset"
            )

        @polar_phase_offset.setter
        def polar_phase_offset(self, value):
            self._dds._set_iio_attr(
                ad9910.channel.PARALLEL_POLAR_PHASE, "offset", value
            )

        @property
        def polar_phase_scale(self):
            """Get the phase scale of the Parallel Port polar channel in radians per LSB"""
            return self._dds._get_iio_attr(ad9910.channel.PARALLEL_POLAR_PHASE, "scale")

        @property
        def rate(self):
            """Get/Set the sampling frequency of the Parallel Port channel in Hz"""
            return self._dds._get_iio_attr(
                ad9910.channel.PARALLEL_FREQ, "sampling_frequency"
            )

        @rate.setter
        def rate(self, value):
            self._dds._set_iio_attr(
                ad9910.channel.PARALLEL_FREQ, "sampling_frequency", int(value)
            )

        def raw_push(self, data_np, cyclic=True):
            self._dds.tx_cyclic_buffer = cyclic
            self._dds.tx(data_np)

        def frequency_push(self, frequency_np, cyclic=True):
            """Push a numpy array of frequency values in Hz to the Parallel Port

            The frequency scale and offset are configured so that the whole
            frequency span fits into the 16-bit parallel port samples.
            """
            freq_min = np.min(frequency_np)
            freq_ptp = np.ptp(frequency_np)

            ch = self._dds._ctrl.find_channel(ad9910.channel.PARALLEL_FREQ.value, True)
            word_max = (1 << ch.data_format.bits) - 1

            self.frequency_scale = freq_ptp / word_max
            scale = self.frequency_scale

            self.frequency_offset = freq_min / scale
            offset = self.frequency_offset

            words = np.round(frequency_np / scale) - offset
            if np.max(words) > word_max:
                raise Exception("Could not resolve frequency scale")

            self._dds.tx_enabled_channels = [ad9910.scan_index.FREQ.value]
            self.raw_push(words.astype(np.uint16), cyclic)

    class output_shift_keying:
        """OSK Channel Class"""

        def __init__(self, dds: "ad9910"):
            self._dds = dds

        def _get_iio_attr(self, name):
            return self._dds._get_iio_attr(ad9910.channel.OSK, name)

        def _set_iio_attr(self, name, value):
            self._dds._set_iio_attr(ad9910.channel.OSK, name, value)

        @property
        def enable(self):
            """Get/Set the enable state of the OSK channel"""
            return self._get_iio_attr("en")

        @enable.setter
        def enable(self, value):
            self._set_iio_attr("en", int(value))

        @property
        def raw(self) -> int:
            """Get/Set the raw amplitude scale factor (ASF) code [0, 16383]"""
            return int(self._get_iio_attr("raw"))

        @raw.setter
        def raw(self, value: int):
            self._set_iio_attr("raw", int(value))

        @property
        def scale(self) -> float:
            """Get the amplitude scale of the DAC in mA per LSB"""
            return self._get_iio_attr("scale")

        @property
        def amplitude(self) -> float:
            """Get/Set the OSK amplitude in mA"""
            return self.raw * self.scale

        @amplitude.setter
        def amplitude(self, value: float):
            self.raw = round(value / self.scale)

        @property
        def raw_roc(self) -> float:
            """Get/Set the OSK rate of change in raw ASF codes per second

            The device only supports a discrete set of rates of change, see
            ``raw_roc_available``. The written value is rounded to the closest
            supported one. A rate of change of 0 puts OSK in manual mode with
            no pin control, while the maximum rate of change puts OSK in manual
            mode with pin control. Any other value selects automatic mode.
            """
            return self._get_iio_attr("raw_roc")

        @raw_roc.setter
        def raw_roc(self, value: float):
            self._set_iio_attr("raw_roc", int(value))

        @property
        def raw_roc_available(self):
            """Get the list of supported rates of change in raw ASF codes per second"""
            return self._get_iio_attr("raw_roc_available")

        @property
        def rate(self):
            """Get/Set the amplitude ramp rate of the OSK channel in Hz

            This is the frequency at which the amplitude scale factor is
            updated when OSK is in automatic mode.
            """
            return self._get_iio_attr("sampling_frequency")

        @rate.setter
        def rate(self, value):
            self._set_iio_attr("sampling_frequency", value)

    class digital_ramp_generator:
        """Digital Ramp Generator (DRG) Channel Class"""

        class mode(Enum):
            """DRG Operating Mode Enumeration Class"""

            BIDIRECTIONAL = "bidirectional"
            RAMP_DOWN = "ramp_down"
            RAMP_UP = "ramp_up"
            BIDIRECTIONAL_CONTINUOUS = "bidirectional_continuous"

        class ramp:
            """DRG Ramp Class"""

            def __init__(
                self,
                dds: "ad9910",
                chan: "ad9910.channel",
                rising_chan: "ad9910.channel",
                falling_chan: "ad9910.channel",
            ):
                self._dds = dds
                self._chan = chan
                self._rising_chan = rising_chan
                self._falling_chan = falling_chan
                if chan == ad9910.channel.DRG_FREQ:
                    self._dest = ad9910.destination.FREQUENCY
                elif chan == ad9910.channel.DRG_PHASE:
                    self._dest = ad9910.destination.PHASE
                else:
                    self._dest = ad9910.destination.AMPLITUDE

            @property
            def enable(self):
                """Get/Set the enable state of the DRG for this destination

                Writing 1 also selects this destination as the DRG destination.
                Writing 0 is a no-op if this is not the selected destination.
                """
                return self._dds._get_iio_attr(self._chan, "en")

            @enable.setter
            def enable(self, value):
                self._dds._set_iio_attr(self._chan, "en", int(value))

            @property
            def scale(self) -> float:
                """Get the scale of this destination in destination units per LSB

                Hz per LSB for frequency, radians per LSB for phase and mA per
                LSB for amplitude. The frequency scale, and with it the limits
                and the slopes derived from it, is expressed at system level.
                """
                scale = self._dds._get_iio_attr(self._chan, "scale")
                if self._dest == ad9910.destination.FREQUENCY:
                    scale *= self._dds._freq_scale

                return scale

            @property
            def raw_min(self) -> int:
                """Get/Set the lower ramp limit as a raw code"""
                return int(self._dds._get_iio_attr(self._falling_chan, "raw"))

            @raw_min.setter
            def raw_min(self, value: int):
                self._dds._set_iio_attr(self._falling_chan, "raw", int(value))

            @property
            def raw_max(self) -> int:
                """Get/Set the upper ramp limit as a raw code"""
                return int(self._dds._get_iio_attr(self._rising_chan, "raw"))

            @raw_max.setter
            def raw_max(self, value: int):
                self._dds._set_iio_attr(self._rising_chan, "raw", int(value))

            @property
            def min(self) -> float:
                """Get/Set the lower ramp limit in destination units"""
                return self.raw_min * self.scale

            @min.setter
            def min(self, value: float):
                self.raw_min = round(value / self.scale)

            @property
            def max(self) -> float:
                """Get/Set the upper ramp limit in destination units"""
                return self.raw_max * self.scale

            @max.setter
            def max(self, value: float):
                self.raw_max = round(value / self.scale)

            @property
            def positive_slope(self) -> float:
                """Get/Set the positive slope in destination units per second

                Hz/s for frequency, rad/s for phase and mA/s for amplitude.
                """
                roc = self._dds._get_iio_attr(self._rising_chan, "raw_roc")
                return roc * self.scale

            @positive_slope.setter
            def positive_slope(self, value: float):
                roc = int(round(value / self.scale))
                self._dds._set_iio_attr(self._rising_chan, "raw_roc", roc)

            @property
            def negative_slope(self) -> float:
                """Get/Set the negative slope in destination units per second

                Hz/s for frequency, rad/s for phase and mA/s for amplitude.
                """
                roc = self._dds._get_iio_attr(self._falling_chan, "raw_roc")
                return roc * self.scale

            @negative_slope.setter
            def negative_slope(self, value: float):
                roc = int(round(value / self.scale))
                self._dds._set_iio_attr(self._falling_chan, "raw_roc", roc)

            @property
            def positive_slope_time(self) -> float:
                """Get/Set the time to sweep the whole ramp range upwards in seconds

                This is derived from the ramp limits and the positive slope, so
                the limits have to be configured before setting it. Setting it
                to 0 selects the steepest slope, i.e. a single step at the
                current increment rate.
                """
                span = self.max - self.min
                slope = self.positive_slope
                return span / slope if slope > 0 else 0.0

            @positive_slope_time.setter
            def positive_slope_time(self, value: float):
                span = self.max - self.min
                if value > 0:
                    self.positive_slope = span / value
                else:
                    self.positive_slope = span * self.positive_slope_rate

            @property
            def negative_slope_time(self) -> float:
                """Get/Set the time to sweep the whole ramp range downwards in seconds

                This is derived from the ramp limits and the negative slope, so
                the limits have to be configured before setting it. Setting it
                to 0 selects the steepest slope, i.e. a single step at the
                current decrement rate.
                """
                span = self.max - self.min
                slope = self.negative_slope
                return span / slope if slope > 0 else 0.0

            @negative_slope_time.setter
            def negative_slope_time(self, value: float):
                span = self.max - self.min
                if value > 0:
                    self.negative_slope = span / value
                else:
                    self.negative_slope = span * self.negative_slope_rate

            @property
            def positive_slope_rate(self) -> float:
                """Get/Set the rate at which the ramp is incremented in Hz"""
                return self._dds._get_iio_attr(self._rising_chan, "sampling_frequency")

            @positive_slope_rate.setter
            def positive_slope_rate(self, value: float):
                self._dds._set_iio_attr(self._rising_chan, "sampling_frequency", value)

            @property
            def negative_slope_rate(self) -> float:
                """Get/Set the rate at which the ramp is decremented in Hz"""
                return self._dds._get_iio_attr(self._falling_chan, "sampling_frequency")

            @negative_slope_rate.setter
            def negative_slope_rate(self, value: float):
                self._dds._set_iio_attr(self._falling_chan, "sampling_frequency", value)

            @property
            def positive_ctl_time(self) -> float:
                """Get/Set the duration of the positive direction control in seconds"""
                return self._dds._get_iio_attr(self._rising_chan, "integration_time")

            @positive_ctl_time.setter
            def positive_ctl_time(self, value: float):
                self._dds._set_iio_attr(self._rising_chan, "integration_time", value)

            @property
            def negative_ctl_time(self) -> float:
                """Get/Set the duration of the negative direction control in seconds"""
                return self._dds._get_iio_attr(self._falling_chan, "integration_time")

            @negative_ctl_time.setter
            def negative_ctl_time(self, value: float):
                self._dds._set_iio_attr(self._falling_chan, "integration_time", value)

            @property
            def no_dwell_high(self):
                """Get/Set whether the ramp dwells at the upper limit"""
                return not bool(self._dds._get_iio_attr(self._rising_chan, "dwell_en"))

            @no_dwell_high.setter
            def no_dwell_high(self, value: bool):
                self._dds._set_iio_attr(self._rising_chan, "dwell_en", int(not value))

            @property
            def no_dwell_low(self):
                """Get/Set whether the ramp dwells at the lower limit"""
                return not bool(self._dds._get_iio_attr(self._falling_chan, "dwell_en"))

            @no_dwell_low.setter
            def no_dwell_low(self, value: bool):
                self._dds._set_iio_attr(self._falling_chan, "dwell_en", int(not value))

            @property
            def operating_mode(self) -> "ad9910.digital_ramp_generator.mode":
                """Get/Set the operating mode of the ramp"""
                ndh = self.no_dwell_high
                ndl = self.no_dwell_low

                if not ndh and not ndl:
                    return ad9910.digital_ramp_generator.mode.BIDIRECTIONAL
                elif not ndh and ndl:
                    return ad9910.digital_ramp_generator.mode.RAMP_DOWN
                elif ndh and not ndl:
                    return ad9910.digital_ramp_generator.mode.RAMP_UP
                else:
                    return ad9910.digital_ramp_generator.mode.BIDIRECTIONAL_CONTINUOUS

            @operating_mode.setter
            def operating_mode(self, mode: "ad9910.digital_ramp_generator.mode"):
                modes = ad9910.digital_ramp_generator.mode
                self.no_dwell_high = mode in (modes.BIDIRECTIONAL_CONTINUOUS, modes.RAMP_UP)
                self.no_dwell_low = mode in (modes.BIDIRECTIONAL_CONTINUOUS, modes.RAMP_DOWN)

            def __repr__(self):
                return (
                    f"DRG {self._dest.name.lower()}: min={self.min}, max={self.max}, "
                    f"slope=[{self.positive_slope}, {self.negative_slope}]"
                )

        def __init__(self, dds: "ad9910"):
            self._dds = dds
            self.frequency = ad9910.digital_ramp_generator.ramp(
                dds,
                ad9910.channel.DRG_FREQ,
                ad9910.channel.DRG_FREQ_RAMP_UP,
                ad9910.channel.DRG_FREQ_RAMP_DOWN,
            )
            self.phase = ad9910.digital_ramp_generator.ramp(
                dds,
                ad9910.channel.DRG_PHASE,
                ad9910.channel.DRG_PHASE_RAMP_UP,
                ad9910.channel.DRG_PHASE_RAMP_DOWN,
            )
            self.amplitude = ad9910.digital_ramp_generator.ramp(
                dds,
                ad9910.channel.DRG_AMP,
                ad9910.channel.DRG_AMP_RAMP_UP,
                ad9910.channel.DRG_AMP_RAMP_DOWN,
            )
            self._ramps = {
                ad9910.destination.FREQUENCY: self.frequency,
                ad9910.destination.PHASE: self.phase,
                ad9910.destination.AMPLITUDE: self.amplitude,
            }
            self._dest = ad9910.destination.FREQUENCY

        @property
        def active_ramp(self) -> "ad9910.digital_ramp_generator.ramp":
            """Get the active ramp control"""
            return self._ramps[self._dest]

        def enable(self, destination: "ad9910.destination"):
            """Set the enable state of the DRG on the selected destination"""
            self._dest = destination
            self.active_ramp.enable = 1

        def disable(self):
            """Disable the DRG"""
            self.active_ramp.enable = 0

        @property
        def operating_mode(self) -> "ad9910.digital_ramp_generator.mode":
            """Get/Set the operating mode of the DRG"""
            return self.active_ramp.operating_mode

        @operating_mode.setter
        def operating_mode(self, mode: "ad9910.digital_ramp_generator.mode"):
            self.active_ramp.operating_mode = mode

    class ram_control:
        """RAM Control Channel Class"""

        class mode(Enum):
            """RAM Control Operating Mode Enumeration"""

            DIRECT_SWITCH = 0
            RAMP_UP = 1
            BIDIRECTIONAL = 2
            BIDIRECTIONAL_CONTINUOUS = 3
            RAMP_UP_CONTINUOUS = 4

        class profile:
            """RAM Profile Class

            RAM profile settings are staged locally and only applied to the
            device as part of the RAM firmware image, see
            :meth:`ad9910.ram_control.config_load`.
            """

            def __init__(self, dds: "ad9910", profile: int):
                self._dds = dds
                self._profile = profile
                self._rate_val = 1
                self._start = 0
                self._end = ad9910.RAM_SIZE_MAX_WORDS - 1
                self._mode = ad9910.ram_control.mode.RAMP_UP_CONTINUOUS
                self._no_dwell_high = False
                self._zero_crossing = False

            @property
            def rate(self) -> float:
                """Get/Set RAM profile sampling frequency in Hz"""
                return (self._dds.sysclk_frequency / 4) / self._rate_val

            @rate.setter
            def rate(self, value: float):
                round_val = round((self._dds.sysclk_frequency / 4) / value)
                self._rate_val = max(1, min(round_val, 0xFFFF))

            @property
            def address_range(self):
                """Get/Set RAM profile address range"""
                return (self._start, self._end)

            @address_range.setter
            def address_range(self, value):
                if not isinstance(value, tuple) or len(value) != 2:
                    raise ValueError("Value must be a tuple of length 2")
                if (
                    value[0] < 0
                    or value[1] >= ad9910.RAM_SIZE_MAX_WORDS
                    or value[0] > value[1]
                ):
                    raise ValueError("Invalid address range")
                self._start = value[0]
                self._end = value[1]

            @property
            def operating_mode(self) -> "ad9910.ram_control.mode":
                """Get/Set RAM profile operating mode"""
                return self._mode

            @operating_mode.setter
            def operating_mode(self, mode: "ad9910.ram_control.mode"):
                self._mode = mode

            @property
            def no_dwell_high(self) -> bool:
                """Get/Set RAM profile no-dwell-high behavior

                When set, the RAM playback returns to the start address instead
                of holding the last word at the end of the address range.
                """
                return self._no_dwell_high

            @no_dwell_high.setter
            def no_dwell_high(self, value: bool):
                self._no_dwell_high = bool(value)

            @property
            def zero_crossing(self) -> bool:
                """Get/Set RAM profile zero-crossing behavior"""
                return self._zero_crossing

            @zero_crossing.setter
            def zero_crossing(self, value: bool):
                self._zero_crossing = bool(value)

            def to_word(self) -> int:
                """Pack the profile settings into its 64-bit register value"""
                word = self._mode.value & 0x7
                word |= int(self._zero_crossing) << 3
                word |= int(self._no_dwell_high) << 5
                word |= (self._start & 0x3FF) << 14
                word |= (self._end & 0x3FF) << 30
                word |= (self._rate_val & 0xFFFF) << 40
                return word

            def from_word(self, word: int):
                """Unpack the profile settings from its 64-bit register value"""
                self._mode = ad9910.ram_control.mode(word & 0x7)
                self._zero_crossing = bool((word >> 3) & 0x1)
                self._no_dwell_high = bool((word >> 5) & 0x1)
                self._start = (word >> 14) & 0x3FF
                self._end = (word >> 30) & 0x3FF
                self._rate_val = (word >> 40) & 0xFFFF

        def __init__(self, dds: "ad9910"):
            """Constructor for RAM Control Channel"""
            self._dds = dds
            self.profiles = [
                ad9910.ram_control.profile(dds, p) for p in range(ad9910.NUM_PROFILES)
            ]
            self._dest = ad9910.destination.FREQUENCY
            self._profile_ctl = 0

        @property
        def enable(self):
            """Get/Set RAM enable"""
            return self._dds._get_iio_attr(ad9910.channel.RAM, "en")

        @enable.setter
        def enable(self, value):
            self._dds._set_iio_attr(ad9910.channel.RAM, "en", int(value))

        @property
        def dest(self) -> "ad9910.destination":
            """Get/Set RAM destination mode. One of 'frequency', 'phase', 'amplitude', 'polar'

            The destination is staged locally and only applied to the device as
            part of the RAM firmware image.
            """
            return self._dest

        @dest.setter
        def dest(self, dest: "ad9910.destination"):
            self._dest = dest

        @property
        def frequency(self):
            """
            Get/Set frequency of the signal when in RAM mode.

            The value reflects content of the FTW register, so it is only effective
            when the RAM destination is NOT set to 'frequency'.
            """
            freq = self._dds._get_iio_attr(ad9910.channel.RAM, "frequency")
            return freq * self._dds._freq_scale

        @frequency.setter
        def frequency(self, value):
            freq = value / self._dds._freq_scale
            self._dds._set_iio_attr(ad9910.channel.RAM, "frequency", freq)

        @property
        def phase(self) -> float:
            """
            Get/Set phase of the signal in radians when in RAM mode.

            The value reflects content of the POW register, so it is only effective
            when the RAM destination is NOT set to phase or polar.
            """
            return self._dds._get_iio_attr(ad9910.channel.RAM, "phase")

        @phase.setter
        def phase(self, value: float):
            self._dds._set_iio_attr(ad9910.channel.RAM, "phase", value)

        @property
        def rate(self):
            """Get/Set the RAM playback rate of the active profile in Hz"""
            return self._dds._get_iio_attr(ad9910.channel.RAM, "sampling_frequency")

        @rate.setter
        def rate(self, value):
            self._dds._set_iio_attr(ad9910.channel.RAM, "sampling_frequency", value)

        def profile_control(self, profile=0, continuous=True):
            """Configure the RAM Internal Profile Control

            :param profile: RAM Internal Profile Control Target. 0 means that
                            internal profile control is disabled and the RAM
                            mode is controlled by the selected profile mode.
            :param continuous: Whether to enable continuous mode for the selected profile.
            """
            if profile < 0 or profile >= ad9910.NUM_PROFILES:
                raise ValueError(f"Invalid profile number: {profile}")

            if profile == 0:
                self._profile_ctl = 0
            else:
                self._profile_ctl = profile
                if continuous:
                    self._profile_ctl = (self._profile_ctl - 1) | 0x1000

        def firmware_load(self, data: bytes, load_config=False):
            """Load firmware data into RAM FW interface

            :param data: Firmware data bytes.
            :param load_config: Whether to parse RAM profile configuration from
                                the firmware data and apply it. If False, the
                                firmware data is loaded as-is without applying
                                any configuration.
            """
            header_len = ad9910.ram_control._FW_HEADER_LEN

            if load_config:
                # parse config from fw data and apply settings
                if len(data) < header_len:
                    raise ValueError("Invalid firmware data length")
                cfr1 = int.from_bytes(data[12:16], byteorder="big")
                self._dest = ad9910.destination((cfr1 >> 29) & 0x3)
                self._profile_ctl = (cfr1 >> 17) & 0xF

                for p in range(ad9910.NUM_PROFILES):
                    p_start = 16 + p * 8
                    p_end = p_start + 8
                    self.profiles[p].from_word(
                        int.from_bytes(data[p_start:p_end], byteorder="big")
                    )

            # the device rejects RAM writes while RAM playback is enabled
            if self.enable:
                self.enable = 0

            # at this point libiio does not handle firmware upload through
            # /sys/class/firmware interface. If running locally, we try to use
            # the sysfs directly (permissions apply). Otherwise, we fallback to
            # using debug attributes, which can be accessed remotely or locally
            # by libiio.
            ram_loading = Path(f"/sys/class/firmware/{self._dds._ctrl._id}:ram/loading")
            ram_data = Path(f"/sys/class/firmware/{self._dds._ctrl._id}:ram/data")
            if ram_loading.exists() and ram_data.exists():
                ram_loading.write_text("1")
                ram_data.write_bytes(data)
                ram_loading.write_text("0")
            else:
                # fallback to debug attributes
                _d_write_dbg_attr_raw = iio._lib.iio_device_debug_attr_write_raw
                _d_write_dbg_attr_raw.restype = c_ssize_t
                _d_write_dbg_attr_raw.argtypes = (
                    iio._DevicePtr,
                    c_char_p,
                    c_void_p,
                    c_size_t,
                )
                _d_write_dbg_attr_raw.errcheck = iio._check_negative

                self._dds._set_iio_debug_attr_str("ram_loading", 1, self._dds._ctrl)
                data_p = c_char_p(data)
                attr_encode = "ram_data".encode("ascii")
                _d_write_dbg_attr_raw(
                    self._dds._ctrl._device, attr_encode, data_p, len(data)
                )
                self._dds._set_iio_debug_attr_str("ram_loading", 0, self._dds._ctrl)

        def config_load(self, data: bytes = None, filename: Path = None):
            """Load configuration and data into RAM

            Builds a version 1 RAM firmware image out of the staged RAM
            configuration and the given data words, and uploads it to the
            device.

            :param data: RAM data bytes in big-endian order. Length must be a
                         multiple of 4 and must not exceed 4096 bytes.
            :param filename: Optional file path to save the RAM fw data.
            """
            length = 0

            if data is not None:
                length = len(data)
                if length % 4 != 0 or length > ad9910.RAM_SIZE_MAX_WORDS * 4:
                    raise Exception(f"invalid RAM data length: {length}")

            wcount = length // 4
            cfr1 = self._dest.value << 29 | (self._profile_ctl & 0xF) << 17

            # the CRC covers everything from cfr1 onwards
            payload = cfr1.to_bytes(4, byteorder="big")
            for profile in self.profiles:
                payload += profile.to_word().to_bytes(8, byteorder="big")
            if data is not None:
                # convert data to big-endian bytes and reverse
                data = np.flip(data).astype(np.dtype(">u4")).tobytes()
                payload += data

            fw_data = ad9910._RAM_FW_MAGIC.to_bytes(4, byteorder="big")
            fw_data += ad9910._RAM_FW_V1.to_bytes(2, byteorder="big")
            fw_data += wcount.to_bytes(2, byteorder="big")
            crc = zlib.crc32(payload, 0xFFFFFFFF) ^ 0xFFFFFFFF
            fw_data += crc.to_bytes(4, byteorder="big")
            fw_data += payload

            if filename is not None:
                with open(filename, "wb") as f:
                    f.write(fw_data)

            self.firmware_load(fw_data, False)

        def file_load(self, file):
            """Load RAM FW data from binary file"""
            with open(file, "rb") as f:
                self.firmware_load(f.read(), True)

        def frequency_load(self, frequency_np, filename: Path = None):
            """Load frequency numpy array (in Hz) into RAM"""
            self._dest = ad9910.destination.FREQUENCY
            frequency_np = np.asarray(frequency_np) / self._dds._freq_scale
            data = np.round((frequency_np * (1 << 32)) / self._dds.sysclk_frequency)
            self.config_load(data, filename)

        def phase_deg_load(self, phase_np, filename: Path = None):
            """Load phase numpy array (in degrees) into RAM"""
            self._dest = ad9910.destination.PHASE
            data = (phase_np % 360) * (1 << 16) / 360
            data = np.minimum(np.round(data), 0xFFFF).astype(np.uint32)
            data <<= 16
            self.config_load(data, filename)

        def phase_rad_load(self, phase_np, filename: Path = None):
            """Load phase numpy array (in radians) into RAM"""
            self._dest = ad9910.destination.PHASE
            data = (phase_np * (1 << 15)) / np.pi
            data = np.minimum(np.round(data), 0xFFFF).astype(np.uint32)
            data <<= 16
            self.config_load(data, filename)

        def amplitude_load(self, amplitude_np, filename: Path = None):
            """Load amplitude numpy array (in mA) into RAM

            Amplitudes are clamped to the DAC full scale output current, see
            ``dac_full_scale_current``.
            """
            self._dest = ad9910.destination.AMPLITUDE
            data = amplitude_np / self._dds.dac_scale
            data = np.minimum(np.round(data), ad9910.ASF_MAX).astype(np.uint32)
            data <<= 18
            self.config_load(data, filename)

        def polar_load(self, complex_np, filename: Path = None):
            """
            Loads numpy array of complex numbers into RAM using polar coordinates.
            Element magnitudes are amplitudes in mA, clamped to the DAC full
            scale output current, see ``dac_full_scale_current``.
            """
            self._dest = ad9910.destination.POLAR
            amplitude_np = np.abs(complex_np) / self._dds.dac_scale
            amplitude_np = np.minimum(np.round(amplitude_np), ad9910.ASF_MAX).astype(
                np.uint32
            )
            phase_np = (np.angle(complex_np) * (1 << 15)) / np.pi
            phase_np = np.minimum(np.round(phase_np), 0xFFFF).astype(np.uint32)
            data = phase_np << 16 | amplitude_np << 2
            self.config_load(data, filename)

        @staticmethod
        def extend_pattern(pattern, length=1024):
            """
            Extend a given pattern to a specified length by repeating it.

            :param pattern: The input pattern to extend.
            :param length: The desired total length of the output pattern.
            :return: The extended pattern.
            """
            pattern_length = len(pattern)
            if pattern_length == 0:
                raise Exception("pattern length cannot be zero")
            repeats = length // pattern_length
            remainder = length % pattern_length
            return pattern * repeats + pattern[:remainder]

        # magic + version + wcount + crc + cfr1 + 8 profiles
        _FW_HEADER_LEN = 4 + 2 + 2 + 4 + 4 + 8 * 8

    def __init__(self, uri="", device_name=""):
        """
        Constructor for the AD9910 class.

        :param uri: URI string for the IIO context
        :param device_name: name, label or ID of the AD9910 device
        """
        compatible.__init__(self, uri, device_name)

        self.st = ad9910.single_tone(self)
        self.osk = ad9910.output_shift_keying(self)
        self.drg = ad9910.digital_ramp_generator(self)
        self.ram = ad9910.ram_control(self)
        self.parallel_port = ad9910.parallel_data_port(self)

        self._profile = ad9910.NUM_PROFILES
        self.profile = 0

        self._txdac = self._ctrl
        self._tx_channel_names = [
            ad9910.channel.PARALLEL_AMP.value,
            ad9910.channel.PARALLEL_PHASE.value,
            ad9910.channel.PARALLEL_FREQ.value,
            ad9910.channel.PARALLEL_POLAR_AMP.value,
            ad9910.channel.PARALLEL_POLAR_PHASE.value,
        ]
        tx.__init__(self)

    def disable_dds(self):
        pass  # peripheral has no FPGA DDS core

    def _get_iio_attr(self, channel: "ad9910.channel", name: str):
        return super()._get_iio_attr(channel.value, name, True, self._ctrl)

    def _set_iio_attr(self, channel: "ad9910.channel", name: str, value):
        if isinstance(value, float):
            value = format(value, ".12f")  # avoid scientific notation
        super()._set_iio_attr(channel.value, name, True, value, self._ctrl)

    @property
    def profile(self):
        """Get/Set the current active profile"""
        return self._profile

    @profile.setter
    def profile(self, value):
        value = int(value)
        if value < 0 or value >= ad9910.NUM_PROFILES:
            raise Exception(f"invalid profile: {value}")
        if self._profile != value:
            self.st.profiles[value].enable = 1
            self._profile = value

    @property
    def powerdown(self):
        """Get/Set the software power-down state of the DDS core"""
        return self._get_iio_attr(ad9910.channel.PHY, "powerdown")

    @powerdown.setter
    def powerdown(self, value):
        self._set_iio_attr(ad9910.channel.PHY, "powerdown", int(value))

    @property
    def sysclk_frequency(self):
        """Get/Set the system clock frequency in Hz

        This property can be set as a multiple of the input reference clock
        frequency if the PLL is enabled in the device-tree, otherwise it can
        only be used to bypass (default) or not the input reference divider.
        """
        return self._get_iio_attr(ad9910.channel.PHY, "sampling_frequency")

    @sysclk_frequency.setter
    def sysclk_frequency(self, value):
        self._set_iio_attr(ad9910.channel.PHY, "sampling_frequency", int(value))

    @property
    def dac_scale(self):
        """Get/Set the DAC amplitude scale in mA per LSB

        This is derived from the full scale output current of the DAC and it is
        shared by all amplitude channels.
        """
        return self._get_iio_attr(ad9910.channel.PHY, "scale")

    @dac_scale.setter
    def dac_scale(self, value):
        self._set_iio_attr(ad9910.channel.PHY, "scale", value)

    @property
    def dac_full_scale_current(self):
        """Get/Set the DAC full scale output current in mA"""
        return self.dac_scale * (ad9910.ASF_MAX + 1)

    @dac_full_scale_current.setter
    def dac_full_scale_current(self, value):
        self.dac_scale = value / (ad9910.ASF_MAX + 1)

    def reg_read(self, reg: "ad9910.reg"):
        """Direct Register Read Access via debugfs"""
        backup_profile = None

        if (
            reg.value >= ad9910.reg.PROFILE0.value
            and reg.value <= ad9910.reg.PROFILE7.value
        ):
            backup_profile = self._profile
            self.profile = reg.value - ad9910.reg.PROFILE0.value

        self._set_iio_debug_attr_str("direct_reg_access", reg.value, self._ctrl)
        val = int(self._get_iio_debug_attr_str("direct_reg_access", self._ctrl), 0)

        if backup_profile is not None:
            # restore profile after reading register value
            self.profile = backup_profile

        return val

    def reg_write(self, reg: "ad9910.reg", value):
        """Direct Register Write Access via debugfs"""
        self._set_iio_debug_attr_str(
            "direct_reg_access", f"{reg.value} {value}", self._ctrl
        )
