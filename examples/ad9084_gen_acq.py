# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""AD9084 transmit and receive example.

Transmits one of three sources and plots the captured receive data in the time
domain:

  python ad9084_example.py sine.csv               waveform file from the PC
  python ad9084_example.py --dds [HZ]                  DDS in the FPGA
  python ad9084_example.py --test-tone [Hz]            test tone inside the AD9084

Add --loopback to capture through the chip's JESD204 loopback instead of the
ADC, which shows what actually reached the chip rather than what came back over
the RF path.

Add --test-tone-scale <value> to specify the test tone amplitude between 0 and 1.
Without this argument, the default scale is 0.35.

Add --lane-errors to print the FPGA link core's per-lane JESD204 receive error
counters.
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np

import adi

# Waveform file used when none is named on the command line. The format is
# picked from the file extension:
#   .npy            numpy array, complex (I + jQ) or real
#   .csv .txt       one sample per line, "I,Q" (two columns) or "I" (one column)
#   .bin .raw .iq   raw interleaved int16, I0 Q0 I1 Q1 ...
TX_SAMPLE_FILE = "examples/sine.csv"

# The transmit path only accepts buffer lengths that are a multiple of this many
# samples. A push of any other length silently does nothing at all, and whatever
# was loaded before keeps replaying out of the offload FIFO -- which looks exactly
# like the new file being ignored rather than rejected. Measured on this board:
# 32, 64, 96, 128 and 256 samples all load; 62 and 66 never do.
TX_LENGTH_MULTIPLE = 32

# Leading samples of each capture to plot. The whole RX buffer is 2**16 samples,
# 26.2 us at 2.5 GSPS, which packs far too many cycles into the width of the
# window to make out individual ones. Set to None to plot the full buffer.
PLOT_SAMPLES = 256

# Converter pairs to transmit and receive on. The index selects a side and a
# converter, per the channel labels the chip reports:
#   0 -> Side-A DAC0/ADC0    2 -> Side-B DAC0/ADC0
#   1 -> Side-A DAC1/ADC1    3 -> Side-B DAC1/ADC1
# The DAC number in those labels is the driver's own index, not the board's. On
# this board the output the driver calls DAC1 is brought out as DACA3, and DAC1 on
# side B as DACB3 -- so a channel 1 or 3 signal appears on the A3/B3 connector.
# The waveform file is sent on every one of them, and each gets its own plot.
CHANNELS_TX = [0, 1, 2, 3]
CHANNELS_RX = [0, 1, 2, 3]

# Defaults for the two on-board sources, used when their option is given without
# a frequency. The DDS frequency has to stay below half the sample rate.
DDS_FREQUENCY = 40320000
DDS_SCALE = 0.5
TEST_TONE_FREQUENCY = 30000000
# DO NOT SET TEST_TONE_SCALE above 0.35, or you will see distortions in the signal.
TEST_TONE_SCALE = 0.35

