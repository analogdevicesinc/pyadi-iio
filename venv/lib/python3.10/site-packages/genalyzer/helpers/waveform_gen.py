# Copyright (C) 2024-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD OR GPL-2.0-or-later
from ..simplified_beta import (
    config_gen_tone,
    gen_real_tone,
    config_quantize,
    config_code_format,
    quantize,
    config_free,
)
import numpy as np
from scipy import signal


class WaveformGen:
    """Waveform data generation for transmit devices"""

    _tone_phase = [0, 0, 0]  # tone phase
    _noise = 0.0

    def __init__(
        self,
        npts: int,
        freq: int,
        code_fmt: int,
        res: int,
        v_ref_n: float,
        v_ref_p: float,
        v_min: float,
        v_max: float,
    ):
        """Constructor for WaveformGen class.

        :param npts: number of points required per waveform cycle
        :param freq: output frequency required in hz
        :param code_fmt: code format to get data in
            0: for binary offset
            1: for 2's complement
        :param res: code resolution
        :param v_ref_n: negative reference voltage
            Can be zero(0) for unipolar device
        :param v_ref_p: positive reference voltage
        :param v_min: minimum required voltage to generate
            Must be in the accepted reference voltage range
        :param v_max: maximum required voltage to generate
            Must be in the accepted reference voltage range
        """

        self._data = []
        self.npts = npts
        self.freq = freq
        self.code_fmt = code_fmt
        self.res = res
        self._v_ref_n = v_ref_n
        self._v_ref_p = v_ref_p
        self.v_min = v_min
        self.v_max = v_max

    @property
    def v_min(self):
        """v_min: Lower required voltage limit"""
        return self._v_min

    @v_min.setter
    def v_min(self, value):
        """v_min: Set Lower required voltage limit"""
        if value < self._v_ref_n:
            raise Exception(
                "required lower voltage cannot be less than lower voltage reference"
            )
        self._v_min = value

    @property
    def v_max(self):
        """v_max: Upper required voltage limit"""
        return self._v_max

    @v_max.setter
    def v_max(self, value):
        """v_max: Set Upper required voltage limit"""
        if value > self._v_ref_p:
            raise Exception(
                "required upper voltage cannot be greater than upper voltage reference"
            )
        self._v_max = value

    def __prepare_waveform_gen(self):
        self.__samp_freq = self.npts * self.freq
        self.__maxcode = pow(2, self.res) - 1
        self.__v_fsr = self._v_ref_p - self._v_ref_n
        self.__vp_p = self.v_max - self.v_min
        self.__mp_fsr = (self._v_ref_p + self._v_ref_n) / 2
        self.__mp_vreq = (self.v_max + self.v_min) / 2
        self.__offset = int(
            ((self.__mp_vreq - self.__mp_fsr) / self.__v_fsr) * self.__maxcode
        )
        self.__v_bias = ((abs(self._v_ref_n) + self.__mp_vreq) * 2) / self.__v_fsr
        self.__amplitude = (2 ** (self.res - 1)) - 1

        self.__tone_freq = [self.freq / self.npts] * 3
        self.__tone_ampl = [self.__vp_p / 2] * 2

        # Period
        self.__ts = 1 / float(self.__samp_freq)
        # Time array
        self.__t = np.arange(0, self.npts * self.__ts, self.__ts)

    def __gen_sine_cosine(self, tone_type):
        self.__prepare_waveform_gen()

        # Generate real tone
        c = config_gen_tone(
            tone_type,
            self.npts,
            self.freq,
            3,
            self.__tone_freq,
            self.__tone_ampl,
            self._tone_phase,
        )
        wf = gen_real_tone(c)

        # Configure the waveform quantization
        config_quantize(self.npts, self.__v_fsr, self.res, self._noise, c)

        # Configure code data format
        config_code_format(self.code_fmt, c)

        # Get the quantized waveform
        qwf = quantize(wf, c)
        self._data = [x + self.__offset for x in qwf]  # Add the offset calculated

        # Free config object
        config_free(c)

        return self._data

    def __gen_other_waveforms(self):
        self._data *= self.__vp_p / self.__v_fsr
        self._data += self.__v_bias
        self._data *= self.__amplitude
        self._data = np.uint32(self._data)

        if self.code_fmt:
            self._data = np.bitwise_xor(2 ** (self.res - 1), self._data)

        return self._data

    def __del__(self):
        self._data = []

    def gen_sine_wave(self):
        """
        Generate sine wave data

        Returns: 
            Waveform as list of ints
        """
        return self.__gen_sine_cosine(1)

    def gen_cosine_wave(self):
        """
        Generate cosine wave data

        Returns: 
            Waveform as list of ints
        """
        return self.__gen_sine_cosine(0)

    def gen_triangular_wave(self):
        """
        Generate triangular wave data

        Returns: 
            Waveform as list of ints
        """
        self.__prepare_waveform_gen()
        self._data = signal.sawtooth(2 * np.pi * self.freq * self.__t, 0.5)
        return self.__gen_other_waveforms()

    def gen_square_wave(self):
        """
        Generate square wave data

        Returns: 
            Waveform as list of ints
        """
        self.__prepare_waveform_gen()
        self._data = signal.square(2 * np.pi * self.freq * self.__t, 0.5)
        return self.__gen_other_waveforms()

    def gen_pwm_wave(self, duty_cycle):
        """
        Generate pwm wave data

        Args: 
            ``duty_cycle`` (``float``): Duty cycle required. Must be in between 0 and 1.

        Returns: 
            Waveform as list of ints
        """
        self.__prepare_waveform_gen()
        self._data = signal.square(2 * np.pi * self.freq * self.__t, duty_cycle)
        return self.__gen_other_waveforms()
