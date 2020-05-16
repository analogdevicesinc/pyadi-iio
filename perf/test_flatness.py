import numpy as np
from test.rf import spec

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def eval_flatness(tx, rx, test_spec):

    # Generate noise

    # Wait for settling

    # Pull data from device
    data = rx.rx()

    ### Calculate flatness
    # Get spectrum
    (amp, freqs) = spec.spec_est(data, test_spec.rx_fs, test_spec.adc_max_val)

    # Get band of interest
    left_start = find_nearest(freqs, -test_spec.bandwidth/2)
    right_end = find_nearest(freqs, test_spec.bandwidth/2)
    band = amp[left_start:right_end]
    flatness_dB = np.max(band) - np.min(band)

    return flatness_dB