# Digital loopback inside the AD9084 selected by --loopback. It feeds transmit
# data back into the receive datapath on the chip, bypassing the DAC output, the
# cable and the ADC. loopback3_jesd is the deepest tap, straight off the JESD204
# deframer, so a capture shows exactly what the chip received from the FPGA. The
# other modes the chip offers are off, loopback0, loopback1 and loopback2.
#
# The mode latches when the receive datapath is brought up rather than when it is
# written, so --loopback reaches the captures on the *next* run of the script,
# not this one.
#
# It also only taps the first channel of each side, and the JTX sample crossbar
# (MUX3) decides which channels get to see that. On this board conv2/conv3 of each
# link point at an FDDC other than FDDC0 -- which one is set by the profile and has
# changed here already -- while the loopback data lands on FDDC0, so channels 0 and
# 2 carry data through loopback3_jesd while 1 and 3 read exactly zero, even though
# all four work over the analog path. Use --no-loopback to see channels 1 and 3,
# or ad9084_sample_xbar.py to repoint them at FDDC0 -- there is no driver knob for
# the crossbar, only direct register access.
LOOPBACK_MODE = "loopback3_jesd"
# loopback0, loopback1 and loopback2 are ADC-to-DAC, not TX-to-RX: they inject
# receive data into the transmit datapath, so a capture is the wrong place to look
# for them and comes back at noise level. Only loopback3_jesd runs TX to RX.


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file",
        nargs="?",
        help=f"waveform file to transmit, default '{TX_SAMPLE_FILE}' when no "
        "other source is selected",
    )
    parser.add_argument(
        "--dds",
        nargs="?",
        type=float,
        const=DDS_FREQUENCY,
        metavar="HZ",
        help="transmit the FPGA DDS rather than a file, optionally at HZ "
        f"(default {DDS_FREQUENCY / 1e6:g} MHz)",
    )
    parser.add_argument(
        "--test-tone",
        nargs="?",
        type=float,
        const=TEST_TONE_FREQUENCY,
        metavar="HZ",
        help="enable the fine DUC NCO test tone at HZ "
        f"(default {TEST_TONE_FREQUENCY / 1e6:g} MHz). It is generated inside "
        "the AD9084, so it needs no data from the FPGA at all",
    )
    parser.add_argument(
        "--test-tone-scale",
        type=float,
        default=TEST_TONE_SCALE,
        metavar="S",
        help=f"test tone amplitude, 0 to 1, default {TEST_TONE_SCALE}",
    )
    parser.add_argument(
        "--loopback",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=f"capture through the chip's {LOOPBACK_MODE} loopback rather than "
        "the ADC. Takes effect on the next run, see LOOPBACK_MODE",
    )

    parser.add_argument(
        "--lane-errors",
        action="store_true",
        help="print the per-lane JESD204 receive error counters, before the "
        "captures and again afterwards so the change over the run is visible",
    )

    args = parser.parse_args()

    if args.file and args.dds is not None:
        parser.error("a waveform file and --dds are two different transmit sources")

    return args


def set_rx_loopback(dev, mode):
    """Set the on-chip digital loopback on every receive channel.

    pyadi has no property for this, so the raw IIO channel attribute is written
    here. Each channel carries it on both its I and Q halves and both have to be
    written. Returns the mode read back from the chip, which is not necessarily
    the one requested.
    """
    names = dev._rx_channel_names
    available = dev._get_iio_attr_str(names[0], "loopback_available", False).split()
    if mode not in available:
        raise ValueError(f"loopback '{mode}' not supported, pick one of {available}")

    for name in names:
        dev._set_iio_attr(name, "loopback", False, mode)

    return dev._get_iio_attr_str(names[0], "loopback", False)


def print_lane_errors(dev, previous=None):
    """Print the FPGA link core's per-lane JESD204 receive error counters.

    The counters climb while the link trains and then stay put, so a large total
    is not a fault on its own -- what matters is whether they are still growing.
    Passing the return value of an earlier call as `previous` shows the change.

    The link cores are IIO "fakedev" devices, so they are found by their label
    rather than by device name. Returns the counts, keyed by lane name.
    """
    core = None
    for d in dev._ctx.devices:
        if "label" in d.attrs and d.attrs["label"].value == "axi-jesd204-rx":
            core = d
            break
    if core is None:
        print("LANE ERRORS: axi-jesd204-rx not found in this context")
        return None

    lanes = {}
    for name in core.attrs:
        if not name.endswith("_info"):
            continue
        lines = core.attrs[name].value.splitlines()
        errors = int(lines[0].split(":")[1])
        state = lines[1].split(":")[-1].strip() if len(lines) > 1 else "?"
        # "Lane Latency: 248 (min/max 64/256" -- keep the measured value only
        latency = lines[2].split(":")[1].split()[0] if len(lines) > 2 else "?"
        lanes[name[: -len("_info")]] = (errors, state, latency)

    if not lanes:
        print("LANE ERRORS: this link core exposes no per-lane counters")
        return None

    print(f"LANE ERRORS: {len(lanes)} lanes on axi-jesd204-rx")
    for name in sorted(lanes, key=lambda k: int(k[len("lane") :])):
        errors, state, latency = lanes[name]
        delta = ""
        if previous and name in previous:
            delta = f"  {errors - previous[name][0]:+d} since the last read"
        print(
            f"   {name:7s} errors={errors:<10d} {state:10s} latency={latency}{delta}"
        )
    print(f"   total {sum(v[0] for v in lanes.values())} errors over all lanes")
    return lanes


