#!/usr/bin/env python3
#  Must use Python 3
# Copyright (C) 2022 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# Utility functions for CN0566 Phaser

import pickle
from time import sleep

import numpy as np
from numpy import (
    absolute,
    argmax,
    argsort,
    cos,
    exp,
    floor,
    linspace,
    log10,
    multiply,
    pi,
)
from numpy.fft import fft, fftfreq, fftshift
from scipy import signal


def to_sup(angle):
    """ Return suplimentary angle if greater than 180 degrees. """
    if angle > 180.0:
        angle -= 360.0
    return angle


def find_peak_bin(cn0566, verbose=False):
    """ Simple function to find the peak frequency bin of the incoming signal.
        sets nomial phases and gains first."""
    win = np.blackman(cn0566.sdr.rx_buffer_size)
    # First, locate fundamental.
    cn0566.set_all_gain(127)
    cn0566.set_beam_phase_diff(0.0)
    data = cn0566.sdr.rx()  # read a buffer of data
    y_sum = (data[0] + data[1]) * win
    s_sum = np.fft.fftshift(np.absolute(np.fft.fft(y_sum)))
    return np.argmax(s_sum)


def calculate_plot(cn0566, gcal_element=0, cal_element=0):
    """ Calculate all the values required to do different antenna pattern plots.
        parameters:
            cn0566: Handle to CN0566 instance
        returns:
            gain: Antenna gain data
            angle: Antenna angles (calculated from phases sent to array)
            delta: Delta between sub-arrays (for monopulse tracking)
            diff_error:
            beam_phase:
            xf:
            max_gain:
            PhaseValues: Actual phase values sent to array
    """

    sweep_angle = 180  # This swweps from -70 deg to +70
    # These are all the phase deltas (i.e. phase difference between Rx1 and Rx2, then Rx2 and Rx3, etc.) we'll sweep
    PhaseValues = np.arange(-(sweep_angle), (sweep_angle), cn0566.phase_step_size)
    max_signal = (
        -100000
    )  # Reset max_signal.  We'll keep track of the maximum signal we get as we do this 140 loop.
    max_angle = -90  # Reset max_angle. This is the angle where we saw the max signal.
    gain, delta, beam_phase, angle, diff_error = (
        [],
        [],
        [],
        [],
        [],
    )  # Create empty lists
    NumSamples = cn0566.sdr.rx_buffer_size
    win = np.blackman(NumSamples)
    win /= np.average(win)

    for PhDelta in PhaseValues:  # These sweeps phase value from -180 to 180
        # set Phase of channels based on Calibration Flag status and calibration element

        cn0566.set_beam_phase_diff(PhDelta)
        # arcsin argument must be between 1 and -1, or numpy will throw a warning
        if PhDelta >= 0:
            SteerAngle = np.degrees(
                np.arcsin(
                    max(
                        min(
                            1,
                            (cn0566.c * np.radians(np.abs(PhDelta)))
                            / (2 * np.pi * cn0566.SignalFreq * cn0566.element_spacing),
                        ),
                        -1,
                    )
                )
            )  # positive PhaseDelta covers 0deg to 90 deg
        else:
            SteerAngle = -(
                np.degrees(
                    np.arcsin(
                        max(
                            min(
                                1,
                                (cn0566.c * np.radians(np.abs(PhDelta)))
                                / (
                                    2
                                    * np.pi
                                    * cn0566.SignalFreq
                                    * cn0566.element_spacing
                                ),
                            ),
                            -1,
                        )
                    )
                )
            )  # negative phase delta covers 0 deg to -90 deg

        total_sum, total_delta, total_angle = 0, 0, 0

        for count in range(0, cn0566.Averages):  # repeat loop and average the results
            data = (
                cn0566.sdr.rx()
            )  # read a buffer of data from Pluto using pyadi-iio library (adi.py)
            y_sum = (data[0] + data[1]) * win
            y_delta = (data[0] - data[1]) * win
            s_sum = np.fft.fftshift(np.absolute(np.fft.fft(y_sum)))
            s_delta = np.fft.fftshift(np.absolute(np.fft.fft(y_delta)))
            total_angle = total_angle + (
                np.angle(s_sum[np.argmax(s_sum)]) - np.angle(s_delta[np.argmax(s_sum)])
            )
            s_mag_sum = np.maximum(
                np.abs(s_sum[np.argmax(s_sum)]) * 2 / np.sum(win), 10 ** (-15)
            )  # Prevent taking log of zero
            s_mag_delta = np.maximum(
                np.abs(s_delta[np.argmax(s_sum)]) * 2 / np.sum(win), 10 ** (-15)
            )
            total_sum = total_sum + (
                20 * np.log10(s_mag_sum / (2 ** 12))
            )  # sum up all the loops, then we'll avg
            total_delta = total_delta + (20 * np.log10(s_mag_delta / (2 ** 12)))

        PeakValue_sum = total_sum / cn0566.Averages
        PeakValue_delta = total_delta / cn0566.Averages
        PeakValue_angle = total_angle / cn0566.Averages

        if np.sign(PeakValue_angle) == -1:
            target_error = min(
                -0.01,
                (
                    np.sign(PeakValue_angle) * (PeakValue_sum - PeakValue_delta)
                    + np.sign(PeakValue_angle) * (PeakValue_sum + PeakValue_delta) / 2
                )
                / (PeakValue_sum + PeakValue_delta),
            )
        else:
            target_error = max(
                0.01,
                (
                    np.sign(PeakValue_angle) * (PeakValue_sum - PeakValue_delta)
                    + np.sign(PeakValue_angle) * (PeakValue_sum + PeakValue_delta) / 2
                )
                / (PeakValue_sum + PeakValue_delta),
            )

        if (
            PeakValue_sum > max_signal
        ):  # take the largest value, so that we know where to point the compass
            max_signal = PeakValue_sum
            #            max_angle = PeakValue_angle
            #            max_PhDelta = PhDelta
            data_fft = data[0] + data[1]
        gain.append(PeakValue_sum)
        delta.append(PeakValue_delta)
        beam_phase.append(PeakValue_angle)
        angle.append(SteerAngle)
        diff_error.append(target_error)

    y = data_fft * win
    sp = np.absolute(np.fft.fft(y))
    sp = np.fft.fftshift(sp)
    s_mag = (
        np.abs(sp) * 2 / np.sum(win)
    )  # Scale FFT by window and /2 since we are using half the FFT spectrum
    s_mag = np.maximum(s_mag, 10 ** (-15))
    max_gain = 20 * np.log10(
        s_mag / (2 ** 12)
    )  # Pluto is a 12 bit ADC, so use that to convert to dBFS
    ts = 1 / float(cn0566.sdr.sample_rate)
    xf = np.fft.fftfreq(NumSamples, ts)
    xf = np.fft.fftshift(xf)  # this is the x axis (freq in Hz) for our fft plot
    # Return values/ parameter based on Calibration Flag status

    return gain, angle, delta, diff_error, beam_phase, xf, max_gain, PhaseValues


