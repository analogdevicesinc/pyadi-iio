from test.rf.spec import *

import numpy as np
import pytest


def test_spec_est_t1():
    fs = 64
    length = 600  # seconds
    N = fs * length
    t = linspace(0, length, num=N, endpoint=False)

    # Generate a sinusoid at frequency f
    f = 10  # Hz
    a = cos(2 * pi * f * t) * 2 ** 15

    amp, freqs = spec_est(a, fs, ref=2 ** 15, plot=False)

    assert np.abs(max(amp) + 6) < 0.03


def test_spec_est_t2():
    fs = 64
    length = 600  # seconds
    N = fs * length
    t = linspace(0, length, num=N, endpoint=False)

    # Generate a sinusoid at frequency f
    f = 10  # Hz
    a = exp(1j * 2 * pi * f * t) * 2 ** 15

    amp, freqs = spec_est(a, fs, ref=2 ** 15, plot=False)

    assert np.abs(max(amp)) < 0.03


def test_spec_est_t3():
    fs = 64
    length = 600  # seconds
    N = fs * length
    t = linspace(0, length, num=N, endpoint=False)

    # Generate a sinusoid at frequency f
    f = 0  # Hz
    a = cos(2 * pi * f * t) * 2 ** 15
    # a = exp(1j * 2 * pi * f * t) * 2 ** 15

    amp, freqs = spec_est(a, fs, ref=2 ** 15, plot=False)
    print(max(amp))
    assert np.abs(max(amp)) < 0.03


def test_spec_est_t4():
    fs = 64
    length = 600  # seconds
    N = fs * length
    t = linspace(0, length, num=N, endpoint=False)

    # Generate a sinusoid at frequency f
    f = 0  # Hz
    # a = cos(2 * pi * f * t) * 2 ** 15
    a = exp(1j * 2 * pi * f * t) * 2 ** 15

    amp, freqs = spec_est(a, fs, ref=2 ** 15, plot=False)
    print(max(amp))
    assert np.abs(max(amp)) < 0.03
