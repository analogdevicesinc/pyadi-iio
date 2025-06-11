# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import adi
import matplotlib.pyplot as plt
import numpy as np
import time as dt
import ADMX6001_MultiClass_pCal as HMC
from scipy.fft import fft, rfftfreq

# Initialize ADMX6001 board
HH = HMC.Hammerhead("ip:192.168.2.1")

# AD4080 calibration
HH.AD4080_CAl()

# AD9213 DC offset calibration

# Initialize ADMX6001 board again for data acquisition
HH = HMC.Hammerhead("ip:192.168.2.1")

#HH.run_cal(0) # calibrate to specific dc offset voltage

HH.set_atten_path(0) # 0 for low attenuation (0dB), 1 for high attenuation (18dB)


# Set offset voltage in mV for the ADL5580 bias
dac_offset1 = 0
HH.set_dac_offset(dac_offset1)

hispeed_data1 = HH.capture_data_ad9213(2**16) # Capture specified # of samples @ 10GSPS

# Plot the AD9213 data
HH.plot_data_ad9213(hispeed_data1) # Plot data captured by high speed path

# Sample rate and duration
sampling_rate = 10e9  # 10GSPS
# Perform FFT of the AD9213 data
N_samples = len(hispeed_data1)
yf = fft(hispeed_data1)
xf = rfftfreq(N_samples, 1 / sampling_rate)
yf_h = yf[range(N_samples // 2)]  #One side if spectrum
xf_h = xf[range(N_samples // 2)]  #One side if spectrum

# Find the primary frequency
idx = np.argmax(np.abs(yf[1:len(yf_h)])) # to skip DC
primary_freq = np.abs(xf[idx+1])

# plot AD9213 data and spectrum
x_time = np.arange(0, len(hispeed_data1))*(10**(-4))
fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.plot(x_time, hispeed_data1)
ax1.set_title('AD9213: data')
ax1.set_xlabel(r'Time ($\mu$s)')
ax1.set_ylabel('AD9213 data (LSBs)')
ax1.set_ylim([-2048, 2048])

ax2.plot(xf_h/1e6, 20*np.log10(np.abs(yf_h)))
ax2.plot(xf_h[idx+1]/1e6, 20*np.log10(np.abs(yf_h[idx+1])), 'ro', label='Primary frequency')
ax2.set_title('AD9213: spectrum')
ax2.set_xlabel('Frequency (MHz)')
ax2.set_ylabel('AD9213 spectrum (dB)')
plt.tight_layout()

# The use can save the plot of AD9213 data and spectrum as a .png image using the plt.savefig method, as in the next line
#plt.savefig("AD9213DataSpectrum.png")
#print("\nThis plot of AD9213 data and spectrum has been saved as AD9213DataSpectrum.png")
print('\nIf the user is interested in saving the plot as a file, please remove # to un-comment line#68 of ADMX6001_acquisition.py.')

plt.show(block=False)
plt.pause(3)

plt.close(fig)

print(f"\nAD9213: The primary frequency index {idx+1} ")
print(f"AD9213: The primary frequency is {primary_freq} Hz")

# Example code to set the ADL5580 to 200mV bias (move the signal down by 200mV)
# Use case example: positive unipolar signal -> move the signal to the negative region
# to avoid clipping at the upper-limit of AD9213 input dynamic range
dac_offset2 = 200  # Set offset voltage in mV
HH.set_dac_offset(dac_offset2) # Set offset voltage in mV

hispeed_data2 = HH.capture_data_ad9213(2**16) # Capture specified # of samples @ 10GSPS

HH.plot_data_ad9213(hispeed_data2) # Plot data captured by high speed path

# Example code to set the ADL5580 to 200mV bias (move the signal up by 200mV)
# Use case example: negative unipolar signal -> move the signal to the positive region
# to avoid clipping at the lower-limit of AD9213 input dynamic range
dac_offset3 = -200  # Set offset voltage in mV
HH.set_dac_offset(dac_offset3) # Set offset voltage in mV

hispeed_data3 = HH.capture_data_ad9213(2**16) # Capture specified # of samples @ 10GSPS

HH.plot_data_ad9213(hispeed_data3) # Plot data captured by high speed path

# plot three AD9213 acquisition withs different dc bias/offset
x_time = np.arange(0, len(hispeed_data1))*(10**(-4))
fig, (ax) = plt.subplots(1, 1)
ax.plot(x_time, hispeed_data1, label=str(dac_offset1) + 'mV offset')
ax.plot(x_time, hispeed_data2, label=str(dac_offset2) + 'mV offset')
ax.plot(x_time, hispeed_data3, label=str(dac_offset3) + 'mV offset')
ax.legend()
ax.set_xlabel(r'Time ($\mu$s)')
ax.set_ylabel('AD9213 data (LSBs)')
ax.set_ylim([-2048, 2048])
ax.set_title('AD9213 with DC offset')
plt.tight_layout()
plt.show(block=False)

# The use can save the plot of AD9213 data with offsets as a .png image using the plt.savefig method, as in the next line
#plt.savefig("AD9213_offsets.png")
#print("\nThis plot of AD9213 data with different offsets has been saved as AD9213_offsets.png")
print('\nIf the user is interested in saving the plot as a file, please remove # to un-comment line#115 of ADMX6001_acquisition.py.')

plt.pause(3)
plt.close(fig)

# Set the high-speed path offset back to 0 mV (default value)
HH.set_dac_offset(0) # Set offset voltage in mV

# AD4080 data capture example
precision_data = HH.capture_data_ad4080(512) # Capture specified # of samples @ 31.25MSPS

# Sample rate and duration
sampling_rate = 31.25e6  # 31.25MSPS
# Perform FFT
N_samples = len(precision_data)
yf = fft(precision_data)
xf = rfftfreq(N_samples, 1 / sampling_rate)

yf_h = yf[range(N_samples // 2)]  #One side if spectrum
xf_h = xf[range(N_samples // 2)]  #One side if spectrum

# Find the primary frequency
idx = np.argmax(np.abs(yf[1:N_samples])) # to skip DC
primary_freq = np.abs(xf[idx+1])

print(f"\nAD4080: The primary frequency index {idx+1}")
print(f"AD4080: The primary frequency is {primary_freq} Hz")

HH.plot_data_ad4080(precision_data) # Plot data captured by precision path

# plot AD4080 data and spectrum
x_time = np.arange(0, len(precision_data))*(1/sampling_rate)*10**(6)
fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.plot(x_time, precision_data)
ax1.set_title('AD4080: data')
ax1.set_xlabel(r'Time ($\mu$s)')
ax1.set_ylabel('AD4080 data (LSBs)')

ax2.plot(xf_h/1e6, 20*np.log10(np.abs(yf_h)))
ax2.plot(xf_h[idx+1]/1e6, 20*np.log10(np.abs(yf_h[idx+1])), 'ro', label='Primary frequency')
ax2.set_title('AD4080: spectrum')
ax2.set_xlabel('Frequency (MHz)')
ax2.set_ylabel('AD4080 spectrum (dB)')
plt.tight_layout()

# The use can save the plot of AD4080 data and spectrum as a .png image using the plt.savefig method, as in the next line
#plt.savefig("AD4080DataSpectrum.png")
#print("\nThis plot of AD4080 data and spectrum has been saved as AD4080DataSpectrum.png")
print('\nIf the user is interested in saving the plot as a file, please remove # to un-comment line#163 of ADMX6001_acquisition.py.')

plt.show(block=False)
plt.pause(3)
plt.close(fig)

# Save AD9213 abd AD4080 data as .csv
np.savetxt("AD9213_" + str(dac_offset1) + ".csv", hispeed_data1, delimiter=',', fmt='%d')
np.savetxt("AD9213_" + str(dac_offset2) + ".csv", hispeed_data2, delimiter=',', fmt='%d')
np.savetxt("AD9213_" + str(dac_offset3) + ".csv", hispeed_data3, delimiter=',', fmt='%d')
np.savetxt("AD4080.csv", precision_data, delimiter=',', fmt='%d')

input('\nEnd of this example script. \nPlease note each plot is intentionally closed after 3 seconds in this example script. \nPress any key to close ...')