def get_signal_levels(cn0566, verbose=False):
    """" Measure signal levels. Without a decent signal, all bets are off. """
    peak_bin = find_peak_bin(cn0566)
    #    channel_levels, plot_data = measure_channel_gains(cn0566, peak_bin, verbose=False)
    #    return channel_levels

    channel_levels = []

    if verbose is True:
        print("Peak bin at ", peak_bin, " out of ", cn0566.sdr.rx_buffer_size)
    # gcal_element indicates current element/channel which is being calibrated
    for element in range(0, (cn0566.num_elements)):
        if verbose is True:
            print("Calibrating Element " + str(element))

        gcal_val, spectrum = measure_element_gain(cn0566, element, peak_bin, verbose)
        if verbose is True:
            print("Measured signal level (ADC counts): " + str(gcal_val))
        channel_levels.append(gcal_val)  # make a list of intermediate cal values
    return channel_levels


def channel_calibration(cn0566, verbose=False):
    """" Do this BEFORE gain_calibration.
         Performs calibration between the two ADAR1000 channels. Accounts for all
         sources of mismatch between the two channels: ADAR1000s, mixers, and
         the SDR (Pluto) inputs. """
    peak_bin = find_peak_bin(cn0566)
    channel_levels, plot_data = measure_channel_gains(cn0566, peak_bin, verbose=False)
    ch_mismatch = 20.0 * np.log10(channel_levels[0] / channel_levels[1])
    if verbose is True:
        print("channel mismatch: ", ch_mismatch, " dB")
    if ch_mismatch > 0:  # Channel 0 hihger, boost ch1:
        cn0566.ccal = [0.0, ch_mismatch]
    else:  # Channel 1 higher, boost ch0:
        cn0566.ccal = [-ch_mismatch, 0.0]
    pass


