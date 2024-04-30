"""Sweep Pluto LO and measure RX power"""

import time
from bench.hittite import HMCT2220
import adi
import pytest
import numpy as np
import test.rf.spec as spec
import json

hardware = ["pluto", "pluto_rev_c"]
classname = "adi.Pluto"


@pytest.mark.iio_hardware(hardware)
def test_pluto_instrument(iio_uri):

    # Test params
    frequency_range = range(325000000, 3800000000, 1000000)
    dwell_time_seconds = 2
    frames_to_avg = 4
    samples_per_frame = 2**14
    siggen_power = -10

    # Set up Pluto
    sdr = adi.Pluto(iio_uri)
    sdr.dds_single_tone(10000, 0)
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_hardwaregain_chan0 = 0
    sdr.rx_buffer_size = samples_per_frame
    sdr._rxadc.set_kernel_buffers_count(1)
    sdr.rx_enabled_channels = [0]

    # Setup siggen
    siggen = HMCT2220()
    siggen.output_enabled = False
    siggen.output_power = siggen_power

    print("Enabling Siggen")
    time.sleep(4)
    siggen.output_enabled = True

    # Get component for RSSI
    voltage0 = sdr._ctrl.find_channel("voltage0", False)

    # Sweep
    results = {}
    for freq in frequency_range:
        sdr.rx_lo = freq
        siggen.frequency = freq / 1000000
        time.sleep(dwell_time_seconds)
        # Flush buffers
        for _ in range(2):
            sdr.rx()

        # Measure power
        powers = []
        sfdrs = []
        rssis = []
        for i in range(frames_to_avg):
            data = sdr.rx()

            power = 10 * np.log10(np.mean(np.abs(data) ** 2))
            sfdr, amp, freqs = spec.sfdr(data, plot=False)

            rssi = voltage0.attrs["rssi"].value
            if isinstance(rssi,str) and "dB" in rssi:
                rssi = rssi.replace("dB","").strip()
            rssi = float(rssi)

            powers.append(power)
            sfdrs.append(sfdr)
            rssis.append(rssi)

            print(f"{i} | Freq: {freq}, Power: {power}, SFDR: {sfdr}, RSSI: {rssi}")

            time.sleep(dwell_time_seconds)


        results[freq] = {
            "power": np.mean(powers),
            "power_std": np.std(powers),
            "sfdr": np.mean(sfdrs),
            "sfdr_std": np.std(sfdrs),
            "rssi": np.mean(rssis),
            "rssi_std": np.std(rssis),
        }

        # Save results
        with open("pluto_results.json", "w") as f:
            json.dump(results, f, indent=4)