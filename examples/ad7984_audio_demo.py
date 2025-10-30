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
import time
import numpy as np
from scipy import signal
import sounddevice as sd
import datetime

try:
    from scipy.io import wavfile
    wav_available = True
except ImportError:
    wav_available = False

# Parse arguments
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
spi_type = sys.argv[2] if len(sys.argv) >= 3 else "engine"
duration = float(sys.argv[3]) if len(sys.argv) >= 4 else 2.0
play_audio = len(sys.argv) < 5 or sys.argv[4].lower() != "noplay"

def setup_device(uri, spi_type, duration):
    if spi_type.lower() in ["classic", "clasic"]:
        device_name = "spi_clasic_ad7984"
        sample_rate = 15_000
        total_samples = int(sample_rate * duration)

        # Classic SPI limitation: max 15,000 samples per chunk
        max_samples_per_chunk = 15_000

        if total_samples <= max_samples_per_chunk:
            buffer_size = total_samples
            num_chunks = 1
        else:
            buffer_size = max_samples_per_chunk
            num_chunks = (total_samples + buffer_size - 1) // buffer_size  # Ceiling division
    else:
        device_name = "spi_engine_ad7984"
        sample_rate = 1_333_000
        total_samples = int(sample_rate * duration)

        # SPI engine can handle larger chunks
        max_samples_per_chunk = 2_000_000

        if total_samples <= max_samples_per_chunk:
            buffer_size = total_samples
            num_chunks = 1
        else:
            buffer_size = max_samples_per_chunk
            num_chunks = (total_samples + buffer_size - 1) // buffer_size  # Ceiling division

    device = adi.ad7689(uri=uri, device_name=device_name)
    device.rx_enabled_channels = [0]
    device.rx_buffer_size = buffer_size

    print(f"Status: Setting up {device_name}")
    print(f"Status: Duration = {duration}s, Sample rate = {sample_rate:,} Hz")
    print(f"Status: Total samples needed = {total_samples:,}")
    print(f"Status: Buffer size = {buffer_size:,}, Chunks = {num_chunks}")

    return device, device_name, num_chunks, sample_rate, total_samples

def capture_audio_chunk(device, device_name, num_chunks, total_samples):
    all_data = []

    if device_name == "spi_engine_ad7984":
        print("Status: Starting SPI engine capture...")
        for i in range(num_chunks):
            print(f"Status: Capturing chunk {i+1}/{num_chunks}")
            chunk = device.rx()
            all_data.extend(chunk)

            # Stop if we have enough samples
            if len(all_data) >= total_samples:
                all_data = all_data[:total_samples]
                break
        elapsed_time = None
    else:
        print("Status: Starting classic SPI capture...")
        start_time = time.perf_counter()
        for i in range(num_chunks):
            print(f"Status: Capturing chunk {i+1}/{num_chunks}")
            chunk = device.rx()
            all_data.extend(chunk)

            # Stop if we have enough samples
            if len(all_data) >= total_samples:
                all_data = all_data[:total_samples]
                break
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

    print(f"Status: Captured {len(all_data):,} samples (target: {total_samples:,})")
    return np.array(all_data, dtype=float), elapsed_time

def process_audio(data, original_sample_rate, target_sample_rate=47984):
    print("Status: Processing audio...")
    data = data - np.mean(data)

    gcd = np.gcd(original_sample_rate, target_sample_rate)
    up = target_sample_rate // gcd
    down = original_sample_rate // gcd
    resampled = signal.resample_poly(data, up, down)

    if np.max(np.abs(resampled)) == 0:
        resampled = np.zeros_like(resampled)
    else:
        resampled = resampled / np.max(np.abs(resampled))

    print(f"Status: Resampled from {original_sample_rate:,} Hz to {target_sample_rate:,} Hz")
    return (resampled * 32767).astype(np.int16)

def save_wav_file(audio_data, sample_rate, spi_type):
    """Save audio data to WAV file with timestamp and SPI type in filename."""
    if not wav_available:
        print("Status: WAV saving not available - scipy not found")
        return None

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ad7984_{spi_type}_{timestamp}.wav"

    try:
        wavfile.write(filename, sample_rate, audio_data)
        print(f"Status: Audio saved to {filename}")
        return filename
    except Exception as e:
        print(f"Status: Error saving WAV file: {e}")
        return None

# Setup
print("Status: Initializing AD7984 Audio Script")
print(f"Status: URI = {my_uri}, SPI = {spi_type}, Duration = {duration}s")
print(f"Status: Audio playback = {'enabled' if play_audio else 'disabled'}")

device, device_name, num_chunks, original_sample_rate, total_samples = setup_device(my_uri, spi_type, duration)
target_sample_rate = 47984

# Single capture and play
data, elapsed_time = capture_audio_chunk(device, device_name, num_chunks, total_samples)

if original_sample_rate is None and elapsed_time:
    actual_sample_rate = int(len(data) / elapsed_time)
    print(f"Status: Calculated sample rate = {actual_sample_rate:,} Hz")
else:
    actual_sample_rate = original_sample_rate

audio_data = process_audio(data, actual_sample_rate, target_sample_rate)

# Save to WAV file
save_wav_file(audio_data, target_sample_rate, spi_type)

if play_audio:
    print(f"Status: Playing audio ({len(audio_data):,} samples at {target_sample_rate:,} Hz)")
    sd.play(audio_data, samplerate=target_sample_rate, blocking=True)
    print("Status: Playback complete")
else:
    print("Status: Audio playback skipped (noplay mode)")

print("Status: Stopping...")
sd.stop()
device.rx_destroy_buffer()
print("Status: Cleanup complete")