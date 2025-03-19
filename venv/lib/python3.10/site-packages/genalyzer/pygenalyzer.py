# Copyright (C) 2024-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD OR GPL-2.0-or-later

"""
Python wrapper for Genalyzer Library (genalyzer_plus_plus)
"""
import ctypes as _ctypes
from ctypes.util import find_library as _find_library
from enum import IntEnum as _IntEnum
import os as _os
import sys as _sys
import numpy as _np
from numpy.ctypeslib import ndpointer as _ndptr

_c_bool = _ctypes.c_bool
_c_char_p = _ctypes.c_char_p
_c_double = _ctypes.c_double
_c_int = _ctypes.c_int
_c_int16 = _ctypes.c_int16
_c_int32 = _ctypes.c_int32
_c_int64 = _ctypes.c_int64
_c_size_t = _ctypes.c_size_t

_c_bool_p = _ctypes.POINTER(_c_bool)
_c_char_p_p = _ctypes.POINTER(_c_char_p)
_c_double_p = _ctypes.POINTER(_c_double)
_c_size_t_p = _ctypes.POINTER(_c_size_t)

_ndptr_f64_1d = _ndptr(dtype=_np.float64, ndim=1)
_ndptr_i16_1d = _ndptr(dtype=_np.int16, ndim=1)
_ndptr_i32_1d = _ndptr(dtype=_np.int32, ndim=1)
_ndptr_i64_1d = _ndptr(dtype=_np.int64, ndim=1)
_ndptr_u16_1d = _ndptr(dtype=_np.uint16, ndim=1)
_ndptr_u32_1d = _ndptr(dtype=_np.uint32, ndim=1)
_ndptr_u64_1d = _ndptr(dtype=_np.uint64, ndim=1)
del _ndptr

_module_dir = _os.path.dirname(__file__)
if "linux" == _sys.platform:
    _libpath = _find_library("genalyzer")
elif "win32" == _sys.platform:
    _libpath = _find_library("libgenalyzer.dll")
else:
    raise Exception("Platform '{}' is not supported.".format(_sys.platform))

if _libpath is None:
    raise OSError(2, "Could not find genalyzer C library")
_lib = _ctypes.cdll.LoadLibrary(_libpath)

del _find_library, _os, _sys

_lib.gn_set_string_termination(True)

"""
Wrapper Utilities
"""

_lib.gn_analysis_results_key_sizes.argtypes = [_c_size_t_p, _c_size_t, _c_int]
_lib.gn_analysis_results_size.argtypes = [_c_size_t_p, _c_int]


def _check_ndarray(a, dtype):
    if not isinstance(a, _np.ndarray):
        raise TypeError("Expected numpy.ndarray, got {}".format(type(a).__name__))
    if type(dtype) in [list, tuple]:
        if a.dtype not in dtype:
            raise TypeError(
                "Expected dtype in [{}], got {}".format(", ".join(dtype), a.dtype)
            )
    elif dtype != a.dtype:
        raise TypeError("Expected dtype '{}', got {}".format(dtype, a.dtype))
    return a.dtype


def _raise_exception_on_failure(result=1):
    if result:
        size = _c_size_t(0)
        _lib.gn_error_string_size(_ctypes.byref(size))
        buf = _ctypes.create_string_buffer(size.value)
        result = _lib.gn_error_string(buf, len(buf))
        if result:
            msg2 = (
                "An error was reported, but the error message could not be retrieved."
            )
        else:
            msg2 = buf.value.decode("utf-8")
            if not msg2:
                msg2 = "An error was reported, but the error message was empty."
        raise Exception("gnnalysis error:\n\t{}".format(msg2))


def _enum_value(enumeration, enumerator):
    value = _c_int(0)
    enumeration = bytes(enumeration, "utf-8")
    enumerator = bytes(enumerator, "utf-8")
    result = _lib.gn_enum_value(_ctypes.byref(value), enumeration, enumerator)
    _raise_exception_on_failure(result)
    return value.value


def _get_analysis_containers(analysis_type):
    size = _c_size_t(0)
    result = _lib.gn_analysis_results_size(_ctypes.byref(size), analysis_type)
    _raise_exception_on_failure(result)
    size = size.value
    key_sizes = (_c_size_t * size)()
    result = _lib.gn_analysis_results_key_sizes(key_sizes, size, analysis_type)
    _raise_exception_on_failure(result)
    keys = (_c_char_p * size)()
    values = (_c_double * size)()
    for i in range(size):
        keys[i] = _ctypes.cast(
            _ctypes.create_string_buffer(int(key_sizes[i])), _c_char_p
        )
    return keys, values


def _get_key_value_arrays(d):
    if not isinstance(d, dict):
        raise TypeError("Expected dict, got {}".format(type(d).__name__))
    size = len(d)
    keys, values = list(d.keys()), list(d.values())
    ckeys = (_c_char_p * size)()
    cvalues = (_c_double * size)()
    for i in range(size):
        ckeys[i] = _ctypes.cast(
            _ctypes.create_string_buffer(bytes(keys[i], "utf-8")), _c_char_p
        )
        cvalues[i] = values[i]
    return ckeys, cvalues


def _make_results_dict(keys, values):
    results = dict()
    for i in range(len(keys)):
        key = keys[i].decode("utf-8")
        results[key] = values[i]
    return results


"""
Enumerations
"""


class _AnalysisType(_IntEnum):  # Intentionally private
    DNL = _enum_value("AnalysisType", "DNL")
    FOURIER = _enum_value("AnalysisType", "Fourier")
    HISTOGRAM = _enum_value("AnalysisType", "Histogram")
    INL = _enum_value("AnalysisType", "INL")
    WAVEFORM = _enum_value("AnalysisType", "Waveform")


class CodeFormat(_IntEnum):
    """Enumerates binary code formats

    Attributes:
        ``OFFSET_BINARY`` : Offset Binary

        ``TWOS_COMPLEMENT`` : Two's Complement
    """
    OFFSET_BINARY = _enum_value("CodeFormat", "OffsetBinary")
    TWOS_COMPLEMENT = _enum_value("CodeFormat", "TwosComplement")


class DnlSignal(_IntEnum):
    """Enumerates signal types for which DNL can be computed

    Attributes:
        ``RAMP`` : Ramp

        ``TONE`` : Tone (Sinusoid)
    """
    RAMP = _enum_value("DnlSignal", "Ramp")
    TONE = _enum_value("DnlSignal", "Tone")


class FaCompTag(_IntEnum):
    """Enumerates Fourier analysis component tags

    Attributes:
        ``DC`` : DC component (always Bin 0)

        ``SIGNAL`` : Signal component

        ``HD`` : Harmonic distortion

        ``IMD`` : Intermodulation distortion

        ``ILOS`` : Interleaving offset component

        ``ILGT`` : Interleaving gain/timing/BW component

        ``CLK`` : Clock component

        ``USERDIST`` : User-designated distortion

        ``NOISE`` : Noise component (e.g. WorstOther)
    """
    DC = _enum_value("FACompTag", "DC")
    SIGNAL = _enum_value("FACompTag", "Signal")
    HD = _enum_value("FACompTag", "HD")
    IMD = _enum_value("FACompTag", "IMD")
    ILOS = _enum_value("FACompTag", "ILOS")
    ILGT = _enum_value("FACompTag", "ILGT")
    CLK = _enum_value("FACompTag", "CLK")
    USERDIST = _enum_value("FACompTag", "UserDist")
    NOISE = _enum_value("FACompTag", "Noise")


class FaSsb(_IntEnum):
    """Enumerates the component categories for which the number of single side bins (SSB) can be set

    Attributes:
        ``DEFAULT`` : Default SSB (applies to auto-generated components)

        ``DC`` : SSB for DC component

        ``SIGNAL`` : SSB for Signal components

        ``WO`` : SSB for WorstOther components
    """
    DEFAULT = _enum_value("FASsb", "Default")
    DC = _enum_value("FASsb", "DC")
    SIGNAL = _enum_value("FASsb", "Signal")
    WO = _enum_value("FASsb", "WO")


class FreqAxisFormat(_IntEnum):
    """Enumerates frequency axis formats

    Attributes:
        ``BINS`` : Bins

        ``FREQ`` : Frequency

        ``NORM`` : Normalized
    """
    BINS = _enum_value("FreqAxisFormat", "Bins")
    FREQ = _enum_value("FreqAxisFormat", "Freq")
    NORM = _enum_value("FreqAxisFormat", "Norm")


class FreqAxisType(_IntEnum):
    """Enumerates frequency axis types

    Attributes:
        ``DC_CENTER`` : DC centered, e.g. [-fs/2, fs/2) (complex FFT only)

        ``DC_LEFT`` : DC on left, e.g. [0, fs) (complex FFT only)

        ``REAL`` : Real axis, e.g. [0, fs/2] (real FFT only)
    """
    DC_CENTER = _enum_value("FreqAxisType", "DcCenter")
    DC_LEFT = _enum_value("FreqAxisType", "DcLeft")
    REAL = _enum_value("FreqAxisType", "Real")


class InlLineFit(_IntEnum):
    """Enumerates INL line fitting options

    Attributes:
        ``BEST_FIT`` : Best fit

        ``END_FIT`` : End fit

        ``NO_FIT`` : No fit
    """
    BEST_FIT = _enum_value("InlLineFit", "BestFit")
    END_FIT = _enum_value("InlLineFit", "EndFit")
    NO_FIT = _enum_value("InlLineFit", "NoFit")


