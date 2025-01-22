"""This example demonstrates how to load a prebuilt profile or create a custom
profile for the ADRV9002 transceiver. If you have libadrv9002-iio installed,
you can create a custom profile. Otherwise, you can use a prebuilt profile that
was generated using libadrv9002-iio or TES.
"""

import argparse
import os
import time

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import adi

# Find the location of this script since the profile folder is relative to it
loc = os.path.dirname(os.path.realpath(__file__))

try:
    # Try using libadrv9002 to load profiles
    # Available at: https://analogdevicesinc.github.io/libadrv9002-iio/
    import copy

    import adrv9002 as libadrv9002

    use_prebuilt_profiles = False
except ImportError:
    print("libadrv9002 not found. Using prebuilt profiles.")
    use_prebuilt_profiles = True
    profile_folder = os.path.join(loc, "adrv9002_profiles")

# Add CLI argument for URI
parser = argparse.ArgumentParser()
parser.add_argument(
    "uri", help="URI for IIO context with ADRV9002-EVAL or AD-JUPITER-EZ"
)
args = parser.parse_args()

# Create ADRV9002 interface
uri = args.uri
sdr = adi.adrv9002(uri=uri)

# Read back radio settings
current_profile = sdr.profile
interface_mode = current_profile["SSI interface"].lower()
api_version = sdr.api_version

print("\nCurrent radio settings:")
print(f"Interface mode: {interface_mode}")
print(f"API version: {api_version}")


# Configure ADRV9002
# See here for more information on the ADRV9002 python API:
# https://analogdevicesinc.github.io/pyadi-iio/devices/adi.adrv9002.html
if use_prebuilt_profiles:
    api_version = api_version.replace(".", "_")
    rate = 40 if interface_mode == "lvds" else 5
    name = f"lte_{rate}_{interface_mode}_api_{api_version}"

    print(f"\nLoading prebuilt profile: {name}")
else:
    #  Create profile configuration
    print("\nCreating custom profile")
    rx1 = libadrv9002.rx_radio_channel_config()
    rx1.enabled = True
    rx1.adc_high_performance_mode = True
    rx1.frequency_offset_correction_enable = False
    rx1.analog_filter_power_mode = 2  # High power/performance
    rx1.analog_filter_biquad = False
    rx1.analog_filter_bandwidth_hz = 18000000
    rx1.channel_bandwidth_hz = 18000000
    rx1.sample_rate_hz = 30720000
    rx1.nco_enable = False
    rx1.nco_frequency_hz = 0
    rx1.rf_port = 0  # RX-A

    rx2 = copy.deepcopy(rx1)

    tx1 = libadrv9002.tx_radio_channel_config()
    tx1.enabled = True
    tx1.sample_rate_hz = 30720000
    tx1.frequency_offset_correction_enable = False
    tx1.analog_filter_power_mode = 2  # High power/performance
    tx1.channel_bandwidth_hz = 18000000
    tx1.orx_enabled = True
    tx1.elb_type = 2

    tx2 = copy.deepcopy(tx1)

    r_cfg = libadrv9002.radio_config()
    r_cfg.adc_rate_mode = 3  # High Performance
    r_cfg.fdd = False
    r_cfg.lvds = True
    r_cfg.ssi_lanes = 2
    r_cfg.ddr = True
    r_cfg.adc_rate_mode = 3  # High Performance
    r_cfg.short_strobe = True
    r_cfg.rx_config[0] = rx1
    r_cfg.rx_config[1] = rx2
    r_cfg.tx_config[0] = tx1
    r_cfg.tx_config[1] = tx2

    clk_cfg = libadrv9002.clock_config()
    clk_cfg.device_clock_frequency_khz = 38400
    clk_cfg.clock_pll_high_performance_enable = True
    clk_cfg.clock_pll_power_mode = 2  # High power/performance
    clk_cfg.processor_clock_divider = 1

    adrv_cfg = libadrv9002.adrv9002_config()
    adrv_cfg.clk_cfg = clk_cfg
    adrv_cfg.radio_cfg = r_cfg

    # Generate profile and stream binary
    profile, stream = libadrv9002.generate_profile(adrv_cfg)

    # Save profile and stream
    name = "custom_profile"
    profile_folder = os.path.join(loc, "adrv9002_profiles")
    if not os.path.exists(profile_folder):
        os.makedirs(profile_folder)

    with open(os.path.join(profile_folder, f"{name}.json"), "w") as f:
        f.write(str(profile))
    with open(os.path.join(profile_folder, f"{name}.stream"), "wb") as f:
        f.write(stream)

    print(f"\nProfile and stream saved to {profile_folder}")


# Load profile
sdr.write_stream_profile(
    os.path.join(profile_folder, f"{name}.stream"),
    os.path.join(profile_folder, f"{name}.json"),
)


sdr.rx_enabled_channels = [0]
sdr.rx_ensm_mode_chan0 = "rf_enabled"
sdr.rx_ensm_mode_chan1 = "rf_enabled"
sdr.tx_hardwaregain_chan0 = -20
sdr.tx_ensm_mode_chan0 = "rf_enabled"
sdr.tx_cyclic_buffer = True

sdr.rx0_lo = 1000000000
sdr.tx0_lo = 1000000000

fs = int(sdr.rx0_sample_rate)

# Set single DDS tone for TX on one transmitter
sdr.dds_single_tone(1000000, 0.9, channel=0)

# Create a sinewave waveform
# fc = 1000000
# N = 1024
# ts = 1 / float(fs)
# t = np.arange(0, N * ts, ts)
# i = np.cos(2 * np.pi * t * fc) * 2 ** 14
# q = np.sin(2 * np.pi * t * fc) * 2 ** 14
# iq = i + 1j * q
#
# # Send data
# sdr.tx(iq)

sdr.rx_buffer_size = 2 ** 18

# Collect data
for r in range(20):
    x = sdr.rx()
    f, Pxx_den = signal.periodogram(x, fs)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    # plt.ylim([1e-9, 1e2])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)
