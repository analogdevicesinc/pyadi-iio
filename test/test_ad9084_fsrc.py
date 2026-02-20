import os
import struct
import subprocess
import shutil

import iio
import numpy as np
import pytest

hardware = ["adsy1100"]
uri = os.environ.get("IIO_URI", "ip:10.44.3.143")

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
]

@pytest.mark.iio_hardware(hardware)
def test_ad9084_fsrc_buffer_cli():
    """
    Only call the buffer cli to write a mat
    """
    os.makedirs("sample", exist_ok=True)

    dac_buffer_cli = shutil.which("dac_buffer_cli")
    assert dac_buffer_cli, "No dac_buffer_cli found!"

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


@pytest.mark.iio_hardware(hardware)
def test_ad9084_fsrc_loopback():
    """
    Test FPGA FSRC TX invalid (-FS) sample insertion.
    Uses the JESD loopback between TX and RX to evaluate the signal.
    The JESD loopback only supports link0.
    The Apollo FSRC is never enabled.
    """
    os.makedirs("sample", exist_ok=True)

    # Configure and enable DAC buffer output
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
    fsrc_ch = fsrc_dev.find_channel("altvoltage0", True)

    for i in range(4):
        ch = rx_dev.find_channel(f"voltage{i}_i")
        ch.attrs["main_nco_frequency"].value = "1000000000"
        ch.attrs["channel_nco_frequency"].value = "150000000"

    rx_dev.find_channel("voltage0_i").attrs["loopback"].value = "loopback3_jesd"
    rx_dev.find_channel("voltage2_i").attrs["loopback"].value = "loopback3_jesd"

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

    fsrc_ch = fsrc_dev.find_channel("altvoltage0", True)
    ratio_exp = []
    ratio_pra = []

    #import matplotlib.pyplot as plt
    for n, m in RATIOS:
        fsrc_ch.attrs["tx_ratio_set"].value = f"{n} {m}"
        fsrc_ch.attrs["tx_enable"].value = "1"
        fsrc_ch.attrs["tx_active"].value = "1"

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

            #plt.plot(channel_data[4], 's')
            #plt.show()
            # Interleave all channels [v0_i, v0_q, v1_i, v1_q, v2_i, v2_q, v3_i, v3_q]
            #                         [link0     , link1     , link0,    link1
            data = bytearray()
            for sample_idx in range(len(channel_data[0])):
                for ch_idx in range(8):
                    data.extend(struct.pack("<h", channel_data[ch_idx][sample_idx]))

            output_file = f"sample/fsrc_jesd_loopback_{n}_{m}_{rx_state_str}.dat"
            with open(output_file, "wb") as f:
                f.write(data)

            gnuplot = shutil.which("gnuplot")
            if gnuplot:
                # plot voltage{_ch}
                for _ch in [0, 2]:
                    svg_file = f"sample/fsrc_jesd_loopback_{n}_{m}_ch{_ch}_{rx_state_str}.svg"
                    plot_title = f"N={n} M={m} ({rx_state_str})"
                    gnuplot_cmd = (
                        f"set terminal svg size 1400,1300; "
                        f"set output '{svg_file}'; "
                        f"plot '{output_file}' binary format='%short%short%short%short%short%short%short%short' using {_ch*2+1} with dots title 'v{_ch}_i {plot_title}', "
                        f"     '{output_file}' binary format='%short%short%short%short%short%short%short%short' using {_ch*2+2} with dots title 'v{_ch}_q {plot_title}'"
                    )
                    subprocess.run([gnuplot, "-e", gnuplot_cmd], check=False)

            else:
                print("gnuplot not found, svg skipped")

        # Analyze link0 channels
        channel_stats = []
        for ch in [0, 2]:
            for i in [0, 1]:
                samples = channel_data[ch * 2 + i]
                valid = sum(1 for s in samples if s != -32768)
                invalid = sum(1 for s in samples if s == -32768)
                ch_ratio = (valid + invalid) / valid if valid > 0 else float('inf')
                channel_stats.append((invalid, valid, ch_ratio))
                i_str = 'i' if not i else 'q'
                print(f"  CH{ch}_{i_str}: invalid={invalid:4d}, valid={valid:4d}, ratio={ch_ratio:.6f}")

        fsrc_ch.attrs["tx_active"].value = "0"
        fsrc_ch.attrs["tx_enable"].value = "0"

        invalid, valid, ch_ratio = channel_stats[0]
        ratio_exp.append(n / m)
        ratio_pra.append(ch_ratio)
        result = f"ratio {n} {m} : {ratio_exp[-1]:.6f} {ratio_pra[-1]:.6f} (invalid,valid) : ({invalid},{valid})"
        ratio_results.append(result)
        print(result)

    rx_dev.find_channel("voltage0_i").attrs["loopback"].value = "off"
    rx_dev.find_channel("voltage2_i").attrs["loopback"].value = "off"

    for i in range(0, len(ratio_exp)):
        assert abs(ratio_exp[i] - ratio_pra[i]) < 0.05, "ratios are too distant!"

    ratio_file = "sample/fsrc_jesd_loopback_ratios.txt"
    with open(ratio_file, "w") as f:
        f.write("\n".join(ratio_results) + "\n")

    assert len(ratio_results) == len(RATIOS)