def set_dds_tone(dev, frequency, scale, channels):
    """Drive the same DDS tone on several transmit channels.

    dds_single_tone() zeroes every other DDS each time it is called, so calling it
    per channel leaves the tone on the last one only. The DDS channels are
    addressed here by label instead: TX<n>_I_F1 and TX<n>_Q_F1 are the quadrature
    pair for channel n-1, and the 90 degree split between them is the convention
    dds_single_tone() itself uses.
    """
    dev.disable_dds()
    for c in channels:
        for half, phase in (("I", 90000), ("Q", 0)):
            name = f"TX{c + 1}_{half}_F1"
            ch = dev._txdac.find_channel(name, True)
            if ch is None:
                raise RuntimeError(f"DDS channel {name} not found")
            ch.attrs["frequency"].value = str(int(frequency))
            ch.attrs["phase"].value = str(phase)
            ch.attrs["scale"].value = str(scale)
            ch.attrs["raw"].value = "1"


def load_samples(path):
    """Load transmit samples from a file on the PC.

    Returns (samples) where samples is a 1-D complex array.
    Real-only input comes back with Q = 0. Integer input is unambiguously in DAC
    counts.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".npy":
        data = np.load(path)
    elif ext in (".csv", ".txt"):
        cols = np.loadtxt(path, delimiter="," if ext == ".csv" else None, ndmin=2)
        data = cols[:, 0] if cols.shape[1] == 1 else cols[:, 0] + 1j * cols[:, 1]
    elif ext in (".bin", ".raw", ".iq"):
        interleaved = np.fromfile(path, dtype=np.int16)
        if interleaved.size % 2:
            raise ValueError(
                f"{path}: odd number of int16 values, expected interleaved I/Q pairs"
            )
        data = interleaved[0::2] + 1j * interleaved[1::2]
    else:
        raise ValueError(f"{path}: unsupported extension '{ext}'")

    data = np.asarray(data).ravel()
    if data.size == 0:
        raise ValueError(f"{path}: file contains no samples")

    if data.size % TX_LENGTH_MULTIPLE:
        usable = (data.size // TX_LENGTH_MULTIPLE + 1) * TX_LENGTH_MULTIPLE
        raise ValueError(
            f"{path}: {data.size} samples is not a multiple of "
            f"{TX_LENGTH_MULTIPLE}, so the transmit path would ignore it and keep "
            f"replaying the previous waveform. Use {usable} samples, or another "
            f"multiple of {TX_LENGTH_MULTIPLE}."
        )

    return data.astype(np.complex128)


# --------------------------------
# 0. Main script begins here
# --------------------------------
args = parse_args()

# --------------------------------
# 1. Initial set-up
# --------------------------------
dev = adi.ad9084("ip:10.48.65.177")

print("CHIP Version:", dev.chip_version)
print("API  Version:", dev.api_version)

print("TX SYNC START AVAILABLE:", dev.tx_sync_start_available)
print("RX SYNC START AVAILABLE:", dev.rx_sync_start_available)

# Configure properties
print("--Setting up chip")

# Set NCOs
dev.rx_channel_nco_frequencies = [0] * 4
dev.tx_channel_nco_frequencies = [0] * 4

dev.rx_main_nco_frequencies = [2000000000] * 4
dev.tx_main_nco_frequencies = [2000000000] * 4

dev.rx_enabled_channels = CHANNELS_RX
dev.tx_enabled_channels = CHANNELS_TX
dev.rx_nyquist_zone = ["odd"] * 4

print("RX LOOPBACK:", set_rx_loopback(dev, LOOPBACK_MODE if args.loopback else "off"))

lanes_before = print_lane_errors(dev) if args.lane_errors else None

# Both of these persist on the chip across runs, so they are written either way
# rather than only when requested. Leaving them alone would let a setting from an
# earlier run bleed into this capture.
if args.test_tone is not None:
    dev.tx_channel_nco_frequencies = [int(args.test_tone)] * 4
    dev.tx_channel_nco_test_tone_scales = [args.test_tone_scale] * 4
    dev.tx_channel_nco_test_tone_en = [1] * 4
    print(f"TEST TONE: {args.test_tone / 1e6:g} MHz at scale {args.test_tone_scale}")
else:
    dev.tx_channel_nco_test_tone_en = [0] * 4

dev.rx_buffer_size = 2 ** 16
dev.tx_cyclic_buffer = True

fs = int(dev.tx_sample_rate)

# --------------------------------
# 2. TX Generation
# --------------------------------
# Pick the transmit source. The cyclic buffer repeats the file contents
# continuously, so the file holds one period of whatever should go out. The TX
# buffer length is fixed by the file length once pushed, so tx_destroy_buffer()
# is required before pushing a different length.
if args.dds is not None:
    set_dds_tone(dev, args.dds, DDS_SCALE, CHANNELS_TX)
    source = f"FPGA DDS, {args.dds / 1e6:g} MHz"
elif args.file is None and args.test_tone is not None:
    # The chip generates the signal on its own, so the FPGA sends nothing.
    source = f"on-chip test tone, {args.test_tone / 1e6:g} MHz"
else:
    tx_sample_file = args.file or TX_SAMPLE_FILE

    if not os.path.isfile(tx_sample_file):
        raise SystemExit(
            f"Sample file '{tx_sample_file}' not found. Pass one as an argument, "
            "use --dds or --test-tone instead, or create a test waveform with:\n"
            '  python -c "import numpy as np; n = 1024; '
            "np.save('tx_samples.npy', np.exp(2j * np.pi * 8 * np.arange(n) / n))\""
        )

    samples = load_samples(tx_sample_file)
    print(f"Loaded {samples.size} samples from {tx_sample_file}")
    print(
        f"TX buffer duration: {samples.size / fs * 1e6:.3f} us at {fs / 1e6:.1f} MSPS"
    )

    # One array per enabled channel; tx() only accepts a bare array for a single
    # channel. Every channel sends the same waveform.
    dev.tx(samples if len(CHANNELS_TX) == 1 else [samples] * len(CHANNELS_TX))
    source = f"{os.path.basename(tx_sample_file)}, {samples.size} samples"

if args.loopback:
    source += f" via {LOOPBACK_MODE}"

# --------------------------------
# 3. Retrieve RX Data & Draw Plots
# --------------------------------
# Collect data.plt.pause() already yields to the GUI event loop, so there is no
# sleep here -- every extra millisecond between refills is time for the receive
# DMA to run ahead of the host.
ncols = 2 if len(CHANNELS_RX) > 1 else 1
nrows = -(-len(CHANNELS_RX) // ncols)
fig, axes = plt.subplots(nrows, ncols, figsize=(11, 7), squeeze=False)
axes = axes.ravel()
for spare in axes[len(CHANNELS_RX) :]:
    spare.set_visible(False)

try:
    # 10 consecutive data captures
    for r in range(10):
        # rx() returns a list of arrays once more than one channel is enabled,
        # and a bare array for a single channel.
        captures = dev.rx()
        if not isinstance(captures, list):
            captures = [captures]

        for ax, channel, x in zip(axes, CHANNELS_RX, captures):
            n = x.size if PLOT_SAMPLES is None else min(PLOT_SAMPLES, x.size)
            t = np.arange(n) / fs * 1e6

            ax.clear()
            ax.plot(t, np.real(x[:n]), label="I")
            ax.plot(t, np.imag(x[:n]), label="Q")
            ax.set_title(f"channel {channel}", fontsize=9)
            ax.set_xlabel("time [us]")
            ax.set_ylabel("amplitude [LSB]")
            ax.grid(True)

        axes[0].legend(loc="upper right", fontsize=8)
        fig.suptitle(source)
        fig.tight_layout()
        plt.draw()
        plt.pause(0.15)

    plt.show()
finally:
    # Release both buffers. Without this the DAC keeps replaying the waveform
    # after the script exits and the receive DMA stays running, which is what
    # leaves buffer allocation broken until the board is power cycled. In a
    # finally block so a Ctrl+C out of the plot window cleans up too.
    dev.tx_destroy_buffer()
    dev.rx_destroy_buffer()
    dev.disable_dds()
    dev.tx_channel_nco_test_tone_en = [0] * 4

# A second read shows whether the link accumulated errors during the captures,
# which is the part that actually indicates trouble.
if args.lane_errors:
    print_lane_errors(dev, lanes_before)