class RfftScale(_IntEnum):
    """Enumerates real FFT scaling options

    Attributes:
        ``DBFS_DC`` : Full-scale sinusoid measures -3 dBFS

        ``DBFS_SIN`` : Full-scale sinusoid measures  0 dBFS

        ``NATIVE`` : Full-scale sinusoid measures -6 dBFS
    """
    DBFS_DC = _enum_value("RfftScale", "DbfsDc")
    DBFS_SIN = _enum_value("RfftScale", "DbfsSin")
    NATIVE = _enum_value("RfftScale", "Native")


class Window(_IntEnum):
    """Enumerates window functions

    Attributes:
        ``BLACKMAN_HARRIS`` : Blackman-Harris

        ``HANN`` : Hann ("Hanning")

        ``NO_WINDOW`` : No window (Rectangular)
    """
    BLACKMAN_HARRIS = _enum_value("Window", "BlackmanHarris")
    HANN = _enum_value("Window", "Hann")
    NO_WINDOW = _enum_value("Window", "NoWindow")


del _IntEnum


"""
API Utilities
"""


def _version_string():
    size = _c_size_t(0)
    _lib.gn_version_string_size(_ctypes.byref(size))
    buf = _ctypes.create_string_buffer(size.value)
    result = _lib.gn_version_string(buf, len(buf))
    _raise_exception_on_failure(result)
    return buf.value.decode("utf-8")


"""
Array Operations
"""

_lib.gn_abs.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t]
_lib.gn_angle.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t]
_lib.gn_db.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t]
_lib.gn_db10.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t]
_lib.gn_db20.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t]
_lib.gn_norm.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t]


def abs(a):
    """
    abs

    Parameters
    ----------
    a :

    Returns
    -------
    out :

    """
    _check_ndarray(a, "complex128")
    out = _np.empty(a.size, dtype="float64")
    af64 = a.view("float64")
    result = _lib.gn_abs(out, out.size, af64, af64.size)
    _raise_exception_on_failure(result)
    return out


def angle(a):
    """
    angle

    Parameters
    ----------
    a :

    Returns
    -------
    out :

    """
    _check_ndarray(a, "complex128")
    out = _np.empty(a.size, dtype="float64")
    af64 = a.view("float64")
    result = _lib.gn_angle(out, out.size, af64, af64.size)
    _raise_exception_on_failure(result)
    return out


def db(a):
    """
    db

    Parameters
    ----------
    a :

    Returns
    -------
    out :

    """
    _check_ndarray(a, "complex128")
    out = _np.empty(a.size, dtype="float64")
    af64 = a.view("float64")
    result = _lib.gn_db(out, out.size, af64, af64.size)
    _raise_exception_on_failure(result)
    return out


def db10(a):
    """
    db10

    Parameters
    ----------
    a :

    Returns
    -------
    out :

    """
    _check_ndarray(a, "float64")
    out = _np.empty(a.size, dtype="float64")
    result = _lib.gn_db10(out, out.size, a, a.size)
    _raise_exception_on_failure(result)
    return out


def db20(a):
    """
    db20

    Parameters
    ----------
    a :

    Returns
    -------
    out :

    """
    _check_ndarray(a, "float64")
    out = _np.empty(a.size, dtype="float64")
    result = _lib.gn_db20(out, out.size, a, a.size)
    _raise_exception_on_failure(result)
    return out


def norm(a):
    """
    norm

    Parameters
    ----------
    a :

    Returns
    -------
    out :

    """
    _check_ndarray(a, "complex128")
    out = _np.empty(a.size, dtype="float64")
    af64 = a.view("float64")
    result = _lib.gn_norm(out, out.size, af64, af64.size)
    _raise_exception_on_failure(result)
    return out


"""
Code Density
"""

_lib.gn_code_axis.argtypes = [_ndptr_f64_1d, _c_size_t, _c_int, _c_int]
_lib.gn_code_axisx.argtypes = [_ndptr_f64_1d, _c_size_t, _c_int64, _c_int64]
_lib.gn_code_density_size.argtypes = [_c_size_t_p, _c_int, _c_int]
_lib.gn_code_densityx_size.argtypes = [_c_size_t_p, _c_int64, _c_int64]
_lib.gn_dnl.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_u64_1d, _c_size_t, _c_int]
_lib.gn_dnl_analysis.argtypes = [
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
]
_lib.gn_hist16.argtypes = [
    _ndptr_u64_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _c_int,
    _c_int,
    _c_bool,
]
_lib.gn_hist32.argtypes = [
    _ndptr_u64_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _c_int,
    _c_int,
    _c_bool,
]
_lib.gn_hist64.argtypes = [
    _ndptr_u64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _c_int,
    _c_int,
    _c_bool,
]
_lib.gn_histx16.argtypes = [
    _ndptr_u64_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _c_int64,
    _c_int64,
    _c_bool,
]
_lib.gn_histx32.argtypes = [
    _ndptr_u64_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _c_int64,
    _c_int64,
    _c_bool,
]
_lib.gn_histx64.argtypes = [
    _ndptr_u64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _c_int64,
    _c_int64,
    _c_bool,
]
_lib.gn_hist_analysis.argtypes = [
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _ndptr_u64_1d,
    _c_size_t,
]
_lib.gn_inl.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t, _c_int]
_lib.gn_inl_analysis.argtypes = [
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
]


def code_axis(n, fmt=CodeFormat.TWOS_COMPLEMENT):
    """
    code_axis

    Parameters
    ----------
    n :
    fmt :

    Returns
    -------
    out :

    """
    size = _c_size_t(0)
    result = _lib.gn_code_density_size(_ctypes.byref(size), n, fmt)
    _raise_exception_on_failure(result)
    out = _np.empty(size.value, dtype="float64")
    result = _lib.gn_code_axis(out, out.size, n, fmt)
    _raise_exception_on_failure(result)
    return out


def code_axisx(min_code, max_code):
    """
    code_axisx

    Parameters
    ----------
    min_code :
    max_code :

    Returns
    -------
    out :

    """
    size = _c_size_t(0)
    result = _lib.gn_code_densityx_size(_ctypes.byref(size), min_code, max_code)
    _raise_exception_on_failure(result)
    out = _np.empty(size.value, dtype="float64")
    result = _lib.gn_code_axisx(out, out.size, min_code, max_code)
    _raise_exception_on_failure(result)
    return out


def dnl(a, signal_type=DnlSignal.TONE):
    """
    dnl

    Parameters
    ----------
    a           : ndarray of type 'uint64'
    signal_type : DnlSignal
                  Signal type

    Returns
    -------
    out : ndarray of type 'float64'
          DNL data
    """
    _check_ndarray(a, "uint64")
    out = _np.empty(a.size, dtype="float64")
    result = _lib.gn_dnl(out, out.size, a, a.size, signal_type)
    _raise_exception_on_failure(result)
    return out


def dnl_analysis(a):
    """

    Parameters
    ----------
    a

    Returns
    -------
    results : dict
        Every Key:Value pair in the dictionary is str:float.

        ====================================================================================
          Key             |  Description
        ====================================================================================
          min             |  Minumum value
          max             |  Maximum value
          avg             |  Average value
          rms             |  RMS value
          min_index       |  Index of first occurence of minimum value
          max_index       |  Index of first occurence of maximum value
          first_nm_index  |  Index of first non-missing code
          last_nm_index   |  Index of last non-missing code
          nm_range        |  Non-missing code range (1 + (last_nm_index - first_nm_index))
        ====================================================================================

    """
    _check_ndarray(a, "float64")
    keys, values = _get_analysis_containers(_AnalysisType.DNL)
    result = _lib.gn_dnl_analysis(keys, len(keys), values, len(values), a, a.size)
    _raise_exception_on_failure(result)
    results = _make_results_dict(keys, values)
    return results


def hist(a, n, fmt=CodeFormat.TWOS_COMPLEMENT):
    """
    hist

    Parameters
    ----------
    a :
    n :
    fmt :

    Returns
    -------
    out :

    """
    dtype = _check_ndarray(a, ["int16", "int32", "int64"])
    size = _c_size_t(0)
    result = _lib.gn_code_density_size(_ctypes.byref(size), n, fmt)
    _raise_exception_on_failure(result)
    out = _np.zeros(size.value, dtype="uint64")
    if "int16" == dtype:
        result = _lib.gn_hist16(out, out.size, a, a.size, n, fmt, False)
    elif "int32" == dtype:
        result = _lib.gn_hist32(out, out.size, a, a.size, n, fmt, False)
    else:
        result = _lib.gn_hist64(out, out.size, a, a.size, n, fmt, False)
    _raise_exception_on_failure(result)
    return out


def histx(a, min_code, max_code):
    """
    hist

    Parameters
    ----------
    a :
    min_code :
    max_code :

    Returns
    -------
    out :

    """
    dtype = _check_ndarray(a, ["int16", "int32", "int64"])
    size = _c_size_t(0)
    result = _lib.gn_code_densityx_size(_ctypes.byref(size), min_code, max_code)
    _raise_exception_on_failure(result)
    out = _np.zeros(size.value, dtype="uint64")
    if "int16" == dtype:
        result = _lib.gn_histx16(out, out.size, a, a.size, min, max, False)
    elif "int32" == dtype:
        result = _lib.gn_histx32(out, out.size, a, a.size, min, max, False)
    else:
        result = _lib.gn_histx64(out, out.size, a, a.size, min, max, False)
    _raise_exception_on_failure(result)
    return out