def gain_calibration(cn0566, verbose=False):
    """ Perform the Gain Calibration routine."""

    """Set the gain calibration flag and create an empty gcal list. Looping through all the possibility i.e. setting
        gain of one of the channel to max and all other to 0 create a zero-list where number of 0's depend on total
        channels. Replace only 1 element with max gain at a time. Now set gain values according to above Note."""

    cn0566.gain_cal = True  # Gain Calibration Flag
    gcalibrated_values = []  # Intermediate cal values list
    plot_data = []
    peak_bin = find_peak_bin(cn0566)
    if verbose is True:
        print("Peak bin at ", peak_bin, " out of ", cn0566.sdr.rx_buffer_size)
    # gcal_element indicates current element/channel which is being calibrated
    for gcal_element in range(0, (cn0566.num_elements)):
        if verbose is True:
            print("Calibrating Element " + str(gcal_element))

        gcal_val, spectrum = measure_element_gain(
            cn0566, gcal_element, peak_bin, verbose=True
        )
        if verbose is True:
            print("Measured signal level (ADC counts): " + str(gcal_val))
        gcalibrated_values.append(gcal_val)  # make a list of intermediate cal values
        plot_data.append(spectrum)

    """ Minimum gain of intermediated cal val is set to Maximum value as we cannot go beyond max value and gain
        of all other channels are set accordingly"""
    print("gcalibrated values: ", gcalibrated_values)
    for k in range(0, 8):
        #            x = ((gcalibrated_values[k] * 127) / (min(gcalibrated_values)))
        cn0566.gcal[k] = min(gcalibrated_values) / (gcalibrated_values[k])

    cn0566.gain_cal = (
        False  # Reset the Gain calibration Flag once system gain is calibrated
    )
    return plot_data
    # print(cn0566.gcal)


def measure_channel_gains(
    cn0566, peak_bin, verbose=False
):  # Default to central element
    """ Calculate all the values required to do different plots. It method calls set_beam_phase_diff and
        sets the Phases of all channel. All the math is done here.
        parameters:
            gcal_element: type=int
                        If gain calibration is taking place, it indicates element number whose gain calibration is
                        is currently taking place
            cal_element: type=int
                        If Phase calibration is taking place, it indicates element number whose phase calibration is
                        is currently taking place
            peak_bin: type=int
                        Peak bin to examine around for amplitude
    """
    width = 10  # Bins around fundamental to sum
    win = signal.windows.flattop(cn0566.sdr.rx_buffer_size)
    win /= np.average(np.abs(win))  # Normalize to unity gain
    plot_data = []
    channel_level = []
    cn0566.set_rx_hardwaregain(6, False)
    for channel in range(0, 2):
        # Start with sdr CH0 elements
        cn0566.set_all_gain(0, apply_cal=False)  # Start with all gains set to zero
        cn0566.set_chan_gain(
            (1 - channel) * 4 + 0,
            127,
            apply_cal=False,  # 1-channel because wonky channel mapping!!
        )  # Set element to max
        cn0566.set_chan_gain(
            (1 - channel) * 4 + 1, 127, apply_cal=False
        )  # Set element to max
        cn0566.set_chan_gain(
            (1 - channel) * 4 + 2, 127, apply_cal=False
        )  # Set element to max
        cn0566.set_chan_gain(
            (1 - channel) * 4 + 3, 127, apply_cal=False
        )  # Set element to max

        sleep(1.0)  # todo - remove when driver fixed to compensate for ADAR1000 quirk
        if verbose:
            print("measuring channel ", channel)
        total_sum = 0
        # win = np.blackman(cn0566.sdr.rx_buffer_size)

        spectrum = np.zeros(cn0566.sdr.rx_buffer_size)

        for count in range(
            0, cn0566.Averages
        ):  # repeatsnip loop and average the results
            data = cn0566.sdr.rx()  # todo - remove once confirmed no flushing necessary
            data = cn0566.sdr.rx()  # read a buffer of data
            y_sum = (data[0] + data[1]) * win

            s_sum = np.fft.fftshift(np.absolute(np.fft.fft(y_sum)))
            spectrum += s_sum

            # Look for peak value within window around fundamental (reject interferers)
            s_mag_sum = np.max(s_sum[peak_bin - width : peak_bin + width])
            total_sum += s_mag_sum

        spectrum /= cn0566.Averages * cn0566.sdr.rx_buffer_size
        PeakValue_sum = total_sum / (cn0566.Averages * cn0566.sdr.rx_buffer_size)
        plot_data.append(spectrum)
        channel_level.append(PeakValue_sum)

    return channel_level, plot_data


