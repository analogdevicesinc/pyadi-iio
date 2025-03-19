# Copyright (C) 2024-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD OR GPL-2.0-or-later

from dataclasses import dataclass, field

# import numpy as np
# from scipy import signal
from typing import List
from ctypes import (
    c_char,
    c_uint8,
    c_int32,
    c_int64,
    c_uint,
    c_uint64,
    c_ulong,
    c_int,
    c_double,
    c_bool,
    POINTER,
    byref,
    Structure,
    c_void_p,
    c_char_p,
    CDLL,
)
from platform import system as _system
from ctypes.util import find_library
import os

if "Windows" in _system():
    _libgen = "libgenalyzer.dll"
else:
    # Non-windows, possibly Posix system
    _libgen = "genalyzer"

_libgen = CDLL(find_library(_libgen), use_errno=True, use_last_error=True)


class _GNConfig(Structure):
    pass


_GNConfigPtr = POINTER(_GNConfig)


class GNConfig(object):
    """Configuration structure to handle library state"""

    def __init__(self):
        self._struct = _GNConfigPtr()


_gn_config_free = _libgen.gn_config_free
_gn_config_free.restype = c_int
_gn_config_free.argtypes = [
    POINTER(_GNConfigPtr),
]

_gn_config_set_ttype = _libgen.gn_config_set_ttype
_gn_config_set_ttype.restype = c_int
_gn_config_set_ttype.argtypes = [
    c_uint,
    POINTER(_GNConfigPtr),
]

_gn_config_set_npts = _libgen.gn_config_set_npts
_gn_config_set_npts.restype = c_int
_gn_config_set_npts.argtypes = [
    c_ulong,
    POINTER(_GNConfigPtr),
]

_gn_config_get_npts = _libgen.gn_config_get_npts
_gn_config_get_npts.restype = c_int
_gn_config_get_npts.argtypes = [
    POINTER(c_ulong),
    POINTER(_GNConfigPtr),
]

_gn_config_set_sample_rate = _libgen.gn_config_set_sample_rate
_gn_config_set_sample_rate.restype = c_int
_gn_config_set_sample_rate.argtypes = [
    c_double,
    POINTER(_GNConfigPtr),
]


