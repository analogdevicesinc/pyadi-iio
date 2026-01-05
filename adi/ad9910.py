# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from ctypes import c_char_p, c_size_t, c_ssize_t, c_void_p
from enum import Enum
from functools import wraps
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
        """AD9910 Destination Enumeration"""

        FREQUENCY = 0
        AMPLITUDE = 1
        PHASE = 2
        POLAR = 3

    class channel(Enum):
        """AD9910 Channel Enumeration"""

        PHY = "altvoltage100"
        PROFILE_0 = "altvoltage101"
        PROFILE_1 = "altvoltage102"
        PROFILE_2 = "altvoltage103"
        PROFILE_3 = "altvoltage104"
        PROFILE_4 = "altvoltage105"
        PROFILE_5 = "altvoltage106"
        PROFILE_6 = "altvoltage107"
        PROFILE_7 = "altvoltage108"
        PARALLEL_PORT = "altvoltage110"
        DRG = "altvoltage120"
        DRG_RAMP_UP = "altvoltage121"
        DRG_RAMP_DOWN = "altvoltage122"
        RAM = "altvoltage130"
        OSK = "altvoltage140"

    NUM_PROFILES = 8
    compatible_parts = ["ad9910"]

    _REG64 = [
        reg.DRG_LIMIT,
        reg.DRG_STEP,
        reg.PROFILE0,
        reg.PROFILE1,
        reg.PROFILE2,
        reg.PROFILE3,
        reg.PROFILE4,
        reg.PROFILE5,
        reg.PROFILE6,
        reg.PROFILE7,
    ]

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
            def frequency(self) -> float:
                """Get/Set the frequency of single tone profile in Hz"""
                return self._dds._get_iio_attr(self._channel, "frequency")

            @frequency.setter
            def frequency(self, value: float):
                self._dds._set_iio_attr(self._channel, "frequency", value)

            @property
            def scale(self) -> float:
                """Get/Set the amplitude scale of single tone profile"""
                return self._dds._get_iio_attr(self._channel, "scale")

            @scale.setter
            def scale(self, value: float):
                self._dds._set_iio_attr(self._channel, "scale", value)

            @property
            def phase(self) -> float:
                """Get/Set the phase of single tone profile in radians"""
                return self._dds._get_iio_attr(self._channel, "phase")

            @phase.setter
            def phase(self, value: float):
                self._dds._set_iio_attr(self._channel, "phase", value)

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
        def scale(self):
            """Get/Set the amplitude scale of currently selected single tone profile"""
            return self.profiles[self._dds.profile].scale

        @scale.setter
        def scale(self, value):
            self.profiles[self._dds.profile].scale = value

        @property
        def phase(self):
            """Get/Set the phase of currently selected single tone profile in radians"""
            return self.profiles[self._dds.profile].phase

        @phase.setter
        def phase(self, value):
            self.profiles[self._dds.profile].phase = value

    class parallel_data_port:
        """Parallel Port Channel Class"""

        class format(Enum):
            """Parallel Port Data Format Enumeration"""

            FREQUENCY = 0x20000
            PHASE = 0x10000
            AMPLITUDE = 0x00000
            POLAR = 0x30000

        def __init__(self, dds: "ad9910"):
            self._dds = dds

        def _get_iio_attr(self, name):
            return self._dds._get_iio_attr(ad9910.channel.PARALLEL_PORT, name)

        def _set_iio_attr(self, name, value):
            self._dds._set_iio_attr(ad9910.channel.PARALLEL_PORT, name, value)

        @property
        def enable(self):
            """Get/Set the enable state of the Parallel Port channel"""
            return self._get_iio_attr("en")

        @enable.setter
        def enable(self, value):
            self._set_iio_attr("en", value)

        @property
        def frequency_offset(self):
            """Get/Set the frequency offset of the Parallel Port channel in Hz

            The value reflects content of the FTW register. The actual frequency
            output of the DDS core when the Parallel Port channel is enabled and
            its destination is set to frequency is given by:

                f_out = f_ftw + f_scale * f_pp

            where:
                - f_ftw is the frequency represented by the frequency_offset attribute
                - f_scale is the frequency_scale attribute
                - f_pp is the frequency value transmitted through the Parallel Port
            """
            return self._get_iio_attr("frequency_offset")

        @frequency_offset.setter
        def frequency_offset(self, value):
            self._set_iio_attr("frequency_offset", value)

        @property
        def frequency_scale(self):
            """Get/Set the frequency scale of the Parallel Port channel

            This value must be a power of 2 and it is a scaling factor applied
            to the transmitted frequency. The actual frequency output of the DDS
            core when the Parallel Port channel is enabled and its destination
            is set to frequency is given by:

                f_out = f_ftw + f_scale * f_pp

            where:
                - f_ftw is the frequency represented by the frequency_offset attribute
                - f_scale is the frequency_scale attribute
                - f_pp is the frequency value transmitted through the Parallel Port
            """
            return self._get_iio_attr("frequency_scale")

        @frequency_scale.setter
        def frequency_scale(self, value):
            self._set_iio_attr("frequency_scale", value)

        @property
        def phase_offset(self):
            """Get/Set the phase offset of the Parallel Port channel in radians

            The value reflects content of the 8 LSB bits POW register.
            This is only applicable when the destination of the Parallel Port
            channel is set to Polar. The actual phase output of the DDS core
            when the Parallel Port channel is enabled and its destination is set
            to Polar is given by:

                phi_out = phi_pow + (phi_pp << 8)

            where:
                - phi_pow is the phase represented by the phase_offset attribute
                - phi_pp is the 8-bit phase value transmitted through the Parallel Port
            """
            return self._get_iio_attr("phase_offset")

        @phase_offset.setter
        def phase_offset(self, value):
            self._set_iio_attr("phase_offset", value)

        @property
        def scale_offset(self):
            """Get/Set the scale offset of the Parallel Port channel

            The value reflects content of the 6 LSB bits of the ASF register.
            This is only applicable when the destination of the Parallel Port
            channel is set to Polar. The actual amplitude output of the DDS core
            when the Parallel Port channel is enabled and its destination is set
            to Polar is given by:

                A_out = A_asf + (A_pp << 6)

            where:
                - A_asf is the amplitude represented by the scale_offset attribute
                - A_pp is the 8-bit amplitude value transmitted through the Parallel Port
            """
            return self._get_iio_attr("scale_offset")

        @scale_offset.setter
        def scale_offset(self, value):
            self._set_iio_attr("scale_offset", value)

        @property
        def rate(self):
            """Get/Set the sampling frequency of the Parallel Port channel in Hz

            Note: The device does not configure a sampling frequency for the
            Parallel Port channel. This attribute is normally brought by the
            IIO Backend driver.
            """
            return self._get_iio_attr("sampling_frequency")

        @rate.setter
        def rate(self, value):
            self._set_iio_attr("sampling_frequency", value)

        def raw_push(self, data_np, cyclic=True):
            self._dds.tx_enabled_channels = [0]
            self._dds.tx_cyclic_buffer = cyclic
            self._dds.tx(data_np)

        def frequency_push(self, frequency_np, cyclic=True):
            hz_to_word = (1 << 32) / self._dds.sysclk_frequency
            freq_min = np.min(frequency_np)
            freq_ptp = np.ptp(frequency_np)

            # compute required frequency scale to fit frequency values into 16 bits
            if freq_ptp > 1e-6:
                freq_shift = np.ceil(np.log2((freq_ptp * hz_to_word) / 2 ** 16))
                if freq_shift < 0:
                    freq_shift = 0
                elif freq_shift > 15:
                    raise Exception("Could not resolve frequency scale")
                freq_scale = int(2 ** freq_shift)
            else:
                freq_scale = 1

            freq_word_np = (frequency_np - freq_min) * hz_to_word / freq_scale
            freq_word_np = np.round(freq_word_np).astype(np.uint32)
            freq_word_np |= ad9910.parallel_data_port.format.FREQUENCY.value

            # update attributes
            self.frequency_scale = freq_scale
            self.frequency_offset = freq_min

            # push words to parallel port
            self.raw_push(freq_word_np, cyclic)

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
            self._set_iio_attr("en", value)

        @property
        def scale(self):
            """Get/Set the amplitude scale [0.0, 1.0) of the OSK channel"""
            return self._get_iio_attr("scale")

        @scale.setter
        def scale(self, value):
            self._set_iio_attr("scale", value)

        @property
        def pinctrl_enable(self):
            """
            Get/Set the OSK pin control state when OSK is in manual mode
            """
            return self._get_iio_attr("pinctrl_en")

        @pinctrl_enable.setter
        def pinctrl_enable(self, value):
            self._set_iio_attr("pinctrl_en", value)

        @property
        def step(self):
            """Get/Set the scale increment step of the OSK channel.
            if step is set to 0, OSK is in manual mode, otherwise it is in automatic mode.
            """
            return self._get_iio_attr("scale_step")

        @step.setter
        def step(self, value):
            self._set_iio_attr("scale_step", value)

        @property
        def rate(self):
            """Get/Set the sampling frequency (step rate) of the OSK channel"""
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

        class range:
            """DRG Range"""

            def __init__(self, dds: "ad9910", range_name):
                self._dds = dds
                self._range_name = range_name

            @property
            def min(self) -> float:
                """Get/Set the minimum value of the DRG range"""
                return self._dds._get_iio_attr(
                    ad9910.channel.DRG_RAMP_DOWN, self._range_name
                )

            @min.setter
            def min(self, value: float):
                self._dds._set_iio_attr(
                    ad9910.channel.DRG_RAMP_DOWN, self._range_name, value
                )

            @property
            def max(self) -> float:
                """Get/Set the maximum value of the DRG range"""
                return self._dds._get_iio_attr(
                    ad9910.channel.DRG_RAMP_UP, self._range_name
                )

            @max.setter
            def max(self, value: float):
                self._dds._set_iio_attr(
                    ad9910.channel.DRG_RAMP_UP, self._range_name, value
                )

            @property
            def increment(self) -> float:
                """Get/Set the increment value of the DRG range"""
                return self._dds._get_iio_attr(
                    ad9910.channel.DRG_RAMP_UP, f"{self._range_name}_step"
                )

            @increment.setter
            def increment(self, value: float):
                self._dds._set_iio_attr(
                    ad9910.channel.DRG_RAMP_UP, f"{self._range_name}_step", value
                )

            @property
            def decrement(self) -> float:
                """Get/Set the decrement value of the DRG range"""
                return self._dds._get_iio_attr(
                    ad9910.channel.DRG_RAMP_DOWN, f"{self._range_name}_step"
                )

            @decrement.setter
            def decrement(self, value: float):
                self._dds._set_iio_attr(
                    ad9910.channel.DRG_RAMP_DOWN, f"{self._range_name}_step", value
                )

            def __repr__(self):
                return f"DRG {self._range_name}: min={self.min}, max={self.max}, inc={self.increment}, dec={self.decrement}"

        def __init__(self, dds: "ad9910"):
            self._dds = dds
            self.frequency = ad9910.digital_ramp_generator.range(dds, "frequency")
            self.scale = ad9910.digital_ramp_generator.range(dds, "scale")
            self.phase = ad9910.digital_ramp_generator.range(dds, "phase")

        def _get_iio_attr(self, name):
            return self._dds._get_iio_attr(ad9910.channel.DRG, name)

        def _set_iio_attr(self, name, value):
            self._dds._set_iio_attr(ad9910.channel.DRG, name, value)

        @property
        def enable(self):
            """Get/Set the enable state of the DRG channel"""
            return self._get_iio_attr("en")

        @enable.setter
        def enable(self, value):
            self._set_iio_attr("en", value)

        @property
        def destination(self) -> "ad9910.destination":
            """Get the DRG destination mode. One of 'frequency', 'phase', 'amplitude'

            This property uses register access, so it is mostly intended for
            debugging and testing purposes. Destination is set automatically
            when range attributes are modified.
            """
            cfr2 = self._dds.reg_read(ad9910.reg.CFR2)
            return ad9910.destination((cfr2 >> 20) & 0x3)

        @property
        def operating_mode(self) -> "ad9910.digital_ramp_generator.mode":
            """Get/Set the operating mode of the DRG channel"""
            ramp_down = int(
                self._dds._get_iio_attr(ad9910.channel.DRG_RAMP_DOWN, "en"), 0
            )
            ramp_up = int(self._dds._get_iio_attr(ad9910.channel.DRG_RAMP_UP, "en"), 0)

            if ramp_up and ramp_down:
                return ad9910.digital_ramp_generator.mode.BIDIRECTIONAL_CONTINUOUS
            elif ramp_up and not ramp_down:
                return ad9910.digital_ramp_generator.mode.RAMP_UP
            elif not ramp_up and ramp_down:
                return ad9910.digital_ramp_generator.mode.RAMP_DOWN
            else:
                return ad9910.digital_ramp_generator.mode.BIDIRECTIONAL

        @operating_mode.setter
        def operating_mode(self, mode: "ad9910.digital_ramp_generator.mode"):
            ramp_up = 0
            ramp_down = 0
            if (
                mode == ad9910.digital_ramp_generator.mode.RAMP_UP
                or mode == ad9910.digital_ramp_generator.mode.BIDIRECTIONAL_CONTINUOUS
            ):
                ramp_up = 1
            if (
                mode == ad9910.digital_ramp_generator.mode.RAMP_DOWN
                or mode == ad9910.digital_ramp_generator.mode.BIDIRECTIONAL_CONTINUOUS
            ):
                ramp_down = 1

            self._dds._set_iio_attr(ad9910.channel.DRG_RAMP_UP, "en", ramp_up)
            self._dds._set_iio_attr(ad9910.channel.DRG_RAMP_DOWN, "en", ramp_down)

        @property
        def increment_rate(self) -> float:
            """Get/Set the frequency increment rate of the DRG channel in samples per second"""
            return self._dds._get_iio_attr(
                ad9910.channel.DRG_RAMP_UP, "sampling_frequency"
            )

        @increment_rate.setter
        def increment_rate(self, value: float):
            self._dds._set_iio_attr(
                ad9910.channel.DRG_RAMP_UP, "sampling_frequency", value
            )

        @property
        def decrement_rate(self) -> float:
            """Get/Set the frequency decrement rate of the DRG channel in samples per second"""
            return self._dds._get_iio_attr(
                ad9910.channel.DRG_RAMP_DOWN, "sampling_frequency"
            )

        @decrement_rate.setter
        def decrement_rate(self, value: float):
            self._dds._set_iio_attr(
                ad9910.channel.DRG_RAMP_DOWN, "sampling_frequency", value
            )

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
            """RAM Profile Class"""

            def __init__(self, dds: "ad9910", profile: int):
                self._dds = dds
                self._profile = profile
                self._rate_val = 1
                self._start = 0
                self._end = 1023
                self._mode = ad9910.ram_control.mode.RAMP_UP_CONTINUOUS

            @property
            def rate(self) -> float:
                """Get/Set RAM profile sampling frequency"""
                return (self._dds.sysclk_frequency / 4) / self._rate_val

            @rate.setter
            def rate(self, value: float):
                round_val = round((self._dds.sysclk_frequency / 4) / value)
                self._rate_val = max(1, min(round_val, 65535))

            @property
            def address_range(self):
                """Get/Set RAM profile address range"""
                return (self._start, self._end)

            @address_range.setter
            def address_range(self, value):
                if not isinstance(value, tuple) or len(value) != 2:
                    raise ValueError("Value must be a tuple of length 2")
                if value[0] < 0 or value[1] > 1023 or value[0] > value[1]:
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
            self._dds._set_iio_attr(ad9910.channel.RAM, "en", value)

        @property
        def dest(self) -> "ad9910.destination":
            """Get/Set RAM destination mode. One of 'frequency', 'amplitude', 'phase', 'polar'"""
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
            return self._dds._get_iio_attr(ad9910.channel.RAM, "frequency")

        @frequency.setter
        def frequency(self, value):
            self._dds._set_iio_attr(ad9910.channel.RAM, "frequency", value)

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

            if load_config:
                # parse config from fw data and apply settings
                if len(data) < 16 + ad9910.NUM_PROFILES * 8:
                    raise ValueError("Invalid firmware data length")
                cfr1 = int.from_bytes(data[4:8], byteorder="big")
                self._dest = ad9910.destination((cfr1 >> 29) & 0x3)
                self._profile_ctl = (cfr1 >> 17) & 0xFF

                for p in range(ad9910.NUM_PROFILES):
                    p_start = 8 + p * 8
                    p_end = p_start + 8
                    p_data = int.from_bytes(data[p_start:p_end], byteorder="big")
                    self.profiles[p]._mode = ad9910.ram_control.mode(p_data & 0x7)
                    self.profiles[p]._start = (p_data >> 14) & 0x3FF
                    self.profiles[p]._end = (p_data >> 30) & 0x3FF
                    self.profiles[p]._rate_val = (p_data >> 40) & 0xFFFF

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

            :param data: RAM data bytes. Length must be a multiple of 4 and not
                         exceed 4096 bytes.
            :param filename: Optional file path to save the RAM fw data.
            """
            length = 0

            if data is not None:
                length = len(data)
                if length % 4 != 0 or length > 4096:
                    raise Exception(f"invalid RAM data length: {length}")

            # prepare fw header with RAM profile metadata
            fw_data = bytes()
            magic = 0x00AD9910
            cfr1 = self._dest.value << 29 | self._profile_ctl << 17
            reserved = 0
            wcount = length // 4
            fw_data += magic.to_bytes(4, byteorder="big")
            fw_data += cfr1.to_bytes(4, byteorder="big")
            for profile in self.profiles:
                profile_data = profile._mode.value
                profile_data |= profile._start << 14
                profile_data |= profile._end << 30
                profile_data |= profile._rate_val << 40
                fw_data += profile_data.to_bytes(8, byteorder="big")

            fw_data += reserved.to_bytes(4, byteorder="big")
            fw_data += wcount.to_bytes(4, byteorder="big")

            if data is not None:
                fw_data += data

            if filename is not None:
                with open(filename, "wb") as f:
                    f.write(fw_data)

            self.firmware_load(fw_data, False)

        def file_load(self, file):
            """Load RAM FW data from binary file"""
            with open(file, "rb") as f:
                self.firmware_load(f.read(), True)

        def frequency_load(self, frequency_np, filename: Path = None):
            """Load frequency numpy array into RAM"""
            self._dest = ad9910.destination.FREQUENCY
            data = np.round((frequency_np * (1 << 32)) / self._dds.sysclk_frequency)
            self.config_load(ad9910.ram_control.be_reversed_bytes(data), filename)

        def phase_deg_load(self, phase_np, filename: Path = None):
            """Load phase numpy array (in degrees) into RAM"""
            self._dest = ad9910.destination.PHASE
            data = (phase_np % 360) * (1 << 16) / 360
            data = np.minimum(np.round(data), 0xFFFF).astype(np.uint32)
            data <<= 16
            self.config_load(ad9910.ram_control.be_reversed_bytes(data), filename)

        def phase_rad_load(self, phase_np, filename: Path = None):
            """Load phase numpy array (in radians) into RAM"""
            self._dest = ad9910.destination.PHASE
            data = (phase_np * (1 << 15)) / np.pi
            data = np.minimum(np.round(data), 0xFFFF).astype(np.uint32)
            data <<= 16
            self.config_load(ad9910.ram_control.be_reversed_bytes(data), filename)

        def amplitude_load(self, scale_np, filename: Path = None):
            """Load amplitude scale [0.0, 1.0) numpy array into RAM"""
            self._dest = ad9910.destination.AMPLITUDE
            data = scale_np * (1 << 14)
            data = np.minimum(np.round(data), 0x3FFF).astype(np.uint32)
            data <<= 18
            self.config_load(ad9910.ram_control.be_reversed_bytes(data), filename)

        def polar_load(self, complex_np, filename: Path = None):
            """
            Loads numpy array of complex numbers into RAM using polar coordinates.
            List elements are normalized to [0.0, 1.0) for amplitude.
            """
            self._dest = ad9910.destination.POLAR
            scale_np = np.abs(complex_np) * (1 << 14)
            scale_np = np.minimum(np.round(scale_np), 0x3FFF).astype(np.uint32)
            phase_np = (np.angle(complex_np) * (1 << 15)) / np.pi
            phase_np = np.minimum(np.round(phase_np), 0xFFFF).astype(np.uint32)
            data = phase_np << 16 | scale_np << 2
            self.config_load(ad9910.ram_control.be_reversed_bytes(data), filename)

        @staticmethod
        def be_reversed_bytes(np_data):
            """Reverses numpy array and converts to big-endian format bytes"""
            return np.flip(np_data).astype(np.dtype(">u4")).tobytes()

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

    def __init__(self, uri="", device_name=""):
        """
        Constructor for the AD9910 class.

        :param uri: URI string for the IIO context
        :param device_name: name, label or ID of the AD9910 device
        """
        compatible.__init__(self, uri, device_name)

        self._profile = ad9910.NUM_PROFILES
        self.profile = 0
        self.st = ad9910.single_tone(self)
        self.osk = ad9910.output_shift_keying(self)
        self.drg = ad9910.digital_ramp_generator(self)
        self.ram = ad9910.ram_control(self)
        self.parallel_port = ad9910.parallel_data_port(self)

        self._txdac = self._ctrl
        self._tx_channel_names = [ad9910.channel.PARALLEL_PORT.value]
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
            self._set_iio_attr(ad9910._PROFILE_CHANNELS[value], "en", 1)
            self._profile = value

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
    def charge_pump_current(self):
        """Get/Set the charge pump current in uA

        This property uses register access, so it is mostly intended for
        debugging and testing purposes. This property only has any effect if
        the PLL is enabled in the device-tree.
        """
        reg_val = self.reg_read(ad9910.reg.CFR3)
        return 25 * ((reg_val >> 19) & 0x7) + 212

    @charge_pump_current.setter
    def charge_pump_current(self, value):
        if value < 212 or value > 387:
            raise Exception(f"Invalid charge pump current: {value} uA")
        reg_val = self.reg_read(ad9910.reg.CFR3)
        icp = round((value - 212) / 25)
        reg_val = (reg_val & ~(0x7 << 19)) | ((icp & 0x7) << 19)
        self.reg_write(ad9910.reg.CFR3, reg_val)

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
        if reg in ad9910._REG64:
            self._set_iio_debug_attr_str(
                "direct_reg_access", 0x100 | reg.value, self._ctrl
            )
            high = int(self._get_iio_debug_attr_str("direct_reg_access", self._ctrl), 0)
            val |= high << 32

        if backup_profile is not None:
            # restore profile after reading register value
            self.profile = backup_profile

        return val

    def reg_write(self, reg: "ad9910.reg", value):
        """Direct Register Write Access via debugfs"""
        low = value & 0xFFFFFFFF
        if reg in ad9910._REG64:
            high = (value >> 32) & 0xFFFFFFFF
            self._set_iio_debug_attr_str(
                "direct_reg_access", f"{0x100 | reg.value} {high}", self._ctrl
            )
        self._set_iio_debug_attr_str(
            "direct_reg_access", f"{reg.value} {low}", self._ctrl
        )
