# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
#
# Sharkbyte dual-ADC example with resolution configuration

import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

# Configuration
resolution = 14  # Options: 8, 12, or 14 bits
run_until_drift = False  # True: run until drift > 10, False: run fixed 100 iterations

my_uri = "ip:192.168.2.1" if len(sys.argv) == 1 else sys.argv[1]

print(f"Connecting to {my_uri}...")
print(f"Resolution: {resolution}-bit")

# Create SSH connection for direct register access
ssh = adi.sshfs(address=my_uri, username="root", password="analog")


# configure the offloads to work in one-shot mode

offload1_base = 0x44B00000
offload2_base = 0x44B10000
offload_reg_control = 0x88

stdout, stderr = ssh._run(
    f"busybox devmem 0x{offload1_base+offload_reg_control:08X} 32 0x2"
)
stdout, stderr = ssh._run(
    f"busybox devmem 0x{offload2_base+offload_reg_control:08X} 32 0x2"
)

# Create sharkbyte multi-ADC manager with TDD synchronization
multi = adi.sharkbyte(
    uri=my_uri,
    device1_name="hmcad15xx-adc-a",
    device2_name="hmcad15xx-adc-b",
    enable_tddn=True,
)

# Configure TDD for DMA synchronization
multi.tddn.enable = 0
multi.tddn.burst_count = 1
multi.tddn.startup_delay_ms = 0
multi.tddn.frame_length_ms = 0.1
multi.tddn.sync_internal = 1
multi.tddn.sync_external = 0

# make sure that the TDD is disable at startup and that the channels are configured to known state

for ch in multi.tddn.channel:
    ch.on_ms = 0
    ch.off_ms = 0
    ch.polarity = 0
    ch.enable = 1

# enable needs a toggle to apply the changes

multi.tddn.enable = 1
multi.tddn.enable = 0

for ch in multi.tddn.channel:
    ch.on_raw = 0
    ch.off_raw = 10
    ch.polarity = 0
    ch.enable = 1

multi.tddn.enable = 1

# Configure based on resolution
if resolution in [8, 12]:
    # Single channel mode, all inputs to IN4
    mode = "SINGLE_CHANNEL"
    num_channels = 1

    # Set input to IN4 for all channels
    for ch in multi.dev1.channel:
        ch.input_select = "IP4_IN4"
    for ch in multi.dev2.channel:
        ch.input_select = "IP4_IN4"

    multi.dev1.rx_enabled_channels = [0]
    multi.dev2.rx_enabled_channels = [0]

    print(f"Mode: {mode}")
    print(f"All inputs set to IP4_IN4")

elif resolution == 14:
    # Quad channel mode, each channel gets its own input
    mode = "QUAD_CHANNEL"
    num_channels = 4
    # Set each channel to its corresponding input
    input_map = ["IP1_IN1", "IP2_IN2", "IP3_IN3", "IP4_IN4"]
    for i, ch in enumerate(multi.dev1.channel):
        if i < len(input_map):
            ch.input_select = input_map[i]
    for i, ch in enumerate(multi.dev2.channel):
        if i < len(input_map):
            ch.input_select = input_map[i]

    multi.dev1.rx_enabled_channels = [0, 1, 2, 3]
    multi.dev2.rx_enabled_channels = [0, 1, 2, 3]

    print(f"Mode: {mode}")
    print(f"Channel inputs: {input_map}")

else:
    raise ValueError(f"Invalid resolution: {resolution}. Use 8, 12, or 14.")

# Configure the maximum buffer size based on the resolution

if resolution == 8:
    N_rx = 2 ** 16
elif resolution == 12:
    N_rx = 2 ** 15
elif resolution == 14:
    N_rx = 2 ** 13

multi.dev1.rx_buffer_size = N_rx
multi.dev2.rx_buffer_size = N_rx

# Test pattern definitions

custom_pattern = 0x7FFF
fixed_test_pattern = 0x10
ramp_pattern = 0x40
pattern_disabled = 0x00

multi.dev1.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev2.hmcad15xx_register_write(0x26, custom_pattern)
multi.dev1.hmcad15xx_register_write(0x25, pattern_disabled)
multi.dev2.hmcad15xx_register_write(0x25, pattern_disabled)

print(f"Buffer size: {N_rx} samples per channel")
print(f"Enabled channels: {num_channels}")

multi.tddn.enable = 1
data = multi.rx()

if resolution == 14:
    plt.plot(data[0][3], "o", label="ADC1 Channel 0")
    plt.plot(data[1][3], "o", label="ADC2 Channel 0")
else:
    plt.plot(data[0], "o", label="ADC1 Channel 0")
    plt.plot(data[1], "o", label="ADC2 Channel 0")
plt.tight_layout()
plt.show()

# make sure that the TDD is disable at the end of the execution and that the channels are configured to known state

multi.tddn.enable = 0
for ch in multi.tddn.channel:
    ch.on_ms = 0
    ch.off_ms = 0
    ch.polarity = 0
    ch.enable = 1


multi.tddn.enable = 1
multi.tddn.enable = 0

# Cleanup
multi.dev1.rx_destroy_buffer()
multi.dev2.rx_destroy_buffer()