def measure_element_gain(
    cn0566, cal, peak_bin, verbose=False
):  # Default to central element
    """ Calculate all the values required to do different plots. It method calls set_beam_phase_diff and
        sets the Phases of all channel. All the math is done here.
        parameters:
            gcal_element: type=int
                        If gain calibration is taking place, it indicates element number whose gain calibration is
                        is currently taking place
            cal_element: type=int
                        If Phase calibration is taking place, it indicates element number whose phase calibration is
                        is currently taking place
            peak_bin: type=int
                        Peak bin to examine around for amplitude
    """
    width = 10  # Bins around fundamental to sum
    cn0566.set_rx_hardwaregain(6)  # Channel calibration defaults to True
    cn0566.set_all_gain(0, apply_cal=False)  # Start with all gains set to zero
    cn0566.set_chan_gain(cal, 127, apply_cal=False)  # Set element to max
    sleep(1.0)  # todo - remove when driver fixed to compensate for ADAR1000 quirk
    if verbose:
        print("measuring element: ", cal)
    total_sum = 0
    # win = np.blackman(cn0566.sdr.rx_buffer_size)
    win = signal.windows.flattop(cn0566.sdr.rx_buffer_size)
    win /= np.average(np.abs(win))  # Normalize to unity gain
    spectrum = np.zeros(cn0566.sdr.rx_buffer_size)

    for count in range(0, cn0566.Averages):  # repeatsnip loop and average the results
        data = cn0566.sdr.rx()  # todo - remove once confirmed no flushing necessary
        data = cn0566.sdr.rx()  # read a buffer of data
        y_sum = (data[0] + data[1]) * win

        s_sum = np.fft.fftshift(np.absolute(np.fft.fft(y_sum)))
        spectrum += s_sum

        # Look for peak value within window around fundamental (reject interferers)
        s_mag_sum = np.max(s_sum[peak_bin - width : peak_bin + width])
        total_sum += s_mag_sum

    spectrum /= cn0566.Averages * cn0566.sdr.rx_buffer_size
    PeakValue_sum = total_sum / (cn0566.Averages * cn0566.sdr.rx_buffer_size)

    return PeakValue_sum, spectrum


def phase_cal_sweep(cn0566, peak_bin, ref=0, cal=1):
    """ Calculate all the values required to do different plots. It method
        calls set_beam_phase_diff and sets the Phases of all channel.
        parameters:
            gcal_element: type=int
                        If gain calibration is taking place, it indicates element number whose gain calibration is
                        is currently taking place
            cal_element: type=int
                        If Phase calibration is taking place, it indicates element number whose phase calibration is
                        is currently taking place
            peak_bin: type=int
                        Which bin the fundamental is in.
                        This prevents detecting other spurs when deep in a null.
    """

    cn0566.set_all_gain(0)  # Reset all elements to zero
    cn0566.set_chan_gain(ref, 127, apply_cal=True)  # Set two adjacent elements to zero
    cn0566.set_chan_gain(cal, 127, apply_cal=True)
    sleep(1.0)

    cn0566.set_chan_phase(ref, 0.0, apply_cal=False)  # Reference element
    # win = np.blackman(cn0566.sdr.rx_buffer_size)
    win = signal.windows.flattop(cn0566.sdr.rx_buffer_size)  # Super important!
    win /= np.average(np.abs(win))  # Normalize to unity gain
    width = 10  # Bins around fundamental to sum
    sweep_angle = 180
    # These are all the phase deltas (i.e. phase difference between Rx1 and Rx2, then Rx2 and Rx3, etc.) we'll sweep
    PhaseValues = np.arange(-(sweep_angle), (sweep_angle), cn0566.phase_step_size)

    gain = []  # Create empty lists
    for phase in PhaseValues:  # These sweeps phase value from -180 to 180
        # set Phase of channels based on Calibration Flag status and calibration element
        cn0566.set_chan_phase(cal, phase, apply_cal=False)
        total_sum = 0
        for count in range(0, cn0566.Averages):  # repeat loop and average the results
            data = cn0566.sdr.rx()  # read a buffer of data
            data = cn0566.sdr.rx()
            y_sum = (data[0] + data[1]) * win
            s_sum = np.fft.fftshift(np.absolute(np.fft.fft(y_sum)))

            # Pick (uncomment) one:
            # 1) RSS sum a few bins around max
            # s_mag_sum = np.sqrt(
            #     np.sum(np.square(s_sum[peak_bin - width : peak_bin + width]))
            # )

            # 2) Take maximum value
            # s_mag_sum = np.maximum(s_mag_sum, 10 ** (-15))

            # 3) Apparently the correct way, use flat-top window, look for peak
            s_mag_sum = np.max(s_sum[peak_bin - width : peak_bin + width])
            s_mag_sum = np.max(s_sum)
            total_sum += s_mag_sum
        PeakValue_sum = total_sum / (cn0566.Averages * cn0566.sdr.rx_buffer_size)
        gain.append(PeakValue_sum)

    return (
        PhaseValues,
        gain,
    )  # beam_phase, max_gain


