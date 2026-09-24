# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import warnings

import numpy as np

from adi.ad4080 import ad4080
from adi.ad5686 import ad5686
from adi.ad9910 import ad9910
from adi.adf4151x import adf41513
from adi.adrf5720 import adrf5720


class admfm8000(ad9910):
    """ADMFM8000 FMCW Transmitter

    This class provides a high-level interface for controlling the ADMFM8000.
    The system consists of an AD9910 DDS, an ADF41513 PLL, and an ADRF5730 DSA.
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
        # the frequency scaling is already in effect while the DDS is brought up
        self._pll_N = 20
        self._pll_refin_init_frequency = pll_refin_frequency

        ad9910.__init__(self, uri)

        self.pll = adf41513(uri)
        self.dsa = adrf5720(uri, "adrf5703")
        self.pll_N = self._pll_N

        for profile in self.st.profiles:
            profile.raw = ad9910.ASF_MAX

    @property
    def attenuation(self):
        """Get/Set the DSA attenuation in dB"""
        return self.dsa.attenuation

    @attenuation.setter
    def attenuation(self, value):
        self.dsa.attenuation = value

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
    def _freq_scale(self):
        return admfm8000._VCO_FEEDBACK_DIV * self._pll_N

    def single_tone_config(self, profile=0, frequency=None, amplitude=None, phase=None):
        """Configure the DDS for single tone output with respect to VCO frequency output.

        :param profile: DDS Profile number
        :param frequency: Output frequency in Hz
        :param amplitude: Output amplitude in mA (input to PLL reference)
        :param phase: Output phase in radians (input to PLL reference)
        """
        self.profile = profile
        if frequency is not None:
            self.st.profiles[profile].frequency = frequency
        if phase is not None:
            self.st.profiles[profile].phase = phase
        if amplitude is not None:
            self.st.profiles[profile].amplitude = amplitude

    def parallel_port_config(
        self, enable=True, frequency_np=None, cyclic=True, rate=None
    ):
        """Configure the DDS Parallel Port channel

        :param enable: Enable/Disable the Parallel Port channel
        :param frequency_np: numpy array of frequency values in Hz
        :param cyclic: Enable/Disable cyclic mode for the DMA buffer
        :param rate: Rate of the Parallel Port channel in samples/second
        """
        if not enable:
            self.tx_destroy_buffer()

        if rate is not None:
            self.parallel_port.rate = rate

        if enable and frequency_np is not None:
            self.parallel_port.frequency_push(frequency_np, cyclic=cyclic)

    def digital_ramp_config(
        self,
        enable=None,
        mode=None,
        freq_min=None,
        freq_max=None,
        inc_time=None,
        dec_time=None,
        inc_slope=None,
        dec_slope=None,
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
        :param inc_time: Positive control time in seconds
        :param dec_time: Negative control time in seconds
        :param inc_slope: Positive ramp slope in Hz/s
        :param dec_slope: Negative ramp slope in Hz/s
        :param inc_rate: Positive slope rate in samples/second
        :param dec_rate: Negative slope in samples/second
        :param inc_ramp_time: Ramp time while it is in a positive slope in seconds.
                              Configure this if not providing inc_slope nor
                              inc_rate. This will automatically calculate the
                              slope based on the desired ramp time.
        :param dec_ramp_time: Ramp time while it is in a negative slope in seconds.
                              Configure this if not providing dec_slope nor
                              dec_rate. This will automatically calculate the
                              slope based on the desired ramp time.
        :param kwargs: Additional frequency ramp attributes to set as key-value pairs
        """
        ramp = self.drg.frequency

        if enable:
            # disable DRG when updating settings.
            # This ensures that HDL starts from a known state.
            self.drg.disable()

        for attr, value in kwargs.items():
            try:
                setattr(ramp, attr, value)
            except Exception as ex:
                warnings.warn(f"Failed to set attribute {attr} on DRG channel: {ex}")

        if freq_min is not None:
            ramp.min = freq_min
        if freq_max is not None:
            ramp.max = freq_max

        freq_range = ramp.max - ramp.min
        if freq_range <= 0:
            raise ValueError("Invalid frequency range for DRG configuration")

        if inc_rate is not None:
            ramp.positive_slope_rate = inc_rate
        if dec_rate is not None:
            ramp.negative_slope_rate = dec_rate

        if inc_ramp_time is not None:
            ramp.positive_slope_time = inc_ramp_time
        if dec_ramp_time is not None:
            ramp.negative_slope_time = dec_ramp_time

        if inc_time is not None:
            ramp.positive_ctl_time = inc_time
        if dec_time is not None:
            ramp.negative_ctl_time = dec_time

        if inc_slope is not None:
            ramp.positive_slope = inc_slope
        if dec_slope is not None:
            ramp.negative_slope = dec_slope

        if mode is not None:
            ramp.operating_mode = mode

        if enable is not None:
            if enable:
                self.drg.enable(ad9910.destination.FREQUENCY)
            else:
                self.drg.disable()

    def ram_control_profile_config(
        self, profile=0, mode=None, addr_range=None, rate=None
    ):
        """Configure the DDS RAM Control Profiles

        :param profile: RAM Control Profile number
        :param mode: RAM Control Mode as defined in ad9910.ram_control.mode
        :param addr_range: RAM address range as a tuple (start_addr, end_addr)
        :param rate: RAM update rate in samples/second
        """
        self.profile = profile
        if isinstance(addr_range, tuple) and len(addr_range) == 2:
            self.ram.profiles[profile].address_range = addr_range
        if mode is not None:
            self.ram.profiles[profile].operating_mode = mode
        if rate is not None:
            self.ram.profiles[profile].rate = rate

    def ram_control_config(self, enable=True, frequency_np=None, output_bin=None):
        """Load frequency list with respect to VCO frequency output into DDS RAM in Hz

        :param enable: Enable/Disable the RAM Mode
        :param frequency_np: numpy array of frequency values in Hz
        :param output_bin: Optional file path to save the RAM fw data
        """
        if frequency_np is not None:
            if self.ram.enable == 1:
                # make sure RAM is disabled before loading new values
                self.ram.enable = 0

            self.ram.frequency_load(frequency_np, output_bin)

        self.ram.enable = 1 if enable else 0


