# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""
Test script for initial 50-piece build of ADALM-MMSC boards
"""

import argparse
from sys import exit

import genalyzer as gn
import libm2k
import workshop

import adi

parser = argparse.ArgumentParser(
    description="Generate a noisy signal on the M2K, record it using the AD4080ARDZ, and do a Fourier analysis."
)
parser.add_argument(
    "-m",
    "--m2k_uri",
    default="ip:192.168.2.1",
    help="LibIIO context URI of the ADALM2000",
)
parser.add_argument(
    "-p",
    "--ad4080_com_port",
    default="COM17",
    help="ADALM-MMSC port, COMx (Windows) or /dev/ttyx (Linux)",
)
args = vars(parser.parse_args())

# Configuration
fs_out = 7500000  # Generated waveform sample rate
fs_in = 40000000  # Received waveform sample rate. AD4080 fixed at 40Msps

# Tone parameters
fsr = 2.0  # Full-scale range in Volts
fund_freq = 100000.0  # Hz

# Test limits

rl_base = -1.55  # db from 100 kHz baseline to RL @ 500 kHz
rm_base = -5.22  # db from 100 kHz baseline to RM @ 500 kHz
rh_base = -12.16  # db from 100 kHz baseline to RH @ 500 kHz
delta_tol = 2.5  # db tolerance


# FFT parameters
window = gn.Window.BLACKMAN_HARRIS  # FFT window
npts = 16384  # Receive buffer size
awf_npts = 16384
navg = 2  # No. of fft averages
nfft = npts // navg  # No. of points per FFT

# 1. Connect to M2K and AD4080
my_m2k = libm2k.m2kOpen()  # (args['m2k_uri'])
if my_m2k is None:
    print("Connection Error: No ADALM2000 device available/connected to your PC.")
    exit(1)

# Initialize DAC channel 0
aout = my_m2k.getAnalogOut()
aout.reset()
my_m2k.calibrateDAC()
aout.setSampleRate(0, fs_out)
aout.enableChannel(0, True)
aout.setCyclic(True)  # Send buffer repeatedly, not just once

# Connect to AD4080
my_ad4080 = adi.ad4080("serial:" + args["ad4080_com_port"] + ",230400")
if my_ad4080 is None:
    print("Connection Error: No ADALM-MMSC device at this port.")
    exit(1)

print("Connected to ADALM-MMSC at serial port COM / tty: " + args["ad4080_com_port"])

# Initialize ADC
my_ad4080.rx_buffer_size = npts
my_ad4080.filter_type = "none"
print(f"Sampling frequency: {my_ad4080.sampling_frequency}")
# print(f'Available sampling frequencies: {my_ad4080.sampling_frequency_available}') # not in ad4080 class yet
assert my_ad4080.sampling_frequency == fs_in  # Check 40Msps assumption


# Nudge fundamental to the closest coherent bin
fund_freq = gn.coherent(nfft, fs_out, fund_freq)

# Build up the signal from the fundamental, harmonics, and noise tones

awf = gn.cos(awf_npts, fs_out, fsr, fund_freq, 0, 0, 0)

# 3. Transmit generated waveform
aout.push([awf])  # Would be [awf0, awf1] if sending data to multiple channels

# 4. Receive one buffer of samples
data_in_raw = my_ad4080.rx()

# Convert ADC codes to Volts
data_in = data_in_raw * my_ad4080.channel[0].scale / 1e3  # Scale is in millivolts/code


# 5. Analyze recorded waveform
fft_results = workshop.fourier_analysis(
    data_in, fundamental=fund_freq, sampling_rate=fs_in, window=window
)

baseline = fft_results["A:mag_dbfs"]  # Save for later

failed_tests = []
results = []

results.append("SNR: " + str(fft_results["snr"]))
results.append("SINAD: " + str(fft_results["sinad"]))
results.append("initial magnitude: " + str(fft_results["A:mag_dbfs"]))

if (-5.0 < fft_results["A:mag_dbfs"] < -2.0) is False:
    failed_tests.append("Failed full-scale amplitude")
if (55.0 < fft_results["snr"] < 70.0) is False:
    failed_tests.append("Failed SNR")
if (55.0 < fft_results["sinad"] < 70.0) is False:
    failed_tests.append("Failed SINAD")


# Tests to run: Start with CIN and CF in 100 pF position
# Set resistors to minimum resistance (RM). Run baseline distortion / THD test at 100 kHz.
# Save amplitude. Re-run at 500 kHz - verify dropped by less than 2 dB from baseline
# Prompt to set jumpers to mid resistance. Verify dropped by between 3 and 5 dB from baseline.
# Prompt to set jumpers to high resistance. Verify dropped by between 10 and 14 dB from baseline.


# Push 500 kHz tone:
fund_freq = gn.coherent(nfft, fs_out, 500000)
awf = gn.cos(awf_npts, fs_out, fsr, fund_freq, 0, 0, 0)
aout.push([awf])  # Would be [awf0, awf1] if sending data to multiple channels


# Verify RL
print("CIN, CF are set to CH value (100 pF)\n")
input("Verify RA, RB set to RL LOW value. Hit Enter to continue.")
data_in_raw = my_ad4080.rx()
data_in = data_in_raw * my_ad4080.channel[0].scale / 1e3  # Scale is in millivolts/code
fft_results = workshop.fourier_analysis(
    data_in, fundamental=fund_freq, sampling_rate=fs_in, window=window
)
if (
    (rl_base - delta_tol)
    < (fft_results["A:mag_dbfs"] - baseline)
    < (rl_base + delta_tol)
) is False:
    failed_tests.append("Failed 500 kHz RL test")

results.append("500 kHz RL mag.: " + str(fft_results["A:mag_dbfs"]))


# Verify RM
input("VerifyRA, RB set to RM MID value. Hit Enter to continue.")
data_in_raw = my_ad4080.rx()
data_in = data_in_raw * my_ad4080.channel[0].scale / 1e3  # Scale is in millivolts/code
fft_results = workshop.fourier_analysis(
    data_in, fundamental=fund_freq, sampling_rate=fs_in, window=window
)
if (
    (rm_base - delta_tol)
    < (fft_results["A:mag_dbfs"] - baseline)
    < (rm_base + delta_tol)
) is False:
    failed_tests.append("Failed 500 kHz RM test")

results.append("500 kHz RM mag.: " + str(fft_results["A:mag_dbfs"]))

# Verify RH
input("Verify RA, RB set to RH HIGH value. Hit Enter to continue.")
data_in_raw = my_ad4080.rx()
data_in = data_in_raw * my_ad4080.channel[0].scale / 1e3  # Scale is in millivolts/code
fft_results = workshop.fourier_analysis(
    data_in, fundamental=fund_freq, sampling_rate=fs_in, window=window
)
if (
    (rh_base - delta_tol)
    < (fft_results["A:mag_dbfs"] - baseline)
    < (rh_base + delta_tol)
) is False:
    failed_tests.append("Failed 500 kHz RH test")

results.append("500 kHz RH mag.: " + str(fft_results["A:mag_dbfs"]))

print("Result summary for debugging:")
print(results)

if len(failed_tests) == 0:
    print("WooHoo, board passes!")
else:
    print("D'oh! Board fails these test(s)")
    print(failed_tests)

# Done talking to hardware, close down...
del my_ad4080
libm2k.contextCloseAll()
del my_m2k