def hist_analysis(a):
    """

    Parameters
    ----------
    a

    Returns
    -------
    results : dict
        Every Key:Value pair in the dictionary is str:float.

        ================================================================================
          Key             |  Description
        ================================================================================
          sum             |  Sum of all histogram bins
          first_nz_index  |  First non-zero bin
          last_nz_index   |  Last non-zero bin
          nz_range        |  Non-zero bin range (1 + (last_nz_index - first_nz_index))
        ================================================================================

    """
    _check_ndarray(a, "uint64")
    keys, values = _get_analysis_containers(_AnalysisType.HISTOGRAM)
    result = _lib.gn_hist_analysis(keys, len(keys), values, len(values), a, a.size)
    _raise_exception_on_failure(result)
    results = _make_results_dict(keys, values)
    return results


def inl(a, fit=InlLineFit.BEST_FIT):
    """
    inl

    Parameters
    ----------
    a   : ndarray of dtype 'float64'
          DNL data
    fit : InlLineFit
          Line fit option

    Returns
    -------
    out : ndarray of type 'float64'
          INL data
    """
    _check_ndarray(a, "float64")
    out = _np.empty(a.size, dtype="float64")
    result = _lib.gn_inl(out, out.size, a, a.size, fit)
    _raise_exception_on_failure(result)
    return out


def inl_analysis(a):
    """

    Parameters
    ----------
    a

    Returns
    -------
    results : dict
        Every Key:Value pair in the dictionary is str:float.

        ===========================================================
          Key        |  Description
        ===========================================================
          min        |  Minumum value
          max        |  Maximum value
          min_index  |  Index of first occurence of minimum value
          max_index  |  Index of first occurence of maximum value
        ===========================================================

    """
    _check_ndarray(a, "float64")
    keys, values = _get_analysis_containers(_AnalysisType.INL)
    result = _lib.gn_inl_analysis(keys, len(keys), values, len(values), a, a.size)
    _raise_exception_on_failure(result)
    results = _make_results_dict(keys, values)
    return results


"""
Fourier Analysis
"""

_lib.gn_fft_analysis.argtypes = [
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _c_char_p,
    _ndptr_f64_1d,
    _c_size_t,
    _c_size_t,
    _c_int,
]
_lib.gn_fft_analysis_results_key_sizes.argtypes = [
    _c_size_t_p,
    _c_size_t,
    _c_char_p,
    _c_size_t,
    _c_size_t,
]
_lib.gn_fft_analysis_results_size.argtypes = [
    _c_size_t_p,
    _c_char_p,
    _c_size_t,
    _c_size_t,
]


def fft_analysis(test_key, a, nfft, axis_type=FreqAxisType.DC_LEFT):
    """Returns all Fourier analysis results

    Args:
        ``test_key`` (``string``) : Key value to the Fourier Analysis object created (through gn_fa_create)

        ``a`` (``ndarray``) : FFT data of type 'complex128' or 'float64'

        ``nfft`` (``int``) : FFT size

        axis_type (``FreqAxisType``) : Frequency axis type

    Returns:
        ``results`` (``dict``) : Dictionary containing all Fourier analysis results

    Notes:
        Every Key:Value pair in the dictionary is ``str``:``float``.

        The dictionary contains the following keys:
            ``signaltype`` : Signal type: 0=Real, 1=Complex

            ``nfft`` : FFT size

            ``datasize`` : Data size

            ``fbin`` : Frequency bin size (Hz)

            ``fdata`` : Data rate (S/s)

            ``fsample`` : Sample rate (S/s)

            ``fshift`` : Shift frequency (Hz)

            ``fsnr`` : Full-scale-to-noise ratio (a.k.a. "SNRFS") (dB)

            ``snr`` : Signal-to-noise ratio (dB)

            ``sinad`` : Signal-to-noise-and-distortion ratio (dB)

            ``sfdr`` : Spurious-free dynamic range (dB)

            ``abn`` : Average bin noise (dBFS)

            ``nsd`` : Noise spectral density (dBFS/Hz)

            ``carrierindex`` : Order index of the Carrier tone

            ``maxspurindex`` : Order index of the MaxSpur tone

            ``ab_width`` : Analysis band width (Hz)

            ``ab_i1`` : Analysis band first index

            ``ab_i2`` : Analysis band last index

            ``{PREFIX}_nbins`` : Number of bins associated with PREFIX

            ``{PREFIX}_rss`` : Root-sum-square associated with PREFIX

            ``{TONEKEY}:ffinal`` : Tone final frequency (Hz)

            ``{TONEKEY}:freq`` : Tone frequency (Hz)

            ``{TONEKEY}:fwavg`` : Tone weighted-average frequency (Hz)

            ``{TONEKEY}:i1`` : Tone first index

            ``{TONEKEY}:i2`` : Tone last index

            ``{TONEKEY}:inband`` : 1: tone is in-band; 0: tone is out-of-band

            ``{TONEKEY}:mag`` : Tone magnitude

            ``{TONEKEY}:mag_dbc`` : Tone magnitude relative to carrier (dBc)

            ``{TONEKEY}:mag_dbfs`` : Tone magnitude relative to full-scale (dBFS)

            ``{TONEKEY}:nbins`` : Tone number of bins

            ``{TONEKEY}:orderindex`` : Tone order index

            ``{TONEKEY}:phase`` : Tone phase (rad)

            ``{TONEKEY}:phase_c`` : Tone phase relative to carrier (rad)

            ``{TONEKEY}:tag`` : Tone tag
    """
    test_key = bytes(test_key, "utf-8")
    dtype = _check_ndarray(a, ["complex128", "float64"])
    af64 = a.view("float64") if "complex128" == dtype else a
    size = _c_size_t(0)
    result = _lib.gn_fft_analysis_results_size(
        _ctypes.byref(size), test_key, af64.size, nfft
    )
    _raise_exception_on_failure(result)
    size = size.value
    key_sizes = (_c_size_t * size)()
    result = _lib.gn_fft_analysis_results_key_sizes(
        key_sizes, size, test_key, af64.size, nfft
    )
    _raise_exception_on_failure(result)
    keys = (_c_char_p * size)()
    values = (_c_double * size)()
    for i in range(size):
        keys[i] = _ctypes.cast(
            _ctypes.create_string_buffer(int(key_sizes[i])), _c_char_p
        )
    result = _lib.gn_fft_analysis(
        keys, size, values, size, test_key, af64, af64.size, nfft, axis_type
    )
    _raise_exception_on_failure(result)
    results = _make_results_dict(keys, values)
    return results


"""
Fourier Analysis Configuration
"""

_lib.gn_fa_analysis_band.argtypes = [_c_char_p, _c_double, _c_double]
_lib.gn_fa_analysis_band_e.argtypes = [_c_char_p, _c_char_p, _c_char_p]
_lib.gn_fa_clk.argtypes = [_c_char_p, _ndptr_i32_1d, _c_size_t, _c_bool]
_lib.gn_fa_create.argtypes = [_c_char_p]
_lib.gn_fa_fdata.argtypes = [_c_char_p, _c_double]
_lib.gn_fa_fdata_e.argtypes = [_c_char_p, _c_char_p]
_lib.gn_fa_fixed_tone.argtypes = [_c_char_p, _c_char_p, _c_int, _c_double, _c_int]
_lib.gn_fa_fixed_tone_e.argtypes = [_c_char_p, _c_char_p, _c_int, _c_char_p, _c_int]
_lib.gn_fa_fsample.argtypes = [_c_char_p, _c_double]
_lib.gn_fa_fsample_e.argtypes = [_c_char_p, _c_char_p]
_lib.gn_fa_fshift.argtypes = [_c_char_p, _c_double]
_lib.gn_fa_fshift_e.argtypes = [_c_char_p, _c_char_p]
_lib.gn_fa_ilv.argtypes = [_c_char_p, _ndptr_i32_1d, _c_size_t, _c_bool]
_lib.gn_fa_load.argtypes = [_c_char_p, _c_size_t, _c_char_p, _c_char_p]
_lib.gn_fa_max_tone.argtypes = [_c_char_p, _c_char_p, _c_int, _c_int]
_lib.gn_fa_preview.argtypes = [_c_char_p, _c_size_t, _c_char_p, _c_bool]
_lib.gn_fa_remove_comp.argtypes = [_c_char_p, _c_char_p]
_lib.gn_fa_var.argtypes = [_c_char_p, _c_char_p, _c_double]


def fa_analysis_band(test_key, center, width):
    """
    Configure analysis band

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``center`` (``float``) : Analysis band center (Hz)

        ``width`` (``float``) : Analysis band width (Hz)
    """
    test_key = bytes(test_key, "utf-8")
    if isinstance(center, str) and isinstance(width, str):
        center = bytes(center, "utf-8")
        width = bytes(width, "utf-8")
        result = _lib.gn_fa_analysis_band_e(test_key, center, width)
    else:
        result = _lib.gn_fa_analysis_band(test_key, center, width)
    _raise_exception_on_failure(result)


def fa_clk(test_key, x, as_noise=False):
    """
    Treat clock components as noise

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``x`` (``list``) : Array of clock divisors

        ``as_noise`` (``bool``) : If true, CLK components will be treated as noise
    """
    test_key = bytes(test_key, "utf-8")
    x = _np.array(x, dtype="int32")
    result = _lib.gn_fa_clk(test_key, x, x.size, as_noise)
    _raise_exception_on_failure(result)


