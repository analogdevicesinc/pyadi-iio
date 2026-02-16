import os
import struct
import subprocess
import shutil

import iio
import numpy as np
import pytest

hardware = ["adsy1100"]
uri = "ip:10.44.3.121"

RATIOS = [
    (2000, 1010),
    (2000, 1100),
    (2000, 1200),
    (2000, 1300),
    (2000, 1400),
    (2000, 1500),
    (2000, 1600),
    (2000, 1700),
    (2000, 1800),
    (2000, 1900),
    (2000, 1990),
    (1562, 1228),
]

@pytest.mark.iio_hardware(hardware)
def test_ad9084_rx_capture():
    """
    Test FSRC invalid (-FS) sample insertion.
    Quantifies amount of -FS samples. Does not assert the distribution.
    """
    os.makedirs("sample", exist_ok=True)

    ctx = iio.Context(uri)
    rx_dev = ctx.find_device("axi-ad9084-rx-hpc")
    fsrc_dev = ctx.find_device("axi_fsrc")
    fsrc_ch = fsrc_dev.find_channel("altvoltage0", True)

    for i in range(4):
        ch = rx_dev.find_channel(f"voltage{i}_i")
        ch.attrs["main_nco_frequency"].value = "1000000000"
        ch.attrs["channel_nco_frequency"].value = "150000000"

    ratio_results = []

    mask = iio.ChannelsMask(rx_dev)
    mask.channels = [
        rx_dev.find_channel("voltage0_i"),
        rx_dev.find_channel("voltage0_q"),
        rx_dev.find_channel("voltage1_i"),
        rx_dev.find_channel("voltage1_q"),
        rx_dev.find_channel("voltage2_i"),
        rx_dev.find_channel("voltage2_q"),
        rx_dev.find_channel("voltage3_i"),
        rx_dev.find_channel("voltage3_q"),
    ]
    buf = iio.Buffer(rx_dev, mask)
    stream = iio.Stream(buffer=buf, nb_blocks=1, samples_count=1024)

    ratio_exp = []
    ratio_pra = []

    for n, m in RATIOS:
        rx_dev.debug_attrs['fsrc_configure_rx'].value = f"{n} {m}"
        rx_dev.debug_attrs['fsrc_rx_reconfig_spi'].value = "1"

        for rx_state in [1, 0]:
            fsrc_ch.attrs["rx_enable"].value = str(rx_state)
            rx_state_str = "rx_on" if rx_state == 1 else "rx_off"

            # Flush stale blocks
            for _ in range(4):
                block = next(stream)

            # Read voltage0-3 I/Q
            channel_data = []
            for ch_idx in range(8):
                raw_data = mask.channels[ch_idx].read(block)
                samples = np.frombuffer(raw_data, dtype="i2")
                channel_data.append(samples)

            # Interleave all channels [v0_i, v0_q, v1_i, v1_q, v2_i, v2_q, v3_i, v3_q, ...]
            data = bytearray()
            for sample_idx in range(len(channel_data[0])):
                for ch_idx in range(8):
                    data.extend(struct.pack("<h", channel_data[ch_idx][sample_idx]))

            output_file = f"sample/sample_{n}_{m}_{rx_state_str}.dat"
            with open(output_file, "wb") as f:
                f.write(data)

            gnuplot = shutil.which("gnuplot")
            if gnuplot:
                svg_file = f"sample/sample_{n}_{m}_{rx_state_str}.svg"
                plot_title = f"N={n} M={m} ({rx_state_str})"
                # plot voltage{_ch}
                _ch=0
                gnuplot_cmd = (
                    f"set terminal svg size 1400,1300; "
                    f"set output '{svg_file}'; "
                    f"plot '{output_file}' binary format='%short%short%short%short%short%short%short%short' using {_ch*2+1} with dots title 'v{_ch}_i {plot_title}', "
                    f"     '{output_file}' binary format='%short%short%short%short%short%short%short%short' using {_ch*2+2} with dots title 'v{_ch}_q {plot_title}'"
                )
                subprocess.run([gnuplot, "-e", gnuplot_cmd], check=False)

            else:
                print("gnuplot not found, svg skipped")

        # Analyze all 4 channels (I samples from voltage0-3)
        channel_stats = []
        for ch in range(4):
            i_samples = channel_data[ch * 2]  # I channel: 0, 2, 4, 6
            valid = sum(1 for s in i_samples if s != -32768)
            invalid = sum(1 for s in i_samples if s == -32768)
            ch_ratio = (valid + invalid) / valid if valid > 0 else float('inf')
            channel_stats.append((invalid, valid, ch_ratio))
            print(f"  CH{ch}: invalid={invalid:4d}, valid={valid:4d}, ratio={ch_ratio:.6f}")

        # Use voltage0 as representative for final assertion
        invalid, valid, ch_ratio = channel_stats[0]
        ratio_exp.append(n / m)
        ratio_pra.append(ch_ratio)
        result = f"ratio {n} {m} : {ratio_exp[-1]:.6f} {ratio_pra[-1]:.6f} (invalid,valid) : ({invalid},{valid})"
        ratio_results.append(result)
        print(result)

    for i in range(0, len(ratio_exp)):
        assert abs(ratio_exp[i] - ratio_pra[i]) < 0.05, "ratios are too distant!"

    ratio_file = "sample/sample_ratios.txt"
    with open(ratio_file, "w") as f:
        f.write("\n".join(ratio_results) + "\n")

    assert len(ratio_results) == len(RATIOS)
