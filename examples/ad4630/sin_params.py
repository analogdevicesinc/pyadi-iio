# --------------------LICENSE AGREEMENT----------------------------------------
# Copyright (c) 2020 Analog Devices, Inc.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#   - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#   - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#   - Modified versions of the software must be conspicuously marked as such.
#   - This software is licensed solely and exclusively for use with
#   processors/products manufactured by or for Analog Devices, Inc.
#   - This software may not be combined or merged with other code in any manner
#   that would cause the software to become subject to terms and conditions
#   which differ from those listed here.
#   - Neither the name of Analog Devices, Inc. nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#   - The use of this software may or may not infringe the patent rights of
#   one or more patent holders.  This license does not release you from the
#   requirement that you obtain separate licenses from these patent holders
#   to use this software.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES, INC. AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# NON-INFRINGEMENT, TITLE, MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ANALOG DEVICES, INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, PUNITIVE OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# DAMAGES ARISING OUT OF CLAIMS OF INTELLECTUAL PROPERTY RIGHTS INFRINGEMENT;
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# 2020-02-24-7CBSD SLA
# -----------------------------------------------------------------------------

import math as m

import numpy as np

NONE = 0x00
HAMMING = 0x10
HANN = 0x11
BLACKMAN = 0x20
BLACKMAN_EXACT = 0x21
BLACKMAN_HARRIS_70 = 0x22
FLAT_TOP = 0x23
BLACKMAN_HARRIS_92 = 0x30

DEF_WINDOW_TYPE = BLACKMAN_HARRIS_92

BW = 3


def sin_params(
    data, window_type=DEF_WINDOW_TYPE, mask=None, num_harms=9, spur_in_harms=True
):
    fft_data = windowed_fft_mag(data, window_type)
    harm_bins, harms, harm_bws = find_harmonics(fft_data, num_harms)
    spur, spur_bw = find_spur(
        spur_in_harms, harm_bins[0], harms, harm_bws, fft_data, window_type
    )

    if mask is None:
        mask = calculate_auto_mask(fft_data, harm_bins, window_type)
    noise, noise_bins = masked_sum_of_sq(fft_data, mask)

    average_noise = noise / max(1, noise_bins)
    noise = average_noise * (len(fft_data) - 1)

    # create a dictionary where key is harmonic number and value is tuple of harm and bin
    harmonics = {}
    for i, (h, (b, bw)) in enumerate(zip(harms, zip(harm_bins, harm_bws))):
        h -= average_noise * bw
        if h > 0:
            harmonics[i + 1] = (h, b)
        elif i < 9:
            harmonics[i + 1] = (h, b)

    spur -= average_noise * spur_bw

    signal = harmonics[1][0]
    floor = 10 * m.log10(average_noise / signal)  # dBc
    snr = 10 * m.log10(signal / noise)
    harm_dist = (
        harmonics.get(2, (0, 0))[0]
        + harmonics.get(3, (0, 0))[0]
        + harmonics.get(4, (0, 0))[0]
        + harmonics.get(5, (0, 0))[0]
    )
    thd = 10 * m.log10(harm_dist / signal) if harm_dist > 0 else 0
    sinad = 10 * m.log10(signal / (harm_dist + noise))
    enob = (sinad - 1.76) / 6.02
    sfdr = 10 * m.log10(signal / spur) if spur > 0 else 0

    return (harmonics, snr, thd, sinad, enob, sfdr, floor)


def window(size, window_type=DEF_WINDOW_TYPE):
    if window_type == NONE:
        return None
    if window_type == HAMMING:
        return _one_cos(size, 0.54, 0.46, 1.586303)
    elif window_type == HANN:
        return _one_cos(size, 0.50, 0.50, 1.632993)
    elif window_type == BLACKMAN:
        return _two_cos(size, 0.42, 0.50, 0.08, 1.811903)
    elif window_type == BLACKMAN_EXACT:
        return _two_cos(size, 42659071, 0.49656062, 0.07684867, 1.801235)
    elif window_type == BLACKMAN_HARRIS_70:
        return _two_cos(size, 0.42323, 0.49755, 0.07922, 1.807637)
    elif window_type == FLAT_TOP:
        return _two_cos(size, 0.2810639, 0.5208972, 0.1980399, 2.066037)
    elif window_type == BLACKMAN_HARRIS_92:
        return _three_cos(size, 0.35875, 0.48829, 0.14128, 0.01168, 1.968888)
    else:
        raise ValueError("Unknown window type")


def _one_cos(n, a0, a1, norm):
    t = np.linspace(0, 1, n, False)
    win = a0 - a1 * np.cos(2 * np.pi * t)
    return win * norm


def _two_cos(n, a0, a1, a2, norm):
    t = np.linspace(0, 1, n, False)
    win = a0 - a1 * np.cos(2 * np.pi * t) + a2 * np.cos(4 * np.pi * t)
    return win * norm


def _three_cos(n, a0, a1, a2, a3, norm):
    t = np.linspace(0, 1, n, False)
    win = (
        a0
        - a1 * np.cos(2 * np.pi * t)
        + a2 * np.cos(4 * np.pi * t)
        - a3 * np.cos(6 * np.pi * t)
    )
    return win * norm


def windowed_fft_mag(data, window_type=BLACKMAN_HARRIS_92):
    n = len(data)
    data = np.array(data, dtype=np.float64)
    data -= np.mean(data)
    w = window(n, window_type)
    if w is not None:
        data = data * w
    n_by_2 = (int)(n / 2)
    fft_data = np.fft.fft(data)[0 : n_by_2 + 1]
    fft_data = abs(fft_data) / n
    fft_data[1:n_by_2] *= 2
    return fft_data