def fa_conv_offset(test_key, enable):
    """
    Enable converter offset

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``enable`` (``bool``) : If true, enable converter offset
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_conv_offset(test_key, enable)
    _raise_exception_on_failure(result)


def fa_create(test_key):
    """
    Create ``fourier_analysis`` object

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_create(test_key)
    _raise_exception_on_failure(result)


def fa_dc(test_key, as_dist):
    """
    Treat DC as distortion

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``as_dist`` (``bool``) : If true, treat DC as distortion
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_dc(test_key, as_dist)
    _raise_exception_on_failure(result)


def fa_fdata(test_key, f):
    """
    Configure fdata

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``f`` (``float``) : fdata
    """
    test_key = bytes(test_key, "utf-8")
    if isinstance(f, str):
        f = bytes(f, "utf-8")
        result = _lib.gn_fa_fdata_e(test_key, f)
    else:
        result = _lib.gn_fa_fdata(test_key, f)
    _raise_exception_on_failure(result)


def fa_fixed_tone(test_key, comp_key, tag, freq, ssb=-1):
    """
    Configure fixed tone

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``comp_key`` (``str``) : Component key

        ``tag`` (``FACompTag``) : Component tag

        ``freq`` (``float``) : Frequency (Hz)

        ``ssb`` (``int``) : Single side bin
    """
    test_key = bytes(test_key, "utf-8")
    comp_key = bytes(comp_key, "utf-8")
    if isinstance(freq, str):
        freq = bytes(freq, "utf-8")
        result = _lib.gn_fa_fixed_tone_e(test_key, comp_key, tag, freq, ssb)
    else:
        result = _lib.gn_fa_fixed_tone(test_key, comp_key, tag, freq, ssb)
    _raise_exception_on_failure(result)


def fa_fsample(test_key, f):
    """
    Configure fsample

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``f`` (``float``) : fsample
    """
    test_key = bytes(test_key, "utf-8")
    if isinstance(f, str):
        f = bytes(f, "utf-8")
        result = _lib.gn_fa_fsample_e(test_key, f)
    else:
        result = _lib.gn_fa_fsample(test_key, f)
    _raise_exception_on_failure(result)


def fa_fshift(test_key, f):
    """
    Configure fshift

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``f`` (``float``) : fshift
    """
    test_key = bytes(test_key, "utf-8")
    if isinstance(f, str):
        f = bytes(f, "utf-8")
        result = _lib.gn_fa_fshift_e(test_key, f)
    else:
        result = _lib.gn_fa_fshift(test_key, f)
    _raise_exception_on_failure(result)


def fa_fund_images(test_key, enable):
    """
    Enable fundamental images

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``enable`` (``bool``) : If true, enable fundamental images
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_fund_images(test_key, enable)
    _raise_exception_on_failure(result)


def fa_hd(test_key, n):
    """
    Configure maximum harmonic order

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``n`` (``int``) : Order of harmonic distortion, i.e., the maximum harmonic
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_hd(test_key, n)
    _raise_exception_on_failure(result)


def fa_ilv(test_key, x, as_noise=False):
    """
    Configure interleaving factors

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``x`` (``list``) : Array of interleaving factors

        ``as_noise`` (``bool``) : If true, interleaving factors will be treated as noise
    """
    
    test_key = bytes(test_key, "utf-8")
    x = _np.array(x, dtype="int32")
    result = _lib.gn_fa_ilv(test_key, x, x.size, as_noise)
    _raise_exception_on_failure(result)


def fa_imd(test_key, n):
    """
    Configure maximum intermodulation order

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``n`` (``int``) : Order of intermodulation distortion
    """    
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_imd(test_key, n)
    _raise_exception_on_failure(result)


def fa_load(filename, test_key=""):
    """
    Load object-key from file

    Args:
        ``filename`` (``str``) : File name

        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)
    """    
    filename = bytes(filename, "utf-8")
    test_key = bytes(test_key, "utf-8")
    size = _c_size_t(0)
    result = _lib.gn_fa_load_key_size(_ctypes.byref(size), filename, test_key)
    _raise_exception_on_failure(result)
    buf = _ctypes.create_string_buffer(size.value)
    result = _lib.gn_fa_load(buf, len(buf), filename, test_key)
    _raise_exception_on_failure(result)
    return buf.value.decode("utf-8")


def fa_max_tone(test_key, comp_key, tag, ssb=-1):
    """
    Configure component-key to select peak tone

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``comp_key`` (``str``) : Component key

        ``tag`` (``FACompTag``) : Tag

        ``ssb`` (``int``) : Number of single-side bins
    """
    test_key = bytes(test_key, "utf-8")
    comp_key = bytes(comp_key, "utf-8")
    result = _lib.gn_fa_max_tone(test_key, comp_key, tag, ssb)
    _raise_exception_on_failure(result)


def fa_preview(test_key, cplx=False):
    """
    Preview ``fourier_analysis`` object

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``cplx`` (``bool``) : If true, preview will include complex components
    """
    test_key = bytes(test_key, "utf-8")
    size = _c_size_t(0)
    result = _lib.gn_fa_preview_size(_ctypes.byref(size), test_key, cplx)
    _raise_exception_on_failure(result)
    buf = _ctypes.create_string_buffer(size.value)
    result = _lib.gn_fa_preview(buf, len(buf), test_key, cplx)
    _raise_exception_on_failure(result)
    return buf.value.decode("utf-8")


def fa_quad_errors(test_key, enable):
    """
    Enable quadrature errors

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``enable`` (``bool``) : If true, enable quadrature errors
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_quad_errors(test_key, enable)
    _raise_exception_on_failure(result)


def fa_remove_comp(test_key, comp_key):
    """
    Remove component

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``comp_key`` (``str``) : Component key
    """
    test_key = bytes(test_key, "utf-8")
    comp_key = bytes(comp_key, "utf-8")
    result = _lib.gn_fa_remove_comp(test_key, comp_key)
    _raise_exception_on_failure(result)


def fa_reset(test_key):
    """
    Reset object

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_reset(test_key)
    _raise_exception_on_failure(result)


def fa_ssb(test_key, group, n):
    """
    Configure number of single-sideband bins

    Args:
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``group`` (``FASsb``) : SSB Group

        ``n`` (``int``) : Number of single-sideband bins
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_ssb(test_key, group, n)
    _raise_exception_on_failure(result)


def fa_ssb_dc(test_key, n):
    """
    Configure number of single-sideband bins for DC

    Args:

        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``n`` (``int``) : Number of single-sideband bins
    """
    print("fa_ssb_dc(test_key, n) is deprecated; use fa_ssb(test_key, FaSsb.DC, n)")
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_ssb(test_key, FaSsb.DC, n)
    _raise_exception_on_failure(result)


def fa_ssb_def(test_key, n):
    """
    Configure default number of single-sideband bins for auto-generated components

    Args:
    
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``n`` (``int``) : Number of single-sideband bins
    """
    print("fa_ssb_def(test_key, n) is deprecated; use fa_ssb(test_key, FaSsb.DEFAULT, n)")
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_ssb(test_key, FaSsb.DEFAULT, n)
    _raise_exception_on_failure(result)


def fa_ssb_wo(test_key, n):
    """
    Configure number of single-sideband bins for WO component

    Args:
        
        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``n`` (``int``) : Number of single-sideband bins
    """
    print("fa_ssb_wo(test_key, n) is deprecated; use fa_ssb(test_key, FaSsb.WO, n)")
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_ssb(test_key, FaSsb.WO, n)
    _raise_exception_on_failure(result)


def fa_var(test_key, name, value):
    """
    Set value of variable in object

    Args:

        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``name`` (``str``) : Variable name

        ``value`` (``float``) : Variable value
    """
    test_key = bytes(test_key, "utf-8")
    name = bytes(name, "utf-8")
    result = _lib.gn_fa_var(test_key, name, value)
    _raise_exception_on_failure(result)


def fa_wo(test_key, n):
    """
    Configure number of WO components

    Args:

        ``test_key`` (``str``) : Test key (key to a Fourier Analysis object)

        ``n`` (``int``) : Number of worst others
    """
    test_key = bytes(test_key, "utf-8")
    result = _lib.gn_fa_wo(test_key, n)
    _raise_exception_on_failure(result)


"""
Fourier Analysis Results
"""

_lib.gn_fa_result_string.argtypes = [
    _c_char_p,
    _c_size_t,
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _c_char_p,
]
_lib.gn_fa_result_string_size.argtypes = [
    _c_size_t_p,
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _c_char_p,
]


def _get_annot_boxes(axis_type, datasize, bottom, height, x1, x2, xscalar):
    boxes = []
    lbound = 0
    rbound = datasize - 1
    if FreqAxisType.DC_CENTER == axis_type:
        lbound -= datasize // 2
        rbound -= datasize // 2
        if rbound < x1:
            x1 -= datasize
        if rbound < x2:
            x2 -= datasize
    if x1 <= x2:  # 1 box, x1->x2
        left = (x1 - 0.5) * xscalar
        width = ((x2 - x1) + 1) * xscalar
        boxes.append((left, bottom, width, height))
    else:  # x2 < x1: 2 boxes, x1->rbound, lbound->x2
        if x1 < rbound:
            left = (x1 - 0.5) * xscalar
            width = rbound * xscalar - left
            boxes.append((left, bottom, width, height))
        if lbound < x2:
            left = lbound * xscalar
            width = (x2 + 0.5) * xscalar - left
            boxes.append((left, bottom, width, height))
    return boxes


