# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi
import matplotlib.pyplot as plt
import numpy as np


dev = adi.ad9081("ip:analog.local")
dev._rxadc.set_kernel_buffers_count(1)
dev._ctrl.ctx.set_timeout(1000)

# Configure properties
print("--Setting up chip")

# Set NCOs
dev.rx_channel_nco_frequencies = [0] * 4
dev.tx_channel_nco_frequencies = [0] * 4

dev.rx_main_nco_frequencies = [1000000000] * 4
dev.tx_main_nco_frequencies = [1000000000] * 4

dev.rx_enabled_channels = [0]
dev.tx_enabled_channels = [0]
dev.rx_nyquist_zone = ["odd"] * 4

dev.tx_cyclic_buffer = True
dev.tx_ddr_offload = True


ctx = dev._ctrl.ctx
tdd = ctx.find_device("axi-core-tdd")

tdd.attrs["enable"].value = "0"
tdd.attrs["startup_delay_ms"].value = "0"

chan2 = tdd.find_channel("channel2", True)
assert chan2 is not None

# Invert TDD control channel
chan2.attrs["polarity"].value = "1"
chan2.attrs["off_ms"].value = "0"
chan2.attrs["on_ms"].value = "0"
chan2.attrs["enable"].value = "1"

# TDD Offload control (FPGA side)
samples_per_frame_desired = 2**12
frame_length_ms = samples_per_frame_desired / dev.tx_sample_rate * 1000

tdd.attrs["frame_length_ms"].value = str(frame_length_ms)
for chan in ["channel0", "channel1", "channel3", "channel4"]:
    i_chan = tdd.find_channel(chan, True)
    assert i_chan is not None
    i_chan.attrs["off_ms"].value = str(frame_length_ms-0.0001)
    i_chan.attrs["on_ms"].value = "0"
    i_chan.attrs["enable"].value = "1"

# Disable TX early
chan0_tx = tdd.find_channel("channel0", True)
chan0_tx.attrs["off_ms"].value = str(frame_length_ms*0.01)

tdd.attrs["enable"].value = "1"


# Print TDD settings
print(f"Frame length: {tdd.attrs['frame_length_ms'].value} ms")
for i in range(5):
    i_chan = tdd.find_channel(f"channel{i}", True)
    print(f"Channel {i} | On: {i_chan.attrs['on_ms'].value} | Off: {i_chan.attrs['off_ms'].value}")

# Dump TDD settings
# pip install paramiko
ssh = adi.sshfs("ip:analog.local", "root", "analog")
base_addr = 0x9c460000
with open("tdd_settings.txt", "w") as f:
    for i in range(0,0x017c,4):
        stdout, stderr = ssh._run(f"busybox devmem 0x{base_addr + i:02x}")
        print(f"0x{base_addr + i:02x} (Relative {i:02x}): {stdout}")
        f.write(f"0x{base_addr + i:02x}, (Relative {i:02x}), {stdout}\n")

# Check channels
with open("tdd_channels_compare.txt", "w") as f:
    chan = 0
    for i in range(0x0080,0x017c,8):
        on, stderr = ssh._run(f"busybox devmem 0x{base_addr + i:02x}")
        off, stderr = ssh._run(f"busybox devmem 0x{base_addr + (i+4):02x}")

        on = int(on, 16)
        off = int(off, 16)

        i_chan = tdd.find_channel(f"channel{chan}", True)
        if i_chan is None:
            print(f"Channel {chan} not found, stopping check")
            break

        i_on = i_chan.attrs["on_raw"].value
        i_off = i_chan.attrs["off_raw"].value

        print(f"Channel {chan} | On: {on} | Off: {off} | i_on: {i_on} | i_off: {i_off}")

        f.write(f"Channel {chan} | On: {on} | Off: {off} | i_on: {i_on} | i_off: {i_off}\n")

        chan += 1

# Create and send data to TX DMA
fs = int(dev.tx_sample_rate)


samples_per_frame = float(tdd.attrs["frame_length_ms"].value) * fs / 1000
print(f"Samples per frame: {samples_per_frame}")

assert samples_per_frame.is_integer()

A = 0.9 * 2**14  # -6 dBFS

B = 5e6
# B = 6e5
N = int(samples_per_frame)
T = N / fs
t = np.linspace(-T / 2, T / 2, N, endpoint=False)
tx_sig = A * np.sinc(B * t)
# Use ramp
assert N < 2**15
tx_sig = [*range(N)]

# Pad with zeros
# tx_sig = np.pad(tx_sig, (0, N*2 - len(tx_sig)))


dev.tx(tx_sig)

dev.rx_buffer_size = int(samples_per_frame) * 2


for i in range(3):

    # print(f"Iteration: {i}")

    tdd.attrs["sync_soft"].value = "0"

    dev.tx_destroy_buffer()

    tdd.attrs["enable"].value = "0"

    # Clean
    try:
        data = dev.rx()
    except:
        # print("pre-refill failed as expected")
        pass

    tdd.attrs["enable"].value = "1"
    
    dev.tx(tx_sig)

    try:
        data = dev.rx()
    except:
        # print("refill failed as expected")
        pass

    tdd.attrs["sync_soft"].value = "1"

    data = dev.rx()

    if i==0:
        print("Throwing away first frame as its always random")
        continue

    # Look for peak or trough (sometimes it's inverted)
    r_data = data.real
    first_peak = np.argmin(r_data)
    # first_peak = np.argmax(r_data)
    # first_peak = np.argmax(r_data[:int(len(r_data)/2)])
    peak_value = r_data[first_peak]
    print(f"Signal start at: {first_peak} with value: {peak_value} | Iteration: {i}")

    plt.clf()
    plt.plot(data.real)
    # Add title
    plt.title(f"Frame {i}")
    plt.draw()
    plt.pause(0.5)

plt.show()




# # dev.dds_single_tone(10e6, 0.8)

# # Pull to setup rx buffer
# try:
#     data = dev.rx()
# except:
#     print("refill failed as expected")

# # Trigger TDD
# tdd.attrs["sync_soft"].value = "1"
# # for _ in range(100):
# #     tdd.attrs["sync_soft"].value = "1"
# #     time.sleep(0.1)

# # Collect data
# for i in range(10):
#     print(f"Iteration: {i}")

#     tdd.attrs["sync_soft"].value = "0"
#     x = dev.rx()

#     plt.clf()
#     plt.plot(x.real)

#     plt.draw()
#     plt.pause(0.1)

#     time.sleep(0.5)

# plt.show()
