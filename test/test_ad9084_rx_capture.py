import os
import struct
import subprocess
import shutil

import iio
import numpy as np
import pytest

hardware = ["adsy1100"]
uri = "ip:10.44.3.116"

n = 5
m = 4

@pytest.mark.iio_hardware(hardware)
def test_ad9084_rx_capture():
    os.makedirs("sample_rx_capture", exist_ok=True)

    ctx = iio.Context(uri)
    rx_dev = ctx.find_device("axi-ad9084-rx-hpc")
    fsrc_dev = ctx.find_device("axi_fsrc")

    for i in range(4):
        ch = rx_dev.find_channel(f"voltage{i}_i")
        ch.attrs["main_nco_frequency"].value = "1000000000"
        ch.attrs["channel_nco_frequency"].value = "150000000"

    ratio_results = []

    mask = iio.ChannelsMask(rx_dev)
    # Enable all channels, some are not yet considered supported.
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

    fsrc_ch = fsrc_dev.find_channel("altvoltage0", True)

    rx_dev.debug_attrs['fsrc_configure_rx'].value = f"{n} {m}"
    rx_dev.debug_attrs['fsrc_configure_tx'].value = f"{n} {m}"
    rx_dev.debug_attrs['fsrc_rx_reconfig_spi'].value = "1"
    rx_dev.debug_attrs['fsrc_tx_reconfig_spi'].value = "1"

    for rx_state in [1, 0]:
        fsrc_ch.attrs["rx_enable"].value = str(rx_state)
        rx_state_str = "rx_on" if rx_state == 1 else "rx_off"

        for r in range(0, 4):
            block = next(stream)
        i_data = mask.channels[0].read(block)
        q_data = mask.channels[1].read(block)

        i_samples = np.frombuffer(i_data, dtype="i2")
        q_samples = np.frombuffer(q_data, dtype="i2")

        data = bytearray()
        for i, q in zip(i_samples, q_samples):
            data.extend(struct.pack("<h", i))
            data.extend(struct.pack("<h", q))

        output_file = f"sample_rx_capture/sample_{n}_{m}_{rx_state_str}.dat"
        with open(output_file, "wb") as f:
            f.write(data)

        gnuplot = shutil.which("gnuplot")
        if gnuplot:
            svg_file = f"sample_rx_capture/sample_{n}_{m}_{rx_state_str}.svg"
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
    print(result)

    ratio_file = "sample_rx_capture/sample_ratio.txt"
    with open(ratio_file, "w") as f:
        f.write(result + "\n")

    assert abs(ratio_exp - ratio_pra) < 0.05, "ratios are too distant!"
