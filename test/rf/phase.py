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
        Signel complex signal

    Returns
    -------
    (phase, sample_delay) : tuple(float,int)
        phase: phase difference between signals in degrees
        sample_delay: sample offset difference between signals
    """
    cor = np.correlate(chan0, chan1, "full")
    i = np.argmax(cor)
    m = cor[i]
    sample_delay = len(chan0) - i - 1
    return (np.angle(m) * 180 / np.pi, sample_delay)


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
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error
