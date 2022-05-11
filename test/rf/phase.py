import numpy as np


def measure_phase_and_delay(chan0, chan1):
    """
    Measure phase and sample delay between two complex signals.
    Signals are assumed to have a single cross-correlation
    peak. Using noise sources are generally useful for this
    measurement and not sinusoids

    Parameters
    ----------
    chan0 : np.array complex
        Single complex signal
    chan1 : np.array complex
        Single complex signal

    Returns
    -------
    (phase, sample_delay) : tuple(float,int)
        phase: phase difference between signals in degrees
        sample_delay: sample offset difference between signals
    """
    cor = np.correlate(chan0, chan1, "full")

    i = np.argmax(np.abs(cor))
    m = cor[i]
    angle = np.angle(m, deg=True)
    if angle < 0:
        angle = angle + 360
    sample_delay = len(chan0) - i - 1
    return (angle, sample_delay)


def measure_phase(chan0, chan1):
    """
    Measure phase between two complex signals.
    Instanteous phase at each point between signals
    is measured then averaged. This measurement assumes
    no sample offset between signals

    Parameters
    ----------
    chan0 : np.array complex
        Single complex signal
    chan1 : np.array complex
        Signel complex signal

    Returns
    -------
    phase : float
        Phase difference between signals in degrees
    """
    errorV = np.unwrap(np.angle(chan0 * np.conj(chan1))) * 180 / np.pi
    for i in range(len(errorV)):
        if errorV[i] < 0:
            errorV[i] = errorV[i] + 360
    error = np.mean(errorV)
    return error