_gn_config_get_sample_rate = _libgen.gn_config_get_sample_rate
_gn_config_get_sample_rate.restype = c_int
_gn_config_get_sample_rate.argtypes = [
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_config_set_data_rate = _libgen.gn_config_set_data_rate
_gn_config_set_data_rate.restype = c_int
_gn_config_set_data_rate.argtypes = [
    c_double,
    POINTER(_GNConfigPtr),
]

_gn_config_set_shift_freq = _libgen.gn_config_set_shift_freq
_gn_config_set_shift_freq.restype = c_int
_gn_config_set_shift_freq.argtypes = [
    c_double,
    POINTER(_GNConfigPtr),
]

_gn_config_set_num_tones = _libgen.gn_config_set_num_tones
_gn_config_set_num_tones.restype = c_int
_gn_config_set_num_tones.argtypes = [
    c_ulong,
    POINTER(_GNConfigPtr),
]

_gn_config_set_tone_freq = _libgen.gn_config_set_tone_freq
_gn_config_set_tone_freq.restype = c_int
_gn_config_set_tone_freq.argtypes = [
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_config_set_tone_ampl = _libgen.gn_config_set_tone_ampl
_gn_config_set_tone_ampl.restype = c_int
_gn_config_set_tone_ampl.argtypes = [
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_config_set_tone_phase = _libgen.gn_config_set_tone_phase
_gn_config_set_tone_phase.restype = c_int
_gn_config_set_tone_phase.argtypes = [
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_config_set_fsr = _libgen.gn_config_set_fsr
_gn_config_set_fsr.restype = c_int
_gn_config_set_fsr.argtypes = [
    c_double,
    POINTER(_GNConfigPtr),
]

_gn_config_set_qres = _libgen.gn_config_set_qres
_gn_config_set_qres.restype = c_int
_gn_config_set_qres.argtypes = [
    c_int,
    POINTER(_GNConfigPtr),
]

_gn_config_set_noise_rms = _libgen.gn_config_set_noise_rms
_gn_config_set_noise_rms.restype = c_int
_gn_config_set_noise_rms.argtypes = [
    c_double,
    POINTER(_GNConfigPtr),
]

_gn_config_set_code_format = _libgen.gn_config_set_code_format
_gn_config_set_code_format.restype = c_int
_gn_config_set_code_format.argtypes = [
    c_uint,
    POINTER(_GNConfigPtr),
]

_gn_config_set_nfft = _libgen.gn_config_set_nfft
_gn_config_set_nfft.restype = c_int
_gn_config_set_nfft.argtypes = [
    c_ulong,
    POINTER(_GNConfigPtr),
]

_gn_config_get_nfft = _libgen.gn_config_get_nfft
_gn_config_get_nfft.restype = c_int
_gn_config_get_nfft.argtypes = [
    POINTER(c_ulong),
    POINTER(_GNConfigPtr),
]

_gn_config_set_fft_navg = _libgen.gn_config_set_fft_navg
_gn_config_set_fft_navg.restype = c_int
_gn_config_set_fft_navg.argtypes = [
    c_ulong,
    POINTER(_GNConfigPtr),
]

_gn_config_set_win = _libgen.gn_config_set_win
_gn_config_set_win.restype = c_int
_gn_config_set_win.argtypes = [
    c_uint,
    POINTER(_GNConfigPtr),
]

_gn_config_set_ssb_fund = _libgen.gn_config_set_ssb_fund
_gn_config_set_ssb_fund.restype = c_int
_gn_config_set_ssb_fund.argtypes = [
    c_int,
    POINTER(_GNConfigPtr),
]

_gn_config_set_ssb_rest = _libgen.gn_config_set_ssb_rest
_gn_config_set_ssb_rest.restype = c_int
_gn_config_set_ssb_rest.argtypes = [
    c_int,
    POINTER(_GNConfigPtr),
]

_gn_config_set_max_harm_order = _libgen.gn_config_set_max_harm_order
_gn_config_set_max_harm_order.restype = c_int
_gn_config_set_max_harm_order.argtypes = [
    c_int,
    POINTER(_GNConfigPtr),
]

_gn_config_set_dnla_signal_type = _libgen.gn_config_set_dnla_signal_type
_gn_config_set_dnla_signal_type.restype = c_int
_gn_config_set_dnla_signal_type.argtypes = [
    c_uint,
    POINTER(_GNConfigPtr),
]

_gn_config_set_inla_fit = _libgen.gn_config_set_inla_fit
_gn_config_set_inla_fit.restype = c_int
_gn_config_set_inla_fit.argtypes = [
    c_uint,
    POINTER(_GNConfigPtr),
]

_gn_config_set_ramp_start = _libgen.gn_config_set_ramp_start
_gn_config_set_ramp_start.restype = c_int
_gn_config_set_ramp_start.argtypes = [
    c_ulong,
    POINTER(_GNConfigPtr),
]

_gn_config_set_ramp_stop = _libgen.gn_config_set_ramp_stop
_gn_config_set_ramp_stop.restype = c_int
_gn_config_set_ramp_stop.argtypes = [
    c_ulong,
    POINTER(_GNConfigPtr),
]

_gn_config_get_code_density_size = _libgen.gn_config_get_code_density_size
_gn_config_get_code_density_size.restype = c_int
_gn_config_get_code_density_size.argtypes = [
    POINTER(c_ulong),
    POINTER(_GNConfigPtr),
]

_gn_config_gen_tone = _libgen.gn_config_gen_tone
_gn_config_gen_tone.restype = c_int
_gn_config_gen_tone.argtypes = [
    c_uint,
    c_ulong,
    c_double,
    c_ulong,
    POINTER(c_double),
    POINTER(c_double),
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_config_gen_ramp = _libgen.gn_config_gen_ramp
_gn_config_gen_ramp.restype = c_int
_gn_config_gen_ramp.argtypes = [
    c_ulong,
    c_double,
    c_double,
    POINTER(_GNConfigPtr),
]

_gn_config_quantize = _libgen.gn_config_quantize
_gn_config_quantize.restype = c_int
_gn_config_quantize.argtypes = [
    c_ulong,
    c_double,
    c_int,
    c_double,
    POINTER(_GNConfigPtr),
]

_gn_config_histz_nla = _libgen.gn_config_histz_nla
_gn_config_histz_nla.restype = c_int
_gn_config_histz_nla.argtypes = [
    c_ulong,
    c_int,
    POINTER(_GNConfigPtr),
]

_gn_config_fftz = _libgen.gn_config_fftz
_gn_config_fftz.restype = c_int
_gn_config_fftz.argtypes = [
    c_ulong,
    c_int,
    c_ulong,
    c_ulong,
    c_uint,
    POINTER(_GNConfigPtr),
]

_gn_config_fa = _libgen.gn_config_fa
_gn_config_fa.restype = c_int
_gn_config_fa.argtypes = [
    c_double,
    POINTER(_GNConfigPtr),
]

_gn_config_fa_auto = _libgen.gn_config_fa_auto
_gn_config_fa_auto.restype = c_int
_gn_config_fa_auto.argtypes = [
    c_uint8,
    POINTER(_GNConfigPtr),
]

_gn_gen_ramp = _libgen.gn_gen_ramp
_gn_gen_ramp.restype = c_int
_gn_gen_ramp.argtypes = [
    POINTER(POINTER(c_double)),
    POINTER(_GNConfigPtr),
]

_gn_gen_real_tone = _libgen.gn_gen_real_tone
_gn_gen_real_tone.restype = c_int
_gn_gen_real_tone.argtypes = [
    POINTER(POINTER(c_double)),
    POINTER(_GNConfigPtr),
]

_gn_gen_complex_tone = _libgen.gn_gen_complex_tone
_gn_gen_complex_tone.restype = c_int
_gn_gen_complex_tone.argtypes = [
    POINTER(POINTER(c_double)),
    POINTER(POINTER(c_double)),
    POINTER(_GNConfigPtr),
]

_gn_quantize = _libgen.gn_quantize
_gn_quantize.restype = c_int
_gn_quantize.argtypes = [
    POINTER(POINTER(c_int32)),
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_fftz = _libgen.gn_fftz
_gn_fftz.restype = c_int
_gn_fftz.argtypes = [
    POINTER(POINTER(c_double)),
    POINTER(c_int32),
    POINTER(c_int32),
    POINTER(_GNConfigPtr),
]

_gn_histz = _libgen.gn_histz
_gn_histz.restype = c_int
_gn_histz.argtypes = [
    POINTER(POINTER(c_uint64)),
    POINTER(c_ulong),
    POINTER(c_int32),
    POINTER(_GNConfigPtr),
]

_gn_dnlz = _libgen.gn_dnlz
_gn_dnlz.restype = c_int
_gn_dnlz.argtypes = [
    POINTER(POINTER(c_double)),
    POINTER(c_ulong),
    POINTER(c_uint64),
    POINTER(_GNConfigPtr),
]

_gn_inlz = _libgen.gn_inlz
_gn_inlz.restype = c_int
_gn_inlz.argtypes = [
    POINTER(POINTER(c_double)),
    POINTER(c_ulong),
    POINTER(c_uint64),
    POINTER(_GNConfigPtr),
]

_gn_get_wfa_results = _libgen.gn_get_wfa_results
_gn_get_wfa_results.restype = c_int
_gn_get_wfa_results.argtypes = [
    POINTER(POINTER(c_char_p)),
    POINTER(POINTER(c_double)),
    POINTER(c_ulong),
    POINTER(c_int32),
    POINTER(_GNConfigPtr),
]

_gn_get_ha_results = _libgen.gn_get_ha_results
_gn_get_ha_results.restype = c_int
_gn_get_ha_results.argtypes = [
    POINTER(POINTER(c_char_p)),
    POINTER(POINTER(c_double)),
    POINTER(c_ulong),
    POINTER(c_uint64),
    POINTER(_GNConfigPtr),
]

_gn_get_dnla_results = _libgen.gn_get_dnla_results
_gn_get_dnla_results.restype = c_int
_gn_get_dnla_results.argtypes = [
    POINTER(POINTER(c_char_p)),
    POINTER(POINTER(c_double)),
    POINTER(c_ulong),
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_get_inla_results = _libgen.gn_get_inla_results
_gn_get_inla_results.restype = c_int
_gn_get_inla_results.argtypes = [
    POINTER(POINTER(c_char_p)),
    POINTER(POINTER(c_double)),
    POINTER(c_ulong),
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_get_fa_single_result = _libgen.gn_get_fa_single_result
_gn_get_fa_single_result.restype = c_int
_gn_get_fa_single_result.argtypes = [
    POINTER(c_double),
    c_char_p,
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]

_gn_get_fa_results = _libgen.gn_get_fa_results
_gn_get_fa_results.restype = c_int
_gn_get_fa_results.argtypes = [
    POINTER(POINTER(c_char_p)),
    POINTER(POINTER(c_double)),
    POINTER(c_ulong),
    POINTER(c_double),
    POINTER(_GNConfigPtr),
]


def config_free(
    c: GNConfig,
) -> int:
    _gn_config_free(byref(c._struct))


def config_gen_ramp(npts: int, ramp_start: int, ramp_stop: int, c: GNConfig = None) -> GNConfig:
    if c is None:
        c = GNConfig()
    
    npts = c_ulong(npts)
    ramp_start = c_double(ramp_start)
    ramp_stop = c_double(ramp_stop)

    ret = _gn_config_gen_ramp(npts, ramp_start, ramp_stop, byref(c._struct))
    if ret != 0:
        raise Exception("config_gen_ramp failed")
    return c


def config_gen_tone(
    ttype: int,
    npts: int,
    sample_rate: float,
    num_tones: int,
    tone_freq: float,
    tone_ampl: float,
    tone_phase: float,
    c: GNConfig = None
) -> GNConfig:
    if c is None:
        c = GNConfig()
    
    ttype = c_uint(ttype)
    npts = c_ulong(npts)
    sample_rate = c_double(sample_rate)
    num_tones = c_ulong(num_tones)
    double_array = c_double * num_tones.value
    tone_freq = (double_array)(*tone_freq)
    tone_ampl = (double_array)(*tone_ampl)
    tone_phase = (double_array)(*tone_phase)

    ret = _gn_config_gen_tone(
        ttype,
        npts,
        sample_rate,
        num_tones,
        tone_freq,
        tone_ampl,
        tone_phase,
        byref(c._struct),
    )
    if ret != 0:
        raise Exception("config_gen_tone failed")
    return c


def config_quantize(npts: int, fsr: float, qres: int, qnoise: float, c: GNConfig = None) -> GNConfig:
    if c is None:
        c = GNConfig()
    
    npts = c_ulong(npts)
    fsr = c_double(fsr)
    qres = c_int(qres)
    qnoise = c_double(qnoise)

    ret = _gn_config_quantize(npts, fsr, qres, qnoise, byref(c._struct))
    if ret != 0:
        raise Exception("config quantize failed")
    return c


def config_histz_nla(npts: int, qres: int, c: GNConfig = None) -> GNConfig:
    if c is None:
        c = GNConfig()
    
    npts = c_ulong(npts)
    qres = c_int(qres)

    ret = _gn_config_histz_nla(npts, qres, byref(c._struct))
    if ret != 0:
        raise Exception("config_histz_nla failed")
    return c


def config_fftz(
    npts: int, qres: int, navg: int, nfft: int, win: int, c: GNConfig = None
) -> GNConfig:
    if c is None:
        c = GNConfig()
    
    npts = c_ulong(npts)
    qres = c_int(qres)
    navg = c_ulong(navg)
    nfft = c_ulong(nfft)
    win = c_uint(win)

    ret = _gn_config_fftz(npts, qres, navg, nfft, win, byref(c._struct))
    if ret != 0:
        raise Exception("config_fftz failed")
    return c


def config_fa(fixed_tone_freq: float, c: GNConfig = None) -> GNConfig:
    if c is None:
        c = GNConfig()

    fixed_tone_freq = c_double(fixed_tone_freq)

    ret = _gn_config_fa(fixed_tone_freq, byref(c._struct))
    if ret != 0:
        raise Exception("config_fa failed")
    return c


def config_fa_auto(ssb_width: int, c: GNConfig = None):
    if c is None:
        c = GNConfig()
    ssb_width = c_uint8(ssb_width)

    ret = _gn_config_fa_auto(ssb_width, byref(c._struct))
    if ret != 0:
        raise Exception("config_fa_auto failed")
    return c


def gen_ramp(c: GNConfig) -> List[float]:
    awf = POINTER(c_double)()
    wf_len = c_ulong(0)
    _gn_config_get_npts(byref(wf_len), byref(c._struct))
    _gn_gen_ramp(byref(awf), byref(c._struct))
    return list(awf[0 : wf_len.value])


def gen_real_tone(c: GNConfig) -> List[float]:
    awf = POINTER(c_double)()
    wf_len = c_ulong(0)
    _gn_config_get_npts(byref(wf_len), byref(c._struct))
    _gn_gen_real_tone(byref(awf), byref(c._struct))
    return list(awf[0 : wf_len.value])


def gen_complex_tone(c: GNConfig) -> List[float]:
    awf_i = POINTER(c_double)()
    awf_q = POINTER(c_double)()
    wf_len = c_ulong(0)
    _gn_config_get_npts(byref(wf_len), byref(c._struct))
    _gn_gen_complex_tone(byref(awf_i), byref(awf_q), byref(c._struct))
    return (list(awf_i[0 : wf_len.value]), list(awf_q[0 : wf_len.value]))


def quantize(in_awf: list, c: GNConfig) -> List[int]:
    qwf = POINTER(c_int32)()
    wf_len = c_ulong(0)
    _gn_config_get_npts(byref(wf_len), byref(c._struct))
    double_array = c_double * wf_len.value
    in_awf_ptr = (double_array)(*in_awf)
    _gn_quantize(byref(qwf), in_awf_ptr, byref(c._struct))
    return list(qwf[0 : wf_len.value])


def fftz(in_qwfi: int, in_qwfq: int, c: GNConfig) -> List[float]:
    fft_out = POINTER(c_double)()
    wf_len = c_ulong(0)
    _gn_config_get_npts(byref(wf_len), byref(c._struct))
    int32_array = c_int32 * wf_len.value
    in_qwfi = (int32_array)(*in_qwfi)
    in_qwfq = (int32_array)(*in_qwfq)
    _gn_fftz(byref(fft_out), in_qwfi, in_qwfq, byref(c._struct))
    fft_len = c_ulong(0)
    _gn_config_get_nfft(byref(fft_len), byref(c._struct))
    out = list(fft_out[0 : 2 * fft_len.value])
    fft_out_i = [out[i] for i in range(len(out)) if i % 2 == 0]
    fft_out_q = [out[i] for i in range(len(out)) if i % 2 != 0]
    return fft_out_i, fft_out_q


def histz(in_qwf: int, c: GNConfig) -> List[int]:
    hist_out = POINTER(c_uint64)()
    wf_len = c_ulong(0)
    _gn_config_get_npts(byref(wf_len), byref(c._struct))
    int32_array = c_int32 * wf_len.value
    in_qwf = (int32_array)(*in_qwf)
    hist_len = c_ulong(0)
    _gn_histz(byref(hist_out), byref(hist_len), in_qwf, byref(c._struct))
    return list(hist_out[0 : hist_len.value])


def get_ha_results(hist_in: int, c: GNConfig) -> dict:
    cd_len = c_ulong(0)
    _gn_config_get_code_density_size(byref(cd_len), byref(c._struct))
    uint64_array = c_uint64 * cd_len.value
    hist_in = (uint64_array)(*hist_in)
    rkeys = POINTER(c_char_p)()
    rvalues = POINTER(c_double)()
    results_size = c_ulong(0)
    _gn_get_ha_results(
        byref(rkeys), byref(rvalues), byref(results_size), hist_in, byref(c._struct)
    )
    ha_results = dict()
    for i in range(results_size.value):
        ha_results[(rkeys[i]).decode("ascii")] = rvalues[i]
    return ha_results


def get_wfa_results(in_qwf: int, c: GNConfig) -> dict:
    wf_len = c_ulong(0)
    _gn_config_get_npts(byref(wf_len), byref(c._struct))
    int32_array = c_int32 * wf_len.value
    in_qwf = (int32_array)(*in_qwf)
    rkeys = POINTER(c_char_p)()
    rvalues = POINTER(c_double)()
    results_size = c_ulong(0)
    _gn_get_wfa_results(
        byref(rkeys), byref(rvalues), byref(results_size), in_qwf, byref(c._struct)
    )
    wfa_results = dict()
    for i in range(results_size.value):
        wfa_results[(rkeys[i]).decode("ascii")] = rvalues[i]
    return wfa_results


def get_fa_single_result(metric_name: str, fft_ilv: float, c: GNConfig) -> float:
    fft_len = c_ulong(0)
    _gn_config_get_nfft(byref(fft_len), byref(c._struct))
    fft_ilv_len = 2 * fft_len.value
    double_array = c_double * fft_ilv_len
    fft_ilv = (double_array)(*fft_ilv)
    metric_name_enc = metric_name.encode("utf-8")
    result = c_double(0)
    _gn_get_fa_single_result(byref(result), metric_name_enc, fft_ilv, byref(c._struct))
    return result.value


def get_fa_results(fft_ilv: float, c: GNConfig) -> dict:
    """
    Get Fourier analysis results.
    
    Args:
        ``fixed_tone_freq``: fixed tone frequency
        
        ``c``: GNConfig object

    Returns:
        Results as dict
    """
    fft_len = c_ulong(0)
    _gn_config_get_nfft(byref(fft_len), byref(c._struct))
    fft_ilv_len = 2 * fft_len.value
    double_array = c_double * fft_ilv_len
    fft_ilv = (double_array)(*fft_ilv)
    rkeys = POINTER(c_char_p)()
    rvalues = POINTER(c_double)()
    results_size = c_ulong(0)
    _gn_get_fa_results(
        byref(rkeys), byref(rvalues), byref(results_size), fft_ilv, byref(c._struct)
    )
    fa_results = dict()
    for i in range(results_size.value):
        fa_results[(rkeys[i]).decode("ascii")] = rvalues[i]
    return fa_results


def config_set_sample_rate(sample_rate: float, c: GNConfig) -> None:
    """
    Set sample rate.
    
    Args:
        ``sample_rate``: Sample rate in Hz
        
        ``c``: GNConfig object
    """
    _gn_config_set_sample_rate(sample_rate, byref(c._struct))


def config_code_format(code_format: int, c: GNConfig) -> None:
    """
    Configure code format.
    
    Args:
        ``code_format``: code format (Offset binary, Twos complement)

        ``c``: GNConfig object
    """
    code_format = c_uint(code_format)
    _gn_config_set_code_format(code_format, byref(c._struct))


class WaveformGen:
    """
    Waveform data generation for transmit devices
    """

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
        """
        Constructor for WaveformGen class.

        Args:
            ``npts`` (``int``): number of points required per waveform cycle

            ``freq`` (``int``): output frequency required in hz

            ``code_fmt`` (``int``): code format to get data in
                
                0: for binary offset
                
                1: for 2's complement
            
            ``res`` (``int``): code resolution
            
            ``v_ref_n`` (``float``): negative reference voltage
                
                Can be zero(0) for unipolar device
            
            ``v_ref_p`` (``float``): positive reference voltage
            
            ``v_min`` (``float``): minimum required voltage to generate
                
                Must be in the accepted reference voltage range
            
            ``v_max`` (``float``): maximum required voltage to generate
            
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
        """
        Lower required voltage limit
        """
        return self._v_min

    @v_min.setter
    def v_min(self, value):
        """
        Set Lower required voltage limit
        
        Args:
            ``value`` (``float``): Lower required voltage limit
        """
        if value < self._v_ref_n:
            raise Exception(
                "required lower voltage cannot be less than lower voltage reference"
            )
        self._v_min = value

    @property
    def v_max(self):
        """
        Upper required voltage limit
        """
        return self._v_max

    @v_max.setter
    def v_max(self, value):
        """
        Set Upper required voltage limit

        Args:
            ``value`` (``float``): Upper required voltage limit
        """
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
