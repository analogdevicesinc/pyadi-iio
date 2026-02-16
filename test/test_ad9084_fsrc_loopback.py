import os
import struct
import subprocess
import shutil

import iio
import numpy as np
import pytest

hardware = ["adsy1100"]
uri = "ip:10.44.3.116"

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
def test_ad9084_fsrc_loopback():
    os.makedirs("sample", exist_ok=True)

    dac_buffer_cli = shutil.which("dac_buffer_cli")
    if dac_buffer_cli:
        subprocess.run(
            [
                dac_buffer_cli,
                "-u",
                uri,
                "-d",
                "axi-ad9084-tx-hpc",
                "-f",
                "/mnt/wsl/data/repos/iio-oscilloscope/waveforms/sinewave_0.9.mat",
            ],
            check=True,
        )
    else:
        print("dac_buffer_cli not found, skipped dmac dac buffer")

    ctx = iio.Context(uri)
    rx_dev = ctx.find_device("axi-ad9084-rx-hpc")
    fsrc_dev = ctx.find_device("axi_fsrc")

    for i in range(4):
        ch = rx_dev.find_channel(f"voltage{i}_i")
        ch.attrs["main_nco_frequency"].value = "1000000000"
        ch.attrs["channel_nco_frequency"].value = "150000000"

    rx_dev.find_channel("voltage0_i").attrs["loopback"].value = "loopback3_jesd"
    rx_dev.find_channel("voltage1_i").attrs["loopback"].value = "loopback3_jesd"
    rx_dev.find_channel("voltage2_i").attrs["loopback"].value = "loopback3_jesd"
    rx_dev.find_channel("voltage3_i").attrs["loopback"].value = "loopback3_jesd"

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
    stream = iio.Stream(buffer=buf, nb_blocks=1, samples_count=1024*4)

    block = next(stream)
    for i in range(4):
        i_data = mask.channels[i].read(block)
        q_data = mask.channels[i + 1].read(block)

    i_samples = np.frombuffer(i_data, dtype="i2")
    q_samples = np.frombuffer(q_data, dtype="i2")

    data = bytearray()
    for i, q in zip(i_samples, q_samples):
        data.extend(struct.pack("<h", i))
        data.extend(struct.pack("<h", q))

    output_file = f"sample/sample_no_fsrc.dat"
    with open(output_file, "wb") as f:
        f.write(data)

    gnuplot = shutil.which("gnuplot")
    if gnuplot:
        svg_file = f"sample/sample_no_fsrc.svg"
        plot_title = f"No FSRC"
        gnuplot_cmd = (
            f"set terminal svg size 1400,1300; "
            f"set output '{svg_file}'; "
            f"plot '{output_file}' binary format='%short%short' using 1 with dots title 'I {plot_title}', "
            f"'{output_file}' binary format='%short%short' using 2 with dots title 'Q {plot_title}'"
        )
        subprocess.run([gnuplot, "-e", gnuplot_cmd], check=False)

    else:
        print("gnuplot not found, svg skipped")

    fsrc_ch = fsrc_dev.find_channel("altvoltage0", True)
    fsrc_ch.attrs["tx_enable"].value = "1"
    fsrc_ch.attrs["tx_active"].value = "1"

    for n, m in RATIOS:
        fsrc_ch.attrs["tx_ratio_set"].value = f"{n} {m}"

        for rx_state in [1, 0]:
            fsrc_ch.attrs["rx_enable"].value = str(rx_state)
            rx_state_str = "rx_on" if rx_state == 1 else "rx_off"

            for r in range(0, 4):
                block = next(stream)
            for i in range(4):
                i_data = mask.channels[i].read(block)
                q_data = mask.channels[i + 1].read(block)

            i_samples = np.frombuffer(i_data, dtype="i2")
            q_samples = np.frombuffer(q_data, dtype="i2")

            data = bytearray()
            for i, q in zip(i_samples, q_samples):
                data.extend(struct.pack("<h", i))
                data.extend(struct.pack("<h", q))

            output_file = f"sample/sample_{n}_{m}_{rx_state_str}.dat"
            with open(output_file, "wb") as f:
                f.write(data)

            gnuplot = shutil.which("gnuplot")
            if gnuplot:
                svg_file = f"sample/sample_{n}_{m}_{rx_state_str}.svg"
                plot_title = f"N={n} M={m} ({rx_state_str})"
                gnuplot_cmd = (
                    f"set terminal svg size 1400,1300; "
                    f"set output '{svg_file}'; "
                    f"plot '{output_file}' binary format='%short%short' using 1 with dots title 'I {plot_title}', "
                    f"'{output_file}' binary format='%short%short' using 2 with dots title 'Q {plot_title}'"
                )
                subprocess.run([gnuplot, "-e", gnuplot_cmd], check=False)

            else:
                print("gnuplot not found, svg skipped")

        valid = sum(1 for s in i_samples if s != -32768) # 0x8000
        invalid = sum(1 for s in i_samples if s == -32768)
        ratio_exp = n / m
        ratio_pra = (valid + invalid) / (valid)
        result = f"ratio {n} {m} : {ratio_exp:.6f} {ratio_pra:.6f} (invalid,valid) : ({invalid},{valid})"
        ratio_results.append(result)
        print(result)

    fsrc_ch.attrs["tx_enable"].value = "0"

    ratio_file = "sample/sample_ratios.txt"
    with open(ratio_file, "w") as f:
        f.write("\n".join(ratio_results) + "\n")

    assert len(ratio_results) == len(RATIOS)