def find_harmonics(fft_data, max_harms):
    BW = 3
    harm_bins = np.zeros(max_harms, dtype=int)
    harms = np.zeros(max_harms)
    harm_bws = np.zeros(max_harms, dtype=int)

    _, fund_bin = get_max(fft_data)
    harm_bins[0] = fund_bin

    for h in range(1, max_harms + 1):
        # first find the location by taking max in area of uncertainty
        mask = init_mask(len(fft_data), False)
        nominal_bin = h * fund_bin
        h_2 = h / 2
        if h > 1:
            mask = set_mask(mask, nominal_bin - h_2, nominal_bin + h_2)
            for i in range(h - 1):
                mask = clear_mask(mask, harm_bins[i], harm_bins[i])
            _, harm_bins[h - 1] = masked_max(fft_data, mask)

        mask = clear_mask(mask, nominal_bin - h_2, nominal_bin + h_2)
        mask = set_mask(mask, harm_bins[h - 1] - BW, harm_bins[h - 1] + BW)
        for i in range(h - 1):
            mask = clear_mask(mask, harm_bins[i] - BW, harm_bins[i] + BW)
        harms[h - 1], harm_bws[h - 1] = masked_sum_of_sq(fft_data, mask)
    return (harm_bins, harms, harm_bws)


def calculate_auto_mask(fft_data, harm_bins, window_type):
    BANDWIDTH_DIVIDER = 80
    NUM_INITAL_NOISE_HARMS = 5
    n = len(fft_data)
    bw = n / BANDWIDTH_DIVIDER

    mask = init_mask(n)
    for i in range(NUM_INITAL_NOISE_HARMS):
        clear_mask(mask, harm_bins[i] - bw, harm_bins[i] + bw)
    mask[0] = False

    noise_est, noise_bins = masked_sum(fft_data, mask)
    noise_est /= noise_bins

    mask = init_mask(n)
    clear_mask_at_dc(mask, window_type)
    for h in harm_bins:
        if mask[h] == 0:
            continue

        j = 1
        while (
            h - j > 0
            and mask[h - j] == 1
            and sum(fft_data[(h - j) : (h - j + 3)]) / 3 > noise_est
        ):
            j += 1
        low = h - j + 1

        j = 1
        while (
            h + j < n
            and mask[h + j] == 1
            and sum(fft_data[(h + j - 2) : (h + j + 1)]) / 3 > noise_est
        ):
            j += 1
        high = h + j - 1

        clear_mask(mask, low, high)

    return mask


def find_spur(find_in_harms, fund_bin, harms, harm_bws, fft_data, window_type):
    if find_in_harms:
        spur, index = get_max(harms[1:])
        return (spur, harm_bws[index + 1])
    else:
        return find_spur_in_data(fft_data, window_type, fund_bin)


def find_spur_in_data(fft_data, window_type, fund_bin):
    BW = 3
    n = len(fft_data)
    mask = init_mask(n)
    mask = clear_mask_at_dc(mask, window_type)
    mask = clear_mask(mask, fund_bin - BW, fund_bin + BW)

    index = 0
    for i, v in enumerate(mask):
        if v:
            index = i
            break

    max_value = masked_sum_of_sq(fft_data, mask, index - BW, index + BW)
    max_index = index

    while index < len(fft_data):
        if mask[index]:
            value = masked_sum_of_sq(fft_data, mask, index - BW, index + BW)
            if value > max_value:
                max_value = value
                max_index = index
        index += 1
    _, spur_bin = masked_max(fft_data, mask, max_index - BW, max_index + BW)
    spur, spur_bw = masked_sum_of_sq(fft_data, mask, spur_bin - BW, spur_bin + BW)
    return (spur, spur_bw)


def clear_mask_at_dc(mask, window_type):
    return clear_mask(mask, 0, window_type >> 4)


def init_mask(n, initial_value=True):
    if initial_value:
        return np.ones(n, dtype=bool)
    else:
        return np.zeros(n, dtype=bool)


def set_mask(mask, start, end, set_value=True):
    nyq = len(mask)
    mask[map_nyquist(np.array(range(int(start), int(end) + 1)), nyq)] = set_value
    return mask


def clear_mask(mask, start, end):
    return set_mask(mask, start, end, False)


def map_nyquist(indices, nyq):
    n = 2 * (nyq - 1)
    indices = np.mod(indices + n, n)
    if isinstance(indices, np.ndarray):
        indices[indices > nyq] = n - indices[indices > nyq]
    else:
        indices = n - indices if indices > nyq else indices
    return indices


def masked_max(data, mask, start=0, finish=None):
    if finish is None:
        finish = len(data) - 1
    _, indices = masked_subset(mask, start, finish)
    [value, i] = get_max(data[indices])
    return (value, indices[i])


def masked_sum(data, mask, start=0, finish=None):
    if finish is None:
        finish = len(data) - 1
    mask, indices = masked_subset(mask, start, finish)
    value = sum(data[indices])
    return value, len(indices)


def masked_sum_of_sq(data, mask, start=0, finish=None):
    if finish is None:
        finish = len(data) - 1
    mask, indices = masked_subset(mask, start, finish)
    value = sum(data[indices] * data[indices])
    return value, len(indices)


def masked_subset(mask, start, finish):
    nyq = len(mask) - 1
    mapped_subset = map_nyquist(np.array(range(start, finish)), nyq)
    indices = np.array(range(0, finish))
    indices = indices[mapped_subset]
    mask = mask[mapped_subset]
    indices = indices[mask]
    return (mask, indices)


def get_max(data):
    index = np.argmax(data)
    return (data[index], index)