def fa_annotations(
    result_dict, axis_type=FreqAxisType.DC_LEFT, axis_format=FreqAxisFormat.FREQ
):
    if not isinstance(result_dict, dict):
        raise TypeError("Expected dict, got {}".format(type(result_dict).__name__))
    if _AnalysisType.FOURIER != result_dict["analysistype"]:
        raise ValueError("Expected Fourier analysis results")

    if 1.0 == result_dict["signaltype"]:  # complex
        if FreqAxisType.REAL == axis_type:
            axis_type = FreqAxisType.DC_LEFT
    else:
        axis_type = FreqAxisType.REAL

    datasize = result_dict["datasize"]
    fbin = result_dict["fbin"]
    if FreqAxisFormat.BINS == axis_format:
        xscalar = 1 / fbin
    elif FreqAxisFormat.NORM == axis_format:
        xscalar = 1 / result_dict["fdata"]
    else:
        xscalar = 1.0
    tone_keys = []
    for k in result_dict:
        if k.endswith(":ffinal"):
            tk = k.split(":")[0]
            tone_keys.append(tk)
    #
    # Labels = (x, y, str)
    #
    label_dict = dict()
    for tk in tone_keys:
        x = result_dict[tk + ":ffinal"] * xscalar
        y = result_dict[tk + ":mag_dbfs"]
        if x in label_dict:
            if label_dict[x][0] < y:
                label_dict[x][0] = y
            label_dict[x][1] += "\n" + tk
        else:
            label_dict[x] = [y, tk]
    labels = []
    for x in label_dict:
        labels.append((x, label_dict[x][0], label_dict[x][1]))
    #
    # Lines = (x1, y1, x2, y2)
    #
    lines = []
    if "abn" in result_dict:
        abn = result_dict["abn"]
        x = result_dict["fdata"] * xscalar
        lines.append((-x, abn, x, abn))
    #
    # Analysis Band Boxes = (xleft, ybottom, width, height)
    #
    ab_boxes = []
    if result_dict["ab_nbins"] < datasize:
        bottom = -300
        height = 600
        x1 = result_dict["ab_i2"] + 1  # "invert" the analysis band
        x2 = result_dict["ab_i1"] - 1  # to draw *excluded* spectrum
        ab_boxes += _get_annot_boxes(
            axis_type, datasize, bottom, height, x1, x2, fbin * xscalar
        )
    #
    # Tone Boxes = (xleft, ybottom, width, height)
    #
    tone_boxes = []
    for tk in tone_keys:
        bottom = -300
        height = result_dict[tk + ":mag_dbfs"] - bottom
        x1 = result_dict[tk + ":i1"]
        x2 = result_dict[tk + ":i2"]
        tone_boxes += _get_annot_boxes(
            axis_type, datasize, bottom, height, x1, x2, fbin * xscalar
        )

    annots = {
        "labels": labels,
        "lines": lines,
        "ab_boxes": ab_boxes,
        "tone_boxes": tone_boxes,
    }
    return annots


def fa_result_string(result_dict, result_key):
    ckeys, cvalues = _get_key_value_arrays(result_dict)
    result_key = bytes(result_key, "utf-8")
    size = _c_size_t(0)
    result = _lib.gn_fa_result_string_size(
        _ctypes.byref(size), ckeys, len(ckeys), cvalues, len(cvalues), result_key
    )
    _raise_exception_on_failure(result)
    size = size.value
    buf = _ctypes.create_string_buffer(size)
    result = _lib.gn_fa_result_string(
        buf, size, ckeys, len(ckeys), cvalues, len(cvalues), result_key
    )
    _raise_exception_on_failure(result)
    return buf.value.decode("utf-8")


"""
Fourier Transforms
"""

_lib.gn_fft.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _c_size_t,
    _c_size_t,
    _c_int,
]
_lib.gn_fft16.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _c_int,
    _c_size_t,
    _c_size_t,
    _c_int,
    _c_int,
]
_lib.gn_fft32.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _c_int,
    _c_size_t,
    _c_size_t,
    _c_int,
    _c_int,
]
_lib.gn_fft64.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _c_int,
    _c_size_t,
    _c_size_t,
    _c_int,
    _c_int,
]
_lib.gn_fft_size.argtypes = [_c_size_t_p, _c_size_t, _c_size_t, _c_size_t, _c_size_t]
_lib.gn_rfft.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _c_size_t,
    _c_size_t,
    _c_int,
    _c_int,
]
_lib.gn_rfft16.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _c_int,
    _c_size_t,
    _c_size_t,
    _c_int,
    _c_int,
    _c_int,
]
_lib.gn_rfft32.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _c_int,
    _c_size_t,
    _c_size_t,
    _c_int,
    _c_int,
    _c_int,
]
_lib.gn_rfft64.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _c_int,
    _c_size_t,
    _c_size_t,
    _c_int,
    _c_int,
    _c_int,
]
_lib.gn_rfft_size.argtypes = [_c_size_t_p, _c_size_t, _c_size_t, _c_size_t]


