# Copyright (C) 2023 Analog Devices, Inc.
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

import sys
import adi
import numpy as np
import matplotlib.pyplot as plt
from scipy import fft
from scipy import signal
from scipy.io import wavfile

my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
plot_en = sys.argv[2] if len(sys.argv) >= 3 else 1
spi_type = sys.argv[3] if len(sys.argv) >= 4 else "engine"
input_type = sys.argv[4].lower() if len(sys.argv) >= 5 else "audio"  # "audio" or "sine"

# the device name can be: spi_clasic_ad7984 or spi_engine_ad7984

if spi_type.lower() in ["classic", "clasic"]:
    my_device_name = "spi_clasic_ad7984"
elif spi_type.lower() == "engine":
    my_device_name = "spi_engine_ad7984"
else:
    print(f"Invalid SPI type '{spi_type}'. Using 'engine' as default.")
    print("Valid options: 'engine' or 'classic'")
    my_device_name = "spi_engine_ad7984"

my_ad7984 = adi.ad7689(uri=my_uri,device_name=my_device_name)
#output_wav = 'audio_reconstructed.wav'
my_ad7984.rx_enabled_channels = [0]

# Sample rates
if my_device_name == "spi_engine_ad7984":
    original_sample_rate = 1_333_000
else:
    original_sample_rate = 15_000
    
target_sample_rate = 44100        # Audio sample rate

if input_type == "sine":
    # Sine test mode
    if my_device_name == "spi_engine_ad7984":
        my_ad7984.rx_buffer_size = 8161
    else:
        my_ad7984.rx_buffer_size = 400
    data = my_ad7984.rx()
    data = np.delete(data,0)
    print(f"Captured {len(data)} samples (sine wave mode)")
else:
    if my_device_name == "spi_engine_ad7984":
        my_ad7984.rx_buffer_size = 2**21 # 2.097.152 samples (1.57 seconds @ 1.333MSPS) 1 chunck 
    else:
        my_ad7984.rx_buffer_size = 2**12 # 4096 samples (0.273 seconds @ 15kSPS) 1 chunck

if my_device_name == "spi_engine_ad7984":
    num_chunks = 6  # Number of chunks to capture
else:
    num_chunks = 45  # Number of chunks to capture

all_data = []
for i in range(num_chunks):
    chunk = my_ad7984.rx()
    all_data.extend(chunk)
    print(f"  -> Captured chunk {i+1}/{num_chunks}")
#Capture samples
data = np.array(all_data, dtype=float)
    # Pre-Processing Remove DC offset (center the signal around 0)
data = data - np.mean(data)

#data = my_ad7984.rx()
#wavfile.write(output_wav, 44100, data)

# Resample from 1.333 MSPS to 44.1 kHz
#original_sample_rate = 1_333_000  # ADC sample rate
#target_sample_rate = 44100        # Audio sample rate
if input_type == "audio":
    # Resample to 44.1 kHz
    
    # Compute up/down factors
    gcd = np.gcd(original_sample_rate, target_sample_rate)
    up = target_sample_rate // gcd
    down = original_sample_rate // gcd
    print(f"Resampling: up = {up}, down = {down} (from {original_sample_rate} Hz to {target_sample_rate} Hz)")
    resampled = signal.resample_poly(data, up, down)

    # Normalize and convert to int16
    if np.max(np.abs(resampled)) == 0:
        print("Warning: Signal is all zeros after resampling.")
        resampled = np.zeros_like(resampled)
    else:
        resampled = resampled / np.max(np.abs(resampled))

    # Convert to 16-bit PCM format
    int16_data = (resampled * 32767).astype(np.int16)

    # Save to WAV file
    if my_device_name == "spi_engine_ad7984":
        output_wav = 'audio_reconstructed_engine.wav'
        wavfile.write(output_wav, target_sample_rate, int16_data)
        print(f"Audio written to '{output_wav}' at {target_sample_rate} Hz.")
    else:
        output_wav = 'audio_reconstructed_classic.wav'
        wavfile.write(output_wav, target_sample_rate, int16_data)
        print(f"Audio written to '{output_wav}' at {target_sample_rate} Hz.")
else:
    # === Save raw sample data (original, unresampled) ===
    print("Writing original ADC samples to 'samples_data_buffer.txt'")
    with open('samples_data_buffer.txt', 'w') as f:
        for sample in data:
            f.write(f"{sample}\n")

if plot_en != 0:
    t = np.arange(len(data)) / original_sample_rate
    plt.figure()
    plt.plot(t, data)
    plt.title("Captured AD7984 Samples (Raw)")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.show()

my_ad7984.rx_destroy_buffer()
print("The samples are in the pyadi-iio/samples_data_buffer.txt file!")
