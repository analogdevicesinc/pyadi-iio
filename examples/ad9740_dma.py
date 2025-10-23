#!/usr/bin/env python3
"""
Simple DMA signal generator for AD974x DACs with waveform display.

Usage:
    python3 ad9740_dma.py -f 1e6 -s 0.5
    python3 ad9740_dma.py --frequency 5000000 --scale 1.0
    python3 ad9740_dma.py -f 1e6 -s 0.5 --device ad9744
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import adi

# Device configuration
DEVICE_CONFIG = {
    'ad9748': {'bits': 8,  'shift': 8, 'sample_rate': 210e6},
    'ad9740': {'bits': 10, 'shift': 6, 'sample_rate': 210e6},
    'ad9742': {'bits': 12, 'shift': 4, 'sample_rate': 210e6},
    'ad9744': {'bits': 14, 'shift': 0, 'sample_rate': 210e6},
}

DEFAULT_BUFFER_SIZE = 4096


def check_frequency_valid(frequency, sample_rate, buffer_size):
    """
    Check if frequency results in integer number of cycles in the buffer.
    Returns (is_valid, num_cycles, samples_per_cycle, suggested_freq).
    """
    samples_per_cycle = sample_rate / frequency
    num_cycles = buffer_size / samples_per_cycle

    # Use tolerance of 1e-6 to handle floating point input precision
    is_integer_cycles = abs(num_cycles - round(num_cycles)) < 1e-6

    # Calculate suggested valid frequency
    k = round(num_cycles)
    if k < 1:
        k = 1
    suggested_freq = k * sample_rate / buffer_size

    return is_integer_cycles, num_cycles, samples_per_cycle, suggested_freq


def generate_sine_samples(frequency, scale, num_samples, device_config, sample_rate):
    """Generate sine wave samples for DMA transmission."""
    t = np.arange(num_samples) / sample_rate
    sine = np.sin(2 * np.pi * frequency * t) * scale

    dac_bits = device_config['bits']
    msb_shift = device_config['shift']

    # Use signed format (dac_datafmt handles conversion)
    dac_max = (1 << (dac_bits - 1)) - 1
    samples = (sine * dac_max).astype(np.int16)
    samples_aligned = (samples << msb_shift).astype(np.int16)

    return samples_aligned, sine


def main():
    parser = argparse.ArgumentParser(
        description='Generate DMA sine wave on AD974x DAC',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  ad9740_dma.py -f 1e6 -s 0.5          # 1 MHz at 50% scale
  ad9740_dma.py -f 5000000 -s 1.0      # 5 MHz at full scale
  ad9740_dma.py -f 100e3 -s 0.25       # 100 kHz at 25% scale
  ad9740_dma.py -f 1e6 --device ad9740 # Use AD9740 device

Valid frequencies for cyclic DMA must result in integer cycles in the buffer.
Formula: frequency = k * sample_rate / buffer_size (where k is an integer)

For 210 MHz sample rate and 4096 buffer: valid frequencies are multiples of 51.27 kHz"""
    )
    parser.add_argument('-f', '--frequency', type=float, default=1230468.75,
                        help='Output frequency in Hz (default: 1230468.75 Hz)')
    parser.add_argument('-s', '--scale', type=float, default=1.0,
                        help='Output scale 0.0-1.0 (default: 1.0)')
    parser.add_argument('-u', '--uri', type=str, default='ip:10.48.65.163',
                        help='Device URI (default: ip:10.48.65.163)')
    parser.add_argument('-d', '--device', type=str, default='ad9744',
                        choices=['ad9748', 'ad9740', 'ad9742', 'ad9744'],
                        help='DAC device name (default: ad9744)')
    parser.add_argument('-b', '--buffer-size', type=int, default=DEFAULT_BUFFER_SIZE,
                        help=f'DMA buffer size in samples (default: {DEFAULT_BUFFER_SIZE})')

    args = parser.parse_args()

    # Get device config
    config = DEVICE_CONFIG[args.device]
    sample_rate = config['sample_rate']

    # Validate parameters
    if args.frequency <= 0:
        print(f"Error: Frequency must be positive, got {args.frequency}")
        sys.exit(1)

    if not 0.0 <= args.scale <= 1.0:
        print(f"Error: Scale must be between 0.0 and 1.0, got {args.scale}")
        sys.exit(1)

    # Check if frequency is valid for cyclic DMA
    is_valid, num_cycles, samples_per_cycle, suggested_freq = check_frequency_valid(
        args.frequency, sample_rate, args.buffer_size
    )

    if not is_valid:
        print("=" * 70)
        print("ERROR: Invalid frequency for cyclic DMA buffer")
        print("=" * 70)
        print()
        print(f"  Requested frequency:    {args.frequency:.1f} Hz")
        print(f"  Sample rate:            {sample_rate:.0f} Hz")
        print(f"  Buffer size:            {args.buffer_size} samples")
        print()
        print(f"  Samples per cycle:      {samples_per_cycle:.3f} (must be integer)")
        print(f"  Cycles in buffer:       {num_cycles:.6f} (must be integer)")
        print()
        print("For cyclic DMA, the frequency must result in an INTEGER number of")
        print("cycles within the buffer to avoid phase discontinuity at wrap-around.")
        print()
        print("Valid frequencies are: f = k * sample_rate / buffer_size")
        print(f"                       f = k * {sample_rate:.0f} / {args.buffer_size}")
        print(f"                       f = k * {sample_rate/args.buffer_size:.2f} Hz")
        print()
        print(f"  Suggested frequency:    {suggested_freq:.2f} Hz ({round(num_cycles)} cycles)")
        print()

        # Show nearby valid frequencies
        k = round(num_cycles)
        print("Nearby valid frequencies:")
        for dk in range(-2, 3):
            if k + dk >= 1:
                f = (k + dk) * sample_rate / args.buffer_size
                print(f"    k={k+dk:4d}: {f:12.2f} Hz")
        print()
        print("=" * 70)
        sys.exit(1)

    # Connect to DAC
    print(f"Connecting to {args.device} at {args.uri}...")

    try:
        dac = adi.ad9740(uri=args.uri, device_name=args.device)
        dac.tx_enabled_channels = [0]
        dac.tx_cyclic_buffer = True
        dac._tx_data_type = np.dtype('<i2')  # Signed little-endian int16
    except Exception as e:
        print(f"Error connecting to DAC: {e}")
        sys.exit(1)

    # Generate samples
    samples_aligned, sine_normalized = generate_sine_samples(
        args.frequency, args.scale, args.buffer_size, config, sample_rate
    )

    freq_str = f"{args.frequency/1e6:.6f} MHz" if args.frequency >= 1e6 else f"{args.frequency/1e3:.3f} kHz"
    print(f"DMA configured: {freq_str} at scale {args.scale:.2f}")
    print(f"  Cycles in buffer: {int(round(num_cycles))}")
    print(f"  Samples per cycle: {samples_per_cycle:.1f}")

    # Send DMA data
    try:
        dac.tx(samples_aligned)
    except Exception as e:
        print(f"Error sending DMA data: {e}")
        sys.exit(1)

    # Generate time axis for display
    num_display_cycles = 4
    display_samples = int(num_display_cycles * samples_per_cycle)
    t = np.arange(display_samples) / sample_rate
    waveform = args.scale * np.sin(2 * np.pi * args.frequency * t)

    # Convert time to appropriate units for display
    if args.frequency >= 1e6:
        t_display = t * 1e6  # microseconds
        t_unit = 'us'
    elif args.frequency >= 1e3:
        t_display = t * 1e3  # milliseconds
        t_unit = 'ms'
    else:
        t_display = t
        t_unit = 's'

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(t_display, waveform, 'b-', linewidth=1.5)
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)
    ax.set_xlabel(f'Time ({t_unit})')
    ax.set_ylabel('Amplitude (normalized)')
    ax.set_title(f'{args.device.upper()} DMA Output: {freq_str} @ {args.scale:.0%} scale')
    ax.set_ylim(-1.1, 1.1)
    ax.grid(True, alpha=0.3)

    # Add info text
    info_text = (f"Frequency: {freq_str}\n"
                 f"Scale: {args.scale:.2f}\n"
                 f"Device: {args.device}\n"
                 f"Cycles: {int(round(num_cycles))}\n"
                 f"Buffer: {args.buffer_size} samples")
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    print("Close the plot window to stop DMA and exit.")
    plt.show()

    # Cleanup
    try:
        dac.tx_destroy_buffer()
    except:
        pass

    print("DMA stopped.")


if __name__ == '__main__':
    main()
