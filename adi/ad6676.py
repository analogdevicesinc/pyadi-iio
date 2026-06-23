# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx


class ad6676(rx, context_manager):
    """ AD6676 Wideband IF Receiver Subsystem """

    _complex_data = True
    _rx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""

    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)

        self._rxadc = self._ctx.find_device("axi-ad6676-hpc")
        self._ctrl = self._rxadc

        rx.__init__(self)

    @property
    def adc_frequency(self):
        """adc_frequency: The clock frequency of the ADC. Maximizing the clock frequency is helpful
        when the IF or bandwidth are high. A lower clock frequency reduces power consumption and is
        appropriate for low IFs and narrow bandwidths.

        Range using external synthesizer [2.0,3.2] GHz in Hz
        Range using internal synthesizer [2.925,3.2] GHz in Hz"""
        return self._get_iio_attr_str("voltage0", "adc_frequency", False)

    @adc_frequency.setter
    def adc_frequency(self, value):
        self._set_iio_attr("voltage0", "adc_frequency", False, value)

    @property
    def bandwidth(self):
        """bandwidth: The bandwidth of the ADC. Since the AD6676 uses delta-sigma technology,
        the available bandwidth is a relatively small fraction of the ADC clock rate and
        the AD6676 achieves the lowest noise and distortion when the bandwidth is small.

        The allowed range is between [0.005,0.05]*FADC in Hz"""
        return self._get_iio_attr_str("voltage0", "bandwidth", False)

    @bandwidth.setter
    def bandwidth(self, value):
        self._set_iio_attr("voltage0", "bandwidth", False, value)

    @property
    def bw_margin_high(self):
        """bw_margin_high: High/upper bandwidth margins for the noise-shaping profile of the ADC.
        Typical values are 5 MHz, but the user may want to increase these margins in wideband operation
        in order to optimize the noise profile of the ADC.
        Typical range [0,30] MHz in MHz"""
        return self._get_iio_attr_str("voltage0", "bw_margin_high", False)

    @bw_margin_high.setter
    def bw_margin_high(self, value):
        self._set_iio_attr("voltage0", "bw_margin_high", False, value)

    @property
    def bw_margin_if(self):
        """bw_margin_if: Displacement of the resonance frequency (F1Shift) of the first resonator within
        the ADC from band-center. Typically 0 is appropriate, but in the widest bandwidth modes
        positive shifts can be used to reduce the noise density near the upper edge of the passband.
        Typical range [-30,30] MHz in MHz"""
        return self._get_iio_attr_str("voltage0", "bw_margin_if", False)

    @bw_margin_if.setter
    def bw_margin_if(self, value):
        self._set_iio_attr("voltage0", "bw_margin_if", False, value)

    @property
    def bw_margin_low(self):
        """bw_margin_low: Lower bandwidth margins for the noise-shaping profile of the ADC.
        Typical values are 5 MHz, but the user may want to increase these margins in wideband operation
        in order to optimize the noise profile of the ADC.
        Typical range [0,30] MHz in MHz"""
        return self._get_iio_attr_str("voltage0", "bw_margin_low", False)

    @bw_margin_low.setter
    def bw_margin_low(self, value):
        self._set_iio_attr("voltage0", "bw_margin_low", False, value)

    @property
    def hardwaregain(self):
        """hardwaregain: The AD6676 contains a 50-ohm input attenuator programmable in 1-dB steps.
        Use this device attribute to set the attenuator's attenuation.
        The dynamic range of the system increases somewhat with moderate attenuation settings of 6-12 dB,
        at the expense of an increased noise figure.
        The range is from 0 to -27.00 dB in 1dB steps.
        The nomenclature used here is gain instead of attenuation, so all values are expressed negative."""
        return self._get_iio_attr_str("voltage0", "hardwaregain", False)

    @hardwaregain.setter
    def hardwaregain(self, value):
        self._set_iio_attr("voltage0", "hardwaregain", False, value)

    @property
    def scale(self):
        """scale: One of the convenient features of the AD6676 is that the full-scale of its ADC is
        relatively small and adjustable over a 12-dB range [1.00 .. 0.25]
        The dynamic range of the ADC is highest at the maximum full-scale setting but the noise
        figure of the system is lowest at the minimum full-scale setting.

        Writing a value of 0.5 to this device attribute lowers the PIN_0dBFS by 6 dB.
        Likewise writing a value of 0.25 to this device attribute lowers the PIN_0dBFS by 12 dB."""
        return self._get_iio_attr_str("voltage0", "scale", False)

    @scale.setter
    def scale(self, value):
        self._set_iio_attr("voltage0", "scale", False, value)

    @property
    def intermediate_frequency(self):
        """intermediate_frequency: The IF (intermediate frequency) to which the ADC is tuned.
        The AD6676 supports IFs from 70 to 450 MHz provided the external inductors are chosen appropriately.
        Since the AD6676-EBZ by default includes a pair of 19-nH inductors soldered to the evaluation board,
        the IF range allowed is less than the full range supported by the AD6676."""
        return self._get_iio_attr_str("voltage0", "intermediate_frequency", False)

    @intermediate_frequency.setter
    def intermediate_frequency(self, value):
        self._set_iio_attr("voltage0", "intermediate_frequency", False, value)

    @property
    def sampling_frequency(self):
        """sampling_frequency: The complex (I/Q) data rate in SPS.
        The AD6676 supports decimation factors (DFs) of 12, 16, 24 and 32.
        The complex (I/Q) data rate at the JESD204B outputs is FADC / DF."""
        return self._get_iio_attr_str("voltage0", "sampling_frequency", False)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_attr("voltage0", "sampling_frequency", False, value)

    @property
    def shuffler_control(self):
        """shuffler_control: The AD6676 includes dynamic reordering of the comparators within the ADC in order to
        break up the spurious tones and distortion products associated with a fixed ordering.
        The Shuffle Control device attribute allows the user to experiment with different shuffling rates.
        The 'fadc' option (Shuffle every 1) reorders the comparators on every clock cycle with 50% probability.
        This shuffle scheme is able to randomize deterministic spurs but tends to increase the
        noise density and creates FADC/32 "shuffle humps" in the output spectrum.
        Similarly, the 'fadc/2' 'fadc/3' 'fadc/4' (Shuffle every 2,3,4) options reorder the comparators every n clock cycles
        with 50% probability. Using a high value of n decreases the noise degradation at the
        expense of less effective randomization and FADC/(32*n) shuffle humps that are closer
        to the main carrier. Fast shuffling can be disabled by selecting the **disable** option.
        Available values: disable fadc fadc/2 fadc/3 fadc/4"""
        return self._get_iio_attr_str("voltage0", "shuffler_control", False)

    @shuffler_control.setter
    def shuffler_control(self, value):
        self._set_iio_attr("voltage0", "shuffler_control", False, value)

    @property
    def shuffler_thresh(self):
        """shuffler_thresh: In order to obtain the spur-reduction benefits of shuffling at large signal levels while
        retaining the low noise of not shuffling when the signal is small, the AD6676 supports
        dynamic shuffle control via the Shuffle Threshold attribute.
        Shuffling is disabled if the raw ADC output is below the specified threshold for ~5000 clock cycles.
        A threshold of zero implies that shuffling is always enabled.
        The supported range is from 0..8"""
        return self._get_iio_attr_str("voltage0", "shuffler_thresh", False)

    @shuffler_thresh.setter
    def shuffler_thresh(self, value):
        self._set_iio_attr("voltage0", "shuffler_thresh", False, value)

    @property
    def test_mode(self):
        """test_mode: Select Test Mode. Options are:
        off midscale_short pos_fullscale neg_fullscale checkerboard pn_long pn_short one_zero_toggle user ramp"""
        return self._get_iio_attr("voltage0", "test_mode", False)

    @test_mode.setter
    def test_mode(self, value):
        self._set_iio_attr("voltage0", "test_mode", False, value, self._rxadc)