def fft(a, *args):
    """
    Compute FFT

    Args:
        ``a`` (``ndarray``) : Input array of type ``complex128``, ``float64``, ``int16``, ``int32``, or ``int64``

        ``args`` (``list``) : Additional arguments
            1. If ``a`` is of type ``complex128`` or ``float64``, then compute the FFT of interleaved normalized samples with the following interpretation.

                ``navg`` (``int``) : FFT averaging number

                ``nfft`` (``int``) : FFT size 

                ``window`` (``Window``): Window

                In this case, if ``a`` is not complex, then a is interpreted to contain interleaved I/Q samples with the following interpretation.

            2. If ``a`` is of type ``float64``, then compute the FFT of split normalized samples.

                ``q`` (``float64``) : Quadrature component 

                ``navg`` (``int``) : FFT averaging number

                ``nfft`` (``int``) : FFT size 

                ``window`` (``Window``): Window

                In this case, ``a`` is interpreted to be the In-phase component.

            3. If ``a`` is of type ``int16``, ``int32``, or ``int64``, then compute the FFT of interleaved quantized samples with the following interpretation.

                ``n`` (``int``) : Resolution (Bitwidth of a)

                ``navg`` (``int``) : FFT averaging number

                ``nfft`` (``int``) : FFT size 

                ``window`` (``Window``): Window

                ``fmt`` (``CodeFormat``): Code format

                In this case, ``a`` is interpreted to contain interleaved quantized samples.

            4. If ``a`` is of type ``int16``, ``int32``, or ``int64``, then compute the FFT of split quantized samples with the following interpretation.

                ``q`` (``int16``, ``int32``, or ``int64``) : Quadrature component 

                ``n`` (``int``) : Resolution (Bitwidth of ``a``)

                ``navg`` (``int``) : FFT averaging number

                ``nfft`` (``int``) : FFT size 

                ``window`` (``Window``): Window

                ``fmt`` (``CodeFormat``): Code format

                In this case, ``a`` is interpreted to to be the In-phase component.

    Returns:
        ``out`` (``ndarray``) : FFT result of type ``float64`` with interleaved Re/Im components

    """
    dtype = _check_ndarray(a, ["complex128", "float64", "int16", "int32", "int64"])
    nargs = len(args)
    q_data = _np.empty(0, dtype=dtype)
    q_size = 0
    base_index = 0
    if dtype in ["complex128", "float64"]:  # normalized samples
        if "complex128" == dtype:
            i_data = a.view("float64")
            q_data.dtype = "float64"
        else:
            i_data = a
            if 0 < nargs and isinstance(args[0], _np.ndarray):  # arg[0] is Q data
                _check_ndarray(args[0], dtype)
                q_data = args[0]
                q_size = q_data.size
                base_index = 1
        i_size = i_data.size
        navg = 1 if nargs <= base_index else args[base_index]
        nfft = 0 if nargs <= base_index + 1 else args[base_index + 1]
        window = Window.NO_WINDOW if nargs <= base_index + 2 else args[base_index + 2]
        n = None
        fmt = None
    else:  # quantized samples
        i_data = a
        i_size = i_data.size
        if 0 < nargs and isinstance(args[0], _np.ndarray):  # arg[0] is Q data
            _check_ndarray(args[0], dtype)
            q_data = args[0]
            q_size = q_data.size
            base_index = 1
        if nargs <= base_index:
            raise Exception("Missing required parameter, n, code width")
        n = args[base_index]
        navg = 1 if nargs <= base_index + 1 else args[base_index + 1]
        nfft = 0 if nargs <= base_index + 2 else args[base_index + 2]
        window = Window.NO_WINDOW if nargs <= base_index + 3 else args[base_index + 3]
        fmt = (
            CodeFormat.TWOS_COMPLEMENT
            if nargs <= base_index + 4
            else args[base_index + 4]
        )
    out_size = _c_size_t(0)
    navg = max(0, navg)
    nfft = max(0, nfft)
    result = _lib.gn_fft_size(_ctypes.byref(out_size), i_size, q_size, navg, nfft)
    _raise_exception_on_failure(result)
    out = _np.empty(out_size.value // 2, dtype="complex128")
    outf64 = out.view("float64")
    if "int16" == dtype:
        result = _lib.gn_fft16(
            outf64,
            outf64.size,
            i_data,
            i_size,
            q_data,
            q_size,
            n,
            navg,
            nfft,
            window,
            fmt,
        )
    elif "int32" == dtype:
        result = _lib.gn_fft32(
            outf64,
            outf64.size,
            i_data,
            i_size,
            q_data,
            q_size,
            n,
            navg,
            nfft,
            window,
            fmt,
        )
    elif "int64" == dtype:
        result = _lib.gn_fft64(
            outf64,
            outf64.size,
            i_data,
            i_size,
            q_data,
            q_size,
            n,
            navg,
            nfft,
            window,
            fmt,
        )
    else:
        result = _lib.gn_fft(
            outf64, outf64.size, i_data, i_size, q_data, q_size, navg, nfft, window
        )
    _raise_exception_on_failure(result)
    return out


def rfft(a, *args):
    """
    Compute Real-FFT

    Args:
        ``a`` (``ndarray``) : Input array of type ``float64``, ``int16``, ``int32``, or ``int64``

        ``args`` (``list``) : Additional arguments
            1. If ``a`` is of type ``float64``, then compute the real-FFT of normalized samples with the following interpretation.

                ``navg`` (``int``) : FFT averaging number

                ``nfft`` (``int``) : FFT size 

                ``window`` (``Window``): Window

                ``scale`` (``RfftScale``): Scaling mode

            2. If ``a`` is of type ``int16``, ``int32``, or ``int64``, then compute the FFT of interleaved quantized samples with the following interpretation.

                ``n`` (``int``) : Resolution (Bitwidth of a)

                ``navg`` (``int``) : FFT averaging number

                ``nfft`` (``int``) : FFT size 

                ``window`` (``Window``): Window

                ``fmt`` (``CodeFormat``): Code format

                ``scale`` (``RfftScale``): Scaling mode
        
    Returns:
        ``out`` (``ndarray``) : FFT result of type ``float64`` with interleaved Re/Im components
    """
    dtype = _check_ndarray(a, ["float64", "int16", "int32", "int64"])
    nargs = len(args)
    if "float64" == dtype:
        # normalized samples
        navg = 1 if nargs == 0 else args[0]
        nfft = 0 if nargs <= 1 else args[1]
        window = Window.NO_WINDOW if nargs <= 2 else args[2]
        scale = RfftScale.DBFS_SIN if nargs <= 3 else args[3]
        n = None
        fmt = None
    else:
        # quantized samples
        if 0 == len(args):
            raise Exception("Missing required parameter, n, code width")
        n = args[0]
        navg = 1 if nargs <= 1 else args[1]
        nfft = 0 if nargs <= 2 else args[2]
        window = Window.NO_WINDOW if nargs <= 3 else args[3]
        fmt = CodeFormat.TWOS_COMPLEMENT if nargs <= 4 else args[4]
        scale = RfftScale.DBFS_SIN if nargs <= 5 else args[5]
    out_size = _c_size_t(0)
    navg = max(0, navg)
    nfft = max(0, nfft)
    result = _lib.gn_rfft_size(_ctypes.byref(out_size), a.size, navg, nfft)
    _raise_exception_on_failure(result)
    out = _np.empty(out_size.value // 2, dtype="complex128")
    outf64 = out.view("float64")
    if "int16" == dtype:
        result = _lib.gn_rfft16(
            outf64, outf64.size, a, a.size, n, navg, nfft, window, fmt, scale
        )
    elif "int32" == dtype:
        result = _lib.gn_rfft32(
            outf64, outf64.size, a, a.size, n, navg, nfft, window, fmt, scale
        )
    elif "int64" == dtype:
        result = _lib.gn_rfft64(
            outf64, outf64.size, a, a.size, n, navg, nfft, window, fmt, scale
        )
    else:
        result = _lib.gn_rfft(outf64, outf64.size, a, a.size, navg, nfft, window, scale)
    _raise_exception_on_failure(result)
    return out


"""
Fourier Utilities
"""

_lib.gn_alias.argtypes = [_c_double_p, _c_double, _c_double, _c_int]
_lib.gn_coherent.argtypes = [_c_double_p, _c_size_t, _c_double, _c_double]
_lib.gn_freq_axis.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _c_size_t,
    _c_int,
    _c_double,
    _c_int,
]
_lib.gn_freq_axis_size.argtypes = [_c_size_t_p, _c_size_t, _c_int]
_lib.gn_fftshift.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t]
_lib.gn_ifftshift.argtypes = [_ndptr_f64_1d, _c_size_t, _ndptr_f64_1d, _c_size_t]


def alias(fs, freq, axis_type):
    """
    alias

    Parameters
    ----------
    fs :
    freq :
    axis_type :

    Returns
    -------
    out :

    """
    out = _c_double(0.0)
    result = _lib.gn_alias(_ctypes.byref(out), fs, freq, axis_type)
    _raise_exception_on_failure(result)
    return out.value


def coherent(nfft, fs, freq):
    """
    coherent

    Parameters
    ----------
    nfft :
    fs :
    freq :

    Returns
    -------
    out :

    """
    out = _c_double(0.0)
    result = _lib.gn_coherent(_ctypes.byref(out), nfft, fs, freq)
    _raise_exception_on_failure(result)
    return out.value


def fftshift(a):
    """
    fftshift

    Parameters
    ----------
    a :

    Returns
    -------
    out :

    """
    _check_ndarray(a, "float64")
    out = _np.empty(a.size, dtype="float64")
    result = _lib.gn_fftshift(out, out.size, a, a.size)
    _raise_exception_on_failure(result)
    return out


def freq_axis(nfft, axis_type, fs=1.0, axis_format=FreqAxisFormat.FREQ):
    """
    freq_axis

    Parameters
    ----------
    nfft :
    axis_type :
    fs :
    axis_format :

    Returns
    -------
    out :

    """
    out_size = _c_size_t()
    result = _lib.gn_freq_axis_size(_ctypes.byref(out_size), nfft, axis_type)
    _raise_exception_on_failure(result)
    out = _np.empty(out_size.value, dtype="float64")
    result = _lib.gn_freq_axis(out, out.size, nfft, axis_type, fs, axis_format)
    _raise_exception_on_failure(result)
    return out


def ifftshift(a):
    """
    ifftshift

    Parameters
    ----------
    a :

    Returns
    -------
    out :

    """
    _check_ndarray(a, "float64")
    out = _np.empty(a.size, dtype="float64")
    result = _lib.gn_ifftshift(out, out.size, a, a.size)
    _raise_exception_on_failure(result)
    return out


"""
Manager
"""

_lib.gn_mgr_compare.argtypes = [_c_bool_p, _c_char_p, _c_char_p]
_lib.gn_mgr_contains.argtypes = [_c_bool_p, _c_char_p]
_lib.gn_mgr_remove.argtypes = [_c_char_p]
_lib.gn_mgr_save.argtypes = [_c_char_p, _c_size_t, _c_char_p, _c_char_p]
_lib.gn_mgr_size.argtypes = [_c_size_t_p]
_lib.gn_mgr_to_string.argtypes = [_c_char_p, _c_size_t, _c_char_p]
_lib.gn_mgr_type.argtypes = [_c_char_p, _c_size_t, _c_char_p]


def mgr_clear():
    _lib.gn_mgr_clear()


def mgr_compare(key1, key2):
    equal = _c_bool(False)
    key1 = bytes(key1, "utf-8")
    key2 = bytes(key2, "utf-8")
    result = _lib.gn_mgr_compare(_ctypes.byref(equal), key1, key2)
    _raise_exception_on_failure(result)
    return equal.value


def mgr_contains(key):
    found = _c_bool(False)
    key = bytes(key, "utf-8")
    result = _lib.gn_mgr_contains(_ctypes.byref(found), key)
    _raise_exception_on_failure(result)
    return found.value


def mgr_remove(key):
    key = bytes(key, "utf-8")
    _lib.gn_mgr_remove(key)


def mgr_save(key, filename=""):
    size = _c_size_t(0)
    key = bytes(key, "utf-8")
    filename = bytes(filename, "utf-8")
    result = _lib.gn_mgr_save_filename_size(_ctypes.byref(size), key, filename)
    _raise_exception_on_failure(result)
    buf = _ctypes.create_string_buffer(size.value)
    result = _lib.gn_mgr_save(buf, len(buf), key, filename)
    _raise_exception_on_failure(result)
    return buf.value.decode("utf-8")


def mgr_size():
    size = _c_size_t(0)
    _lib.gn_mgr_size(_ctypes.byref(size))
    return size.value


def mgr_to_string(key=""):
    size = _c_size_t(0)
    key = bytes(key, "utf-8")
    _lib.gn_mgr_to_string_size(_ctypes.byref(size), key)
    buf = _ctypes.create_string_buffer(size.value)
    result = _lib.gn_mgr_to_string(buf, len(buf), key)
    _raise_exception_on_failure(result)
    return buf.value.decode("utf-8")


def mgr_type(key):
    size = _c_size_t(0)
    key = bytes(key, "utf-8")
    result = _lib.gn_mgr_type_size(_ctypes.byref(size), key)
    _raise_exception_on_failure(result)
    buf = _ctypes.create_string_buffer(size.value)
    result = _lib.gn_mgr_type(buf, len(buf), key)
    _raise_exception_on_failure(result)
    return buf.value.decode("utf-8")


"""
Signal Processing
"""

