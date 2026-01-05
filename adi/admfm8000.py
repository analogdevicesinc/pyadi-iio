# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import warnings

from adi.ad9910 import ad9910
from adi.adf4151x import adf41513
from adi.adrf5720 import adrf5720


class admfm8000:
    """ADMFM8000 FMCW Transmitter

    This class provides a high-level interface for controlling the ADMFM8000.
    The system consists of an AD9910 DDS, an ADF41513 PLL, and an ADRF5730 DSA.
    Helper functions to configure the DDS modes have the frequency values
    automatically scaled down based on the PLL N divider and VCO feedback
    divider.
    """

    _VCO_FEEDBACK_DIV = 16

    def __init__(self, uri="", pll_refin_frequency=80e6):
        """Initialize the ADMFM8000 system

        :param uri:
            URI string for connecting to the hardware
        :param pll_refin_frequency:
            Initial PLL reference input frequency in Hz (default: 80e6).
            This should be set to the value configured in the device-tree.
        """
        self.dds = ad9910(uri)
        self.pll = adf41513(uri)
        self.dsa = adrf5720(uri, "adrf5730")
        self._pll_refin_init_frequency = pll_refin_frequency
        self.pll_N = 20

    @property
    def attenuation(self):
        """Get/Set the DSA attenuation in dB"""
        return self.dsa.attenuation

    @attenuation.setter
    def attenuation(self, value):
        self.dsa.attenuation = value

    @property
    def profile(self):
        """Get/Set the current DDS profile"""
        return self.dds.profile

    @profile.setter
    def profile(self, value):
        self.dds.profile = value

    @property
    def pll_N(self):
        """Get/Set the PLL N divider value

        This makes sure that PLL is always configured in Integer-N mode, for
        best phase noise performance.
        """
        return self._pll_N

    @pll_N.setter
    def pll_N(self, value):
        value = int(value)
        self.pll.frequency = value * self._pll_refin_init_frequency
        self._pll_N = value

    @property
    def frequency_scale(self):
        """Get the overall frequency scaling factor based on current PLL and VCO
        settings

        This value takes into account the PLL settings and the feedback divider
        to calculate the effective frequency scaling factor.
        """
        return admfm8000._VCO_FEEDBACK_DIV * self._pll_N

    @property
    def single_tone_frequency(self):
        """Get/Set the single tone output frequency in Hz

        This value represents the system-level output frequency of the VCO
        when the DDS is operating in single tone mode. It considers the current
        selected DDS profile frequency and the overall frequency scaling factor
        based on the PLL settings.
        """
        return self.dds.st.frequency * self.frequency_scale

    @single_tone_frequency.setter
    def single_tone_frequency(self, value):
        self.dds.st.frequency = value / self.frequency_scale

    def single_tone_config(self, profile=0, frequency=None, scale=None, phase=None):
        """Configure the DDS for single tone output with respect to VCO frequency output.

        :param profile: DDS Profile number
        :param frequency: Output frequency in Hz
        :param scale: Output scale (0.0 to 1.0)
        :param phase: Output phase in radians
        """
        self.dds.profile = profile
        if frequency is not None:
            self.dds.st.profiles[profile].frequency = frequency / self.frequency_scale
        if phase is not None:
            self.dds.st.profiles[profile].phase = phase
        if scale is not None:
            self.dds.st.profiles[profile].scale = scale

    def parallel_port_config(
        self, enable=True, frequency_np=None, cyclic=True, rate=None
    ):
        """Configure the DDS Parallel Port channel

        :param enable: Enable/Disable the Parallel Port channel
        :param frequency_np: numpy array of frequency values in Hz
        :param cyclic: Enable/Disable cyclic mode for the DMA buffer
        :param rate: Rate of the Parallel Port channel in samples/second
        """
        if enable:
            self.dds.parallel_port.enable = 1
        else:
            self.dds.tx_destroy_buffer()
            self.dds.parallel_port.enable = 0

        if rate is not None:
            try:
                self.dds.parallel_port.rate = rate
            except Exception as ex:
                warnings.warn(f"Failed to set Parallel Port rate: {ex}")

        if frequency_np is not None:
            self.dds.parallel_port.frequency_push(
                frequency_np / self.frequency_scale, cyclic=cyclic
            )

    def digital_ramp_config(
        self,
        enable=None,
        mode=None,
        freq_min=None,
        freq_max=None,
        inc_step=None,
        dec_step=None,
        inc_rate=None,
        dec_rate=None,
        inc_ramp_time=None,
        dec_ramp_time=None,
        **kwargs,
    ):
        """Configure the DDS Digital Ramp Generator (DRG)

        :param enable: Enable/Disable the Digital Ramp Generator
        :param mode: DRG Operating Mode as defined in ad9910.digital_ramp_generator.mode
        :param freq_min: Minimum frequency in Hz
        :param freq_max: Maximum frequency in Hz
        :param inc_step: Increment step in Hz
        :param dec_step: Decrement step in Hz
        :param inc_rate: Increment rate in samples/second
        :param dec_rate: Decrement rate in samples/second
        :param inc_ramp_time: Ramp time for increment in seconds.
                              Configure this if not providing inc_step nor
                              inc_rate. This will automatically calculate the
                              increment step based on the desired ramp time.
        :param dec_ramp_time: Ramp time for decrement in seconds.
                              Configure this if not providing dec_step nor
                              dec_rate. This will automatically calculate the
                              decrement step based on the desired ramp time.
        :param kwargs: Additional DRG attributes to set as key-value pairs
        """
        if enable:
            # disable DRG when updating settings.
            # This ensures that HDL starts from a known state.
            self.dds.drg.enable = 0

        for attr, value in kwargs.items():
            try:
                self.dds.drg._set_iio_attr(attr, value)
            except Exception as ex:
                warnings.warn(f"Failed to set attribute {attr} on DRG channel: {ex}")

        if freq_min is not None:
            self.dds.drg.frequency.min = freq_min / self.frequency_scale

        freq_min = self.dds.drg.frequency.min * self.frequency_scale

        if freq_max is not None:
            self.dds.drg.frequency.max = freq_max / self.frequency_scale

        freq_max = self.dds.drg.frequency.max * self.frequency_scale

        freq_range = freq_max - freq_min
        if freq_range <= 0:
            raise ValueError("Invalid frequency range for DRG configuration")

        if mode is not None:
            self.dds.drg.operating_mode = mode

        if inc_step is None and inc_rate is None and inc_ramp_time is not None:
            inc_rate = self.dds.sysclk_frequency / 4  # max DRG update rate
            inc_step = freq_range
            if inc_ramp_time > 0:
                inc_step /= inc_rate * inc_ramp_time

        if dec_step is None and dec_rate is None and dec_ramp_time is not None:
            dec_rate = self.dds.sysclk_frequency / 4  # max DRG update rate
            dec_step = freq_range
            if dec_ramp_time > 0:
                dec_step /= dec_rate * dec_ramp_time

        if inc_step is not None:
            self.dds.drg.frequency.increment = inc_step / self.frequency_scale
        if dec_step is not None:
            self.dds.drg.frequency.decrement = dec_step / self.frequency_scale
        if inc_rate is not None:
            self.dds.drg.increment_rate = inc_rate
        if dec_rate is not None:
            self.dds.drg.decrement_rate = dec_rate
        if enable is not None:
            self.dds.drg.enable = 1 if enable else 0

    def ram_control_profile_config(
        self, profile=0, mode=None, addr_range=None, rate=None
    ):
        """Configure the DDS RAM Control Profiles

        :param profile: RAM Control Profile number
        :param mode: RAM Control Mode as defined in ad9910.ram_control.mode
        :param addr_range: RAM address range as a tuple (start_addr, end_addr)
        :param rate: RAM update rate in samples/second
        """
        self.dds.profile = profile
        if isinstance(addr_range, tuple) and len(addr_range) == 2:
            self.dds.ram.profiles[profile].address_range = addr_range
        if mode is not None:
            self.dds.ram.profiles[profile].operating_mode = mode
        if rate is not None:
            self.dds.ram.profiles[profile].rate = rate

    def ram_control_config(self, enable=True, frequency_np=None):
        """Load frequency list with respect to VCO frequency output into DDS RAM in Hz

        :param enable: Enable/Disable the RAM Mode
        :param frequency_np: numpy array of frequency values in Hz
        """
        if frequency_np is not None:
            if self.dds.ram.enable == 1:
                # make sure RAM is disabled before loading new values
                self.dds.ram.enable = 0

            self.dds.ram.frequency_load(frequency_np / self.frequency_scale)

        self.dds.ram.enable = 1 if enable else 0
