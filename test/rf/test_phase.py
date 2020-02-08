from test.rf.phase import *

# import matplotlib.pyplot as plt
import pytest
from numpy import abs, exp, linspace, pi, real


def test_measure_phase():
    fs = 64
    length = 600  # seconds
    N = fs * length
    t = linspace(0, length, num=N, endpoint=False)

    # Generate a sinusoid at frequency f
    f = 10  # Hz
    a = exp(1j * 2 * pi * f * t)
    b = exp(1j * (2 * pi * f * t - pi / 4))
    # plt.plot(t, np.real(a))
    # plt.plot(t, np.real(b))
    # plt.show()

    phase = measure_phase(a, b)

    assert abs(phase - 45) < 0.01


def test_measure_phase_and_delay_delay():
    buff_size = 1024
    B = 2 ** 15 * 0.8
    a = np.random.uniform(-B, B, buff_size * 4)
    b = a * exp(1j * (-pi / 4))
    a = a[1:]
    b = b[:-1]
    # plt.plot(t, np.real(a))
    # plt.plot(t, np.real(b))
    # plt.show()
    phase, delay = measure_phase_and_delay(a, b)
    assert delay == 1
    assert abs(phase - 45) < 0.01


def test_measure_phase_and_delay_phase():
    buff_size = 1024
    B = 2 ** 15 * 0.8
    a = np.random.uniform(-B, B, buff_size * 4)
    b = a * exp(1j * (-pi / 4))
    # plt.plot(t, np.real(a))
    # plt.plot(t, np.real(b))
    # plt.show()
    phase, delay = measure_phase_and_delay(a, b)
    assert delay == 0
    assert abs(phase - 45) < 0.01