_lib.gn_downsample.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _c_int,
    _c_bool,
]
_lib.gn_downsample16.argtypes = [
    _ndptr_i16_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _c_int,
    _c_bool,
]
_lib.gn_downsample32.argtypes = [
    _ndptr_i32_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _c_int,
    _c_bool,
]
_lib.gn_downsample64.argtypes = [
    _ndptr_i64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _c_int,
    _c_bool,
]
_lib.gn_fshift.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _c_double,
    _c_double,
]
_lib.gn_fshift16.argtypes = [
    _ndptr_i16_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _c_int,
    _c_double,
    _c_double,
    _c_int,
]
_lib.gn_fshift32.argtypes = [
    _ndptr_i32_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _c_int,
    _c_double,
    _c_double,
    _c_int,
]
_lib.gn_fshift64.argtypes = [
    _ndptr_i64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _c_int,
    _c_double,
    _c_double,
    _c_int,
]
_lib.gn_normalize16.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
    _c_int,
    _c_int,
]
_lib.gn_normalize32.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
    _c_int,
    _c_int,
]
_lib.gn_normalize64.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
    _c_int,
    _c_int,
]
_lib.gn_polyval.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
]
_lib.gn_quantize16.argtypes = [
    _ndptr_i16_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _c_double,
    _c_int,
    _c_double,
    _c_int,
]
_lib.gn_quantize32.argtypes = [
    _ndptr_i32_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _c_double,
    _c_int,
    _c_double,
    _c_int,
]
_lib.gn_quantize64.argtypes = [
    _ndptr_i64_1d,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
    _c_double,
    _c_int,
    _c_double,
    _c_int,
]