def phase_calibration(cn0566, verbose=False):
    """ Perform the Phase Calibration routine."""

    """ Set the phase calibration flag and create an empty pcal list. Looping through all the possibility
        i.e. setting gain of two adjacent channels to gain calibrated values and all other to 0 create a zero-list
        where number of 0's depend on total channels. Replace gain value of 2 adjacent channel.
        Now set gain values according to above Note."""
    peak_bin = find_peak_bin(cn0566)
    if verbose is True:
        print("Peak bin at ", peak_bin, " out of ", cn0566.sdr.rx_buffer_size)

    #        cn0566.phase_cal = True  # Gain Calibration Flag
    #        cn0566.load_gain_cal('gain_cal_val.pkl')  # Load gain cal val as phase cal is dependent on gain cal
    cn0566.pcal = [0, 0, 0, 0, 0, 0, 0, 0]
    cn0566.ph_deltas = [0, 0, 0, 0, 0, 0, 0]
    plot_data = []
    # cal_element indicates current element/channel which is being calibrated
    # As there are 8 channels and we take two adjacent chans for calibration we have 7 cal_elements
    for cal_element in range(0, 7):
        if verbose is True:
            print("Calibrating Element " + str(cal_element))

        PhaseValues, gain, = phase_cal_sweep(
            cn0566, peak_bin, cal_element, cal_element + 1
        )

        ph_delta = to_sup((180 - PhaseValues[gain.index(min(gain))]) % 360.0)
        if verbose is True:
            print("Null found at ", PhaseValues[gain.index(min(gain))])
            print("Phase Delta to correct: ", ph_delta)
        cn0566.ph_deltas[cal_element] = ph_delta

        cn0566.pcal[cal_element + 1] = to_sup(
            (cn0566.pcal[cal_element] - ph_delta) % 360.0
        )
        plot_data.append(gain)
    return PhaseValues, plot_data


def save_hb100_cal(freq, filename="hb100_freq_val.pkl"):
    """ Saves measured frequency calibration file."""
    with open(filename, "wb") as file1:
        pickle.dump(freq, file1)  # save calibrated gain value to a file
        file1.close()


def load_hb100_cal(filename="hb100_freq_val.pkl"):
    """ Load frequency measurement value, set to 10.5GHz if no
        parameters:
            filename: type=string
                      Provide path of gain calibration file
    """
    try:
        with open(filename, "rb") as file1:
            freq = pickle.load(file1)  # Load gain cal values
    except Exception:
        print("file not found, loading default 10.5GHz")
    return freq


def spec_est(x, fs, ref=2 ** 15, plot=False):

    N = len(x)

    # Apply window
    window = signal.kaiser(N, beta=38)
    window /= np.average(window)
    x = multiply(x, window)

    # Use FFT to get the amplitude of the spectrum
    ampl = 1 / N * fftshift(absolute(fft(x)))
    ampl = 20 * log10(ampl / ref + 10 ** -20)

    # FFT frequency bins
    freqs = fftshift(fftfreq(N, 1 / fs))

    # ampl and freqs for real data
    if not np.iscomplexobj(x):
        ampl = ampl[0 : len(ampl) // 2]
        freqs = freqs[0 : len(freqs) // 2]

    if plot:
        # Plot signal, showing how endpoints wrap from one chunk to the next
        import matplotlib.pyplot as plt

        plt.subplot(2, 1, 1)
        plt.plot(x, ".-")
        plt.plot(1, 1, "r.")  # first sample of next chunk
        plt.margins(0.1, 0.1)
        plt.xlabel("Time [s]")
        # Plot shifted data on a shifted axis
        plt.subplot(2, 1, 2)
        plt.plot((freqs), (ampl))
        plt.margins(0.1, 0.1)
        plt.xlabel("Frequency [Hz]")
        plt.tight_layout()
        plt.show()

    return ampl, freqs