class admfm8000_evalz(admfm8000):
    """ADMFM8000-EVALZ FMCW Transceiver

    This class extends the ADMFM8000 transmitter with the evaluation board
    receive datapath. The RX chain consists of an AD4880 high speed SAR ADC,
    which captures the downconverted I and Q baseband channels, and an AD5317R
    nanoDAC, whose first two voltage channels drive the gain control input of
    the I and Q VGAs.
    """

    def __init__(self, uri="", pll_refin_frequency=80e6):
        """Initialize the ADMFM8000-EVALZ system

        :param uri:s
            URI string for connecting to the hardware
        :param pll_refin_frequency:
            Initial PLL reference input frequency in Hz (default: 80e6).
            This should be set to the value configured in the device-tree.
        """
        admfm8000.__init__(self, uri, pll_refin_frequency)

        self.sar_adc = ad4080(uri, "ad4880")
        self.nano_dac = ad5686(uri, "ad5313r")
        self.sar_adc.rx_enabled_channels = [0, 1]

        # Full-scale code magnitude of the ADC, taken from the sample format.
        # The AD4884 always reports two's complement samples.
        bits = self.sar_adc._ctrl.channels[0].data_format.bits
        self._rx_full_scale = float(2 ** (bits - 1))

    @property
    def rx_vgain_voltage(self):
        """Get/Set the I/Q path VGA gain control voltage in Volts"""
        return self.nano_dac.channel[0].voltage

    @rx_vgain_voltage.setter
    def rx_vgain_voltage(self, value):
        # Clamp the voltage between 0 and 1.5 V
        value = min(max(value, 0), 1.5)
        self.nano_dac.channel[0].voltage = value
        self.nano_dac.channel[1].voltage = value

    @property
    def rx_gain_dB(self):
        """Get/Set the I/Q path VGA gain control voltage in dB.

        It is assumed a gain scaling of 30 mV/dB.
        """
        return self.rx_vgain_voltage * 1000 / 30

    @rx_gain_dB.setter
    def rx_gain_dB(self, value):
        self.rx_vgain_voltage = value * 30 / 1000

    @property
    def rx_sampling_frequency(self):
        """Get the ADC sampling frequency in Hz"""
        return self.sar_adc.channel[0].sampling_frequency

    @property
    def rx_buffer_size(self):
        """Get/Set the ADC buffer size in samples"""
        return self.sar_adc.rx_buffer_size

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        self.sar_adc.rx_buffer_size = value

    def rx(self):
        """Capture the baseband data from the SAR ADC

        The I and Q channel codes are combined into complex samples and
        normalized by the full-scale code magnitude, so both the real and
        imaginary parts span the -1.0 to 1.0 full-scale range.

        :return: Complex numpy array with the I/Q baseband data
        """
        data = self.sar_adc.rx()
        samples = np.asarray(data[0], dtype=np.float64)
        if len(data) > 1:
            samples = samples + 1j * np.asarray(data[1], dtype=np.float64)
        return samples / self._rx_full_scale