def downsample(a, ratio, interleaved=False):    
    """
    Downsample a waveform

    Args:
        ``a`` (``ndarray``) : Input array of type ``complex128``, ``int16``, ``int32``, or ``int64``
        
        ``ratio`` (``int``) : Downsample ratio

        ``interleaved`` (``double``) : If true, ``a`` is interleaved I/Q data

    Returns:
        ``out`` (``ndarray``) : ``float64``, ``int16``, ``int32``, or ``int64`` ``numpy`` array consisting of downsampled waveform
    """
    dtype = _check_ndarray(a, ["complex128", "float64", "int16", "int32", "int64"])
    ratio = int(ratio)
    if (
        "complex128" == dtype
    ):  # parameter 'interleaved' is ignored because 'complex128' is
        out_size = _c_size_t(0)
        af64 = a.view("float64")
        result = _lib.gn_downsample_size(
            _ctypes.byref(out_size), af64.size, ratio, True
        )
        _raise_exception_on_failure(result)
        out = _np.empty(out_size.value // 2, dtype="complex128")
        outf64 = out.view("float64")
        result = _lib.gn_downsample(
            outf64, outf64.size, af64, af64.size, ratio, interleaved
        )
    else:
        out_size = _c_size_t(0)
        result = _lib.gn_downsample_size(
            _ctypes.byref(out_size), a.size, ratio, interleaved
        )
        _raise_exception_on_failure(result)
        out = _np.empty(out_size.value, dtype=dtype)
        if "int16" == dtype:
            result = _lib.gn_downsample16(out, out.size, a, a.size, ratio, interleaved)
        elif "int32" == dtype:
            result = _lib.gn_downsample32(out, out.size, a, a.size, ratio, interleaved)
        elif "int64" == dtype:
            result = _lib.gn_downsample64(out, out.size, a, a.size, ratio, interleaved)
        else:
            result = _lib.gn_downsample(out, out.size, a, a.size, ratio, interleaved)
    _raise_exception_on_failure(result)
    return out


def fshift(a, *args):
    """
    Perform frequency shift

    Args:
        ``a`` (``ndarray``) : Input array of type ``complex128``, ``float64``, ``int16``, ``int32``, or ``int64``

        ``args`` (``list``) : Additional arguments
            1. If ``a`` is of type ``complex128`` or ``float64``, then perform frequency shift of interleaved normalized samples with the following interpretation.

                ``fs`` (``double``) : Sample rate

                ``fshift_`` (``double``) : Shift frequency

                In this case, if ``a`` is not complex, then a is interpreted to contain interleaved I/Q samples.

            2. If ``a`` is of type ``float64``, then perform frequency shift of split normalized samples.

                ``q`` (``float64``) : Quadrature component 

                ``fs`` (``double``) : Sample rate

                ``fshift_`` (``double``) : Shift frequency

                In this case, ``a`` is interpreted to be the In-phase component.

            3. If ``a`` is of type ``int16``, ``int32``, or ``int64``, then perform frequency shift of interleaved quantized samples with the following interpretation.

                ``n`` (``int``) : Resolution (Bitwidth of a)

                ``fs`` (``double``) : Sample rate

                ``fshift_`` (``double``) : Shift frequency

                ``fmt`` (``CodeFormat``): Code format

                In this case, ``a`` is interpreted to contain interleaved quantized samples.

            4. If ``a`` is of type ``int16``, ``int32``, or ``int64``, then perform frequency shift of split quantized samples with the following interpretation.

                ``q`` (``int16``, ``int32``, or ``int64``) : Quadrature component 

                ``n`` (``int``) : Resolution (Bitwidth of ``a``)

                ``fs`` (``double``) : Sample rate

                ``fshift_`` (``double``) : Shift frequency

                ``fmt`` (``CodeFormat``): Code format

                In this case, ``a`` is interpreted to to be the In-phase component.

    Returns:
        ``out`` (``ndarray``) : Frequency-shifted input waveform. The output datatype is the same as the input datatype.

    """
    dtype = _check_ndarray(a, ["complex128", "float64", "int16", "int32", "int64"])
    nargs = len(args)
    q_data = _np.empty(0, dtype=dtype)
    q_size = 0
    base_index = 0
    if dtype in ["complex128", "float64"]:  # normalized samples
        if "complex128" == dtype:
            i_data = a.view("float64")
            q_data.dtype = "float64"
        else:
            i_data = a
            if 0 < nargs and isinstance(args[0], _np.ndarray):  # arg[0] is Q data
                _check_ndarray(args[0], dtype)
                q_data = args[0]
                q_size = q_data.size
                base_index = 1
        i_size = i_data.size
        if nargs <= base_index + 1:
            raise Exception("Missing required parameters")
        fs = args[base_index]
        fshift_ = args[base_index + 1]
        out_size = _c_size_t(0)
        result = _lib.gn_fshift_size(_ctypes.byref(out_size), i_size, q_size)
        _raise_exception_on_failure(result)
        if "complex128" == dtype:
            out = _np.empty(out_size.value // 2, dtype=dtype)
            outf64 = out.view("float64")
            result = _lib.gn_fshift(
                outf64, outf64.size, i_data, i_size, q_data, q_size, fs, fshift_
            )
        else:
            out = _np.empty(out_size.value, dtype=dtype)
            result = _lib.gn_fshift(
                out, out.size, i_data, i_size, q_data, q_size, fs, fshift_
            )
    else:  # quantized samples
        i_data = a
        i_size = i_data.size
        if 0 < nargs and isinstance(args[0], _np.ndarray):  # arg[0] is Q data
            _check_ndarray(args[0], dtype)
            q_data = args[0]
            q_size = q_data.size
            base_index = 1
        if nargs <= base_index + 2:
            raise Exception("Missing required parameters")
        n = args[base_index]
        fs = args[base_index + 1]
        fshift_ = args[base_index + 2]
        fmt = (
            CodeFormat.TWOS_COMPLEMENT
            if nargs <= base_index + 3
            else args[base_index + 3]
        )
        out_size = _c_size_t(0)
        result = _lib.gn_fshift_size(_ctypes.byref(out_size), i_size, q_size)
        _raise_exception_on_failure(result)
        out = _np.empty(out_size.value, dtype=dtype)
        if "int16" == dtype:
            result = _lib.gn_fshift16(
                out, out.size, i_data, i_size, q_data, q_size, n, fs, fshift_, fmt
            )
        elif "int32" == dtype:
            result = _lib.gn_fshift32(
                out, out.size, i_data, i_size, q_data, q_size, n, fs, fshift_, fmt
            )
        else:  # 'int64'
            result = _lib.gn_fshift64(
                out, out.size, i_data, i_size, q_data, q_size, n, fs, fshift_, fmt
            )
    _raise_exception_on_failure(result)
    return out


def normalize(a, n, fmt=CodeFormat.TWOS_COMPLEMENT):
    """
    Normalize a waveform

    Args:
        ``a`` (``ndarray``) : Input array of type ``int16``, ``int32``, or ``int64``
        
        ``n`` (``int``) : Resolution (Bitwidth of ``a``)

        ``fmt`` (``CodeFormat``): Code format

    Returns:
        ``out`` (``ndarray``) : ``float64`` ``numpy`` array consisting of normalized input waveform
    """
    dtype = _check_ndarray(a, ["int16", "int32", "int64"])
    out = _np.empty(a.size, dtype="float64")
    if "int16" == dtype:
        result = _lib.gn_normalize16(out, out.size, a, a.size, n, fmt)
    elif "int32" == dtype:
        result = _lib.gn_normalize32(out, out.size, a, a.size, n, fmt)
    else:
        result = _lib.gn_normalize64(out, out.size, a, a.size, n, fmt)
    _raise_exception_on_failure(result)
    return out


def polyval(a, c):
    """
    Apply distortion as a polynomial function

    Args:
        ``a`` (``ndarray``) : Input array of type ``float64``
        
        ``c`` (``ndarray``) : Polynomial coefficient array of type ``float64``

    Returns:
        ``out`` (``ndarray``) : ``float64`` ``numpy`` array consisting of distorted input waveform
    """
    _check_ndarray(a, "float64")
    c = _np.array(c, dtype="float64")
    out = _np.empty(a.size, dtype="float64")
    result = _lib.gn_polyval(out, out.size, a, a.size, c, c.size)
    _raise_exception_on_failure(result)
    return out


def quantize16(a, fsr, n, noise=0.0, fmt=CodeFormat.TWOS_COMPLEMENT):
    """
    Quantize a floating-point waveform

    Args:
        ``a`` (``ndarray``) : Input array of type ``float64``

        ``fsr`` (``double``) : Full-scale range of the waveform
        
        ``n`` (``int``) : Resolution (Bitwidth of ``a``)

        ``noise`` (``double``) : Quantization Noise RMS level

        ``fmt`` (``CodeFormat``): Code format

    Returns:
        ``out`` (``ndarray``) : ``int16`` ``numpy`` array consisting of quantized input waveform
    """
    _check_ndarray(a, "float64")
    out = _np.empty(a.size, dtype="int16")
    result = _lib.gn_quantize16(out, out.size, a, a.size, fsr, n, noise, fmt)
    _raise_exception_on_failure(result)
    return out


def quantize32(a, fsr, n, noise=0.0, fmt=CodeFormat.TWOS_COMPLEMENT):
    """
    Quantize a floating-point waveform

    Args:
        ``a`` (``ndarray``) : Input array of type ``float64``

        ``fsr`` (``double``) : Full-scale range of the waveform
        
        ``n`` (``int``) : Resolution (Bitwidth of ``a``)

        ``noise`` (``double``) : Quantization Noise RMS level

        ``fmt`` (``CodeFormat``): Code format

    Returns:
        ``out`` (``ndarray``) : ``int32`` ``numpy`` array consisting of quantized input waveform
    """
    _check_ndarray(a, "float64")
    out = _np.empty(a.size, dtype="int32")
    result = _lib.gn_quantize32(out, out.size, a, a.size, fsr, n, noise, fmt)
    _raise_exception_on_failure(result)
    return out


def quantize64(a, fsr, n, noise=0.0, fmt=CodeFormat.TWOS_COMPLEMENT):
    """
    Quantize a floating-point waveform

    Args:
        ``a`` (``ndarray``) : Input array of type ``float64``

        ``fsr`` (``double``) : Full-scale range of the waveform
        
        ``n`` (``int``) : Resolution (Bitwidth of ``a``)

        ``noise`` (``double``) : Quantization Noise RMS level

        ``fmt`` (``CodeFormat``): Code format

    Returns:
        ``out`` (``ndarray``) : ``int64`` ``numpy`` array consisting of quantized input waveform
    """
    _check_ndarray(a, "float64")
    out = _np.empty(a.size, dtype="int64")
    result = _lib.gn_quantize64(out, out.size, a, a.size, fsr, n, noise, fmt)
    _raise_exception_on_failure(result)
    return out


def quantize(a, fsr, n, noise=0.0, fmt=CodeFormat.TWOS_COMPLEMENT):
    """
    Quantize a floating-point waveform

    Args:
        ``a`` (``ndarray``) : Input array of type ``float64``

        ``fsr`` (``double``) : Full-scale range of the waveform
        
        ``n`` (``int``) : Resolution (Bitwidth of ``a``)

        ``noise`` (``double``) : Quantization Noise RMS level

        ``fmt`` (``CodeFormat``): Code format

    Returns:
        ``out`` (``ndarray``) : ``numpy`` array consisting of quantized input waveform of datatype ``int16`` if ``n <= 16``, ``int32`` otherwise
    """
    if n < 16 or 16 == n and CodeFormat.TWOS_COMPLEMENT == fmt:
        return quantize16(a, fsr, n, noise, fmt)
    else:
        return quantize32(a, fsr, n, noise, fmt)


"""
Waveforms
"""

_lib.gn_cos.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _c_double,
    _c_double,
    _c_double,
    _c_double,
    _c_double,
    _c_double,
]
_lib.gn_gaussian.argtypes = [_ndptr_f64_1d, _c_size_t, _c_double, _c_double]
_lib.gn_ramp.argtypes = [_ndptr_f64_1d, _c_size_t, _c_double, _c_double, _c_double]
_lib.gn_sin.argtypes = [
    _ndptr_f64_1d,
    _c_size_t,
    _c_double,
    _c_double,
    _c_double,
    _c_double,
    _c_double,
    _c_double,
]
_lib.gn_wf_analysis.argtypes = [
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _ndptr_f64_1d,
    _c_size_t,
]
_lib.gn_wf_analysis16.argtypes = [
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _ndptr_i16_1d,
    _c_size_t,
]
_lib.gn_wf_analysis32.argtypes = [
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _ndptr_i32_1d,
    _c_size_t,
]
_lib.gn_wf_analysis64.argtypes = [
    _c_char_p_p,
    _c_size_t,
    _c_double_p,
    _c_size_t,
    _ndptr_i64_1d,
    _c_size_t,
]


def cos(nsamples, fs, ampl, freq, phase=0.0, td=0.0, tj=0.0):
    """
    Generate cosine waveform

    Args:
        ``nsamples`` (``int``) : Number of samples

        ``fs`` (``double``) : Sample rate (S/s)

        ``ampl`` (``double``) : Amplitude

        ``freq`` (``double``) : Frequency (Hz)

        ``phase`` (``double``) : Phase (rad)

        ``td`` (``double``) : Time delay (s)

        ``tj`` (``double``) : RMS Aperture jitter (s)

    Returns:
        ``out`` (``ndarray``) : ``float64`` ``numpy`` array consisting of Cosine waveform
    """
    out = _np.empty(nsamples, "float64")
    result = _lib.gn_cos(out, out.size, fs, ampl, freq, phase, td, tj)
    _raise_exception_on_failure(result)
    return out


def gaussian(nsamples, mean, sd):
    """
    Generate Gaussian random samples

    Args:
        ``nsamples`` (``int``) : Number of samples

        ``mean`` (``double``) : Mean

        ``sd`` (``double``) : Standard deviation

    Returns:
        ``out`` (``ndarray``) : ``float64`` ``numpy`` array consisting of Gaussian random samples
    """
    out = _np.empty(nsamples, "float64")
    result = _lib.gn_gaussian(out, out.size, mean, sd)
    _raise_exception_on_failure(result)
    return out


def ramp(nsamples, start, stop, noise):
    """
    Generate ramp waveform

    Args:
        ``nsamples`` (``int``) : Number of samples

        ``start`` (``double``) : Start value

        ``stop`` (``double``) : Stop value

        ``noise`` (``double``) : RMS noise

    Returns:
        ``out`` (``ndarray``) : ``float64`` ``numpy`` array consisting of ramp waveform
    """
    out = _np.empty(nsamples, "float64")
    result = _lib.gn_ramp(out, out.size, start, stop, noise)
    _raise_exception_on_failure(result)
    return out


def sin(nsamples, fs, ampl, freq, phase=0.0, td=0.0, tj=0.0):
    """
    Generate sine waveform

    Args:
        ``nsamples`` (``int``) : Number of samples

        ``fs`` (``double``) : Sample rate (S/s)

        ``ampl`` (``double``) : Amplitude

        ``freq`` (``double``) : Frequency (Hz)

        ``phase`` (``double``) : Phase (rad)

        ``td`` (``double``) : Time delay (s)

        ``tj`` (``double``) : RMS Aperture jitter (s)

    Returns:
        ``out`` (``ndarray``) : ``float64`` ``numpy`` array consisting of Sine waveform
    """
    out = _np.empty(nsamples, "float64")
    result = _lib.gn_sin(out, out.size, fs, ampl, freq, phase, td, tj)
    _raise_exception_on_failure(result)
    return out


def wf_analysis(a):    
    """
    Run waveform analysis

    Args:
        ``a`` (``ndarray``) : Input array of type ``int16``, ``int32``, or ``int64``
        
    Returns:
        Returns:
        ``results`` (``dict``) : Dictionary containing all waveform analysis results

    Notes:
        Every Key:Value pair in the dictionary is ``str``:``float``.

        The dictionary contains the following keys:
            ``signaltype`` : Signal type: 0=Real, 1=Complex

            ``min`` : Minumum value

            ``max`` : Maximum value

            ``mid`` : Middle value ((max + min) / 2)

            ``range`` : Range (max - min)

            ``avg`` : Average value

            ``rms`` : RMS value

            ``rmsac`` : RMS value with DC removed

            ``min_index`` : Index of first occurence of minimum value

            ``max_index`` : Index of first occurence of maximum value
    """
    dtype = _check_ndarray(a, ["float", "int16", "int32", "int64"])
    keys, values = _get_analysis_containers(_AnalysisType.WAVEFORM)
    if "int16" == dtype:
        result = _lib.gn_wf_analysis16(keys, len(keys), values, len(values), a, a.size)
    elif "int32" == dtype:
        result = _lib.gn_wf_analysis32(keys, len(keys), values, len(values), a, a.size)
    elif "int64" == dtype:
        result = _lib.gn_wf_analysis64(keys, len(keys), values, len(values), a, a.size)
    else:
        result = _lib.gn_wf_analysis(keys, len(keys), values, len(values), a, a.size)
    _raise_exception_on_failure(result)
    results = _make_results_dict(keys, values)
    return results