@pytest.mark.iio_hardware(hardware)
def test_ad9084_fsrc_rx_capture():
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
        rx_dev.debug_attrs['fsrc_rx_configure'].value = f"{n} {m}"
        rx_dev.debug_attrs['fsrc_rx_reconfig'].value = "1"

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

            # Interleave all channels [v0_i, v0_q, v1_i, v1_q, v2_i, v2_q, v3_i, v3_q]
            data = bytearray()
            for sample_idx in range(len(channel_data[0])):
                for ch_idx in range(8):
                    data.extend(struct.pack("<h", channel_data[ch_idx][sample_idx]))

            output_file = f"sample/fsrc_rx_capture_{n}_{m}_{rx_state_str}.dat"
            with open(output_file, "wb") as f:
                f.write(data)

            gnuplot = shutil.which("gnuplot")
            if gnuplot:
                svg_file = f"sample/fsrc_rx_capture_{n}_{m}_{rx_state_str}.svg"
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

        invalid, valid, ch_ratio = channel_stats[0]
        ratio_exp.append(n / m)
        ratio_pra.append(ch_ratio)
        result = f"ratio {n} {m} : {ratio_exp[-1]:.6f} {ratio_pra[-1]:.6f} (invalid,valid) : ({invalid},{valid})"
        ratio_results.append(result)
        print(result)

    for i in range(0, len(ratio_exp)):
        assert abs(ratio_exp[i] - ratio_pra[i]) < 0.05, "ratios are too distant!"

    ratio_file = "sample/fsrc_rx_capture_ratios.txt"
    with open(ratio_file, "w") as f:
        f.write("\n".join(ratio_results) + "\n")

    assert len(ratio_results) == len(RATIOS)


@pytest.mark.iio_hardware(hardware)
def test_ad9084_fsrc_tx_capture():
    """
    Test FSRC invalid (-FS) sample removal.
    Create a physical loopback between TX and RX, or use a oscilloscope,
    to evaluate the signal.
    """
    os.makedirs("sample", exist_ok=True)

    # Configure and enable DAC buffer output
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
    fsrc_ch = fsrc_dev.find_channel("altvoltage0", True)

    for i in range(4):
        ch = rx_dev.find_channel(f"voltage{i}_i")
        ch.attrs["main_nco_frequency"].value = "1000000000"
        ch.attrs["channel_nco_frequency"].value = "150000000"

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

    for n, m in RATIOS:
        rx_dev.debug_attrs['fsrc_tx_configure'].value = f"{n} {m}"
        rx_dev.debug_attrs['fsrc_tx_reconfig'].value = "1"

        for tx_state in [1]:

            tx_state_str = "tx_on"

            # Flush stale blocks
            for _ in range(4):
                block = next(stream)

            # Read voltage0-3 I/Q
            channel_data = []
            for ch_idx in range(8):
                raw_data = mask.channels[ch_idx].read(block)
                samples = np.frombuffer(raw_data, dtype="i2")
                channel_data.append(samples)

            # Interleave all channels [v0_i, v0_q, v1_i, v1_q, v2_i, v2_q, v3_i, v3_q]
            data = bytearray()
            for sample_idx in range(len(channel_data[0])):
                for ch_idx in range(8):
                    data.extend(struct.pack("<h", channel_data[ch_idx][sample_idx]))

            output_file = f"sample/fsrc_tx_capture_{n}_{m}_{tx_state_str}.dat"
            with open(output_file, "wb") as f:
                f.write(data)

            gnuplot = shutil.which("gnuplot")
            if gnuplot:
                svg_file = f"sample/fsrc_tx_capture_{n}_{m}_{tx_state_str}.svg"
                plot_title = f"N={n} M={m} ({tx_state_str})"
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

