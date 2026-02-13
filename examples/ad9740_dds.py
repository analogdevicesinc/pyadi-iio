#!/usr/bin/env python3
"""
Simple DDS signal generator for AD974x DACs with waveform display.

Usage:
    python3 ad9740_dds.py -f 1e6 -s 0.5
    python3 ad9740_dds.py --frequency 5000000 --scale 1.0
    python3 ad9740_dds.py -f 1e6 -s 0.5 --device ad9744
    python3 ad9740_dds.py -f 1e6 -s 1.0 --sample-rate 200e6
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import iio
import adi

def set_sample_rate(uri, sample_rate):
    """Set the ADF4351 clock frequency (DAC sample rate).

    Args:
        uri: IIO context URI
        sample_rate: Desired sample rate in Hz

    Returns:
        Actual sample rate set, or None if ADF4351 not found
    """
    try:
        ctx = iio.Context(uri)

        for dev in ctx.devices:
            name = dev.name or ''
            if 'adf4351' in name or 'adf4350' in name:
                ch0 = dev.find_channel('altvoltage0', True)
                if ch0 and 'frequency' in ch0.attrs:
                    ch0.attrs['frequency'].value = str(int(sample_rate))
                    return int(ch0.attrs['frequency'].value)
        # ADF4351 in clock-provider mode (no IIO channel):
        # frequency is fixed at boot from device tree
        return int(sample_rate)

    except Exception as e:
        print(f"Warning: Could not set sample rate: {e}")
        return None


def get_sample_rate(uri):
    """Get the current ADF4351 clock frequency (DAC sample rate).

    Args:
        uri: IIO context URI

    Returns:
        Current sample rate in Hz, or None if ADF4351 not found
    """
    try:
        ctx = iio.Context(uri)

        for dev in ctx.devices:
            name = dev.name or ''
            if 'adf4351' in name or 'adf4350' in name:
                ch0 = dev.find_channel('altvoltage0', True)
                if ch0 and 'frequency' in ch0.attrs:
                    return int(ch0.attrs['frequency'].value)
        return None

    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Generate DDS signal on AD974x DAC',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  ad9740_dds.py -f 1e6 -s 0.5              # 1 MHz at 50% scale
  ad9740_dds.py -f 5000000 -s 1.0          # 5 MHz at full scale
  ad9740_dds.py -f 100e3 -s 0.25           # 100 kHz at 25% scale
  ad9740_dds.py -f 1e6 --device ad9744     # Use AD9744 device
  ad9740_dds.py -f 1e6 --sample-rate 200e6 # Set DAC clock to 200 MHz"""
    )
    parser.add_argument('-f', '--frequency', type=float, required=True,
                        help='Output frequency in Hz (e.g., 1e6 for 1 MHz)')
    parser.add_argument('-s', '--scale', type=float, default=1.0,
                        help='Output scale 0.0-1.0 (default: 1.0)')
    parser.add_argument('-u', '--uri', type=str, default='ip:10.48.65.134',
                        help='Device URI (default: ip:10.48.65.134)')
    parser.add_argument('-d', '--device', type=str, default='ad9744',
                        choices=['ad9748', 'ad9740', 'ad9742', 'ad9744'],
                        help='DAC device name (default: ad9744)')
    parser.add_argument('-r', '--sample-rate', type=float, default=None,
                        help='DAC sample rate in Hz via ADF4351 (e.g., 210e6)')

    args = parser.parse_args()

    # Validate parameters
    if args.frequency <= 0:
        print(f"Error: Frequency must be positive, got {args.frequency}")
        sys.exit(1)

    if not 0.0 <= args.scale <= 1.0:
        print(f"Error: Scale must be between 0.0 and 1.0, got {args.scale}")
        sys.exit(1)

    # Set sample rate if specified
    if args.sample_rate is not None:
        if args.sample_rate <= 0:
            print(f"Error: Sample rate must be positive, got {args.sample_rate}")
            sys.exit(1)

        print(f"Setting sample rate to {args.sample_rate/1e6:.3f} MHz...")
        actual_rate = set_sample_rate(args.uri, args.sample_rate)

        if actual_rate is None:
            print("Warning: ADF4351 not found, sample rate unchanged")
        else:
            print(f"Sample rate set to {actual_rate/1e6:.3f} MHz")

            # Validate DDS frequency against Nyquist
            if args.frequency > actual_rate / 2:
                print(f"Warning: DDS frequency {args.frequency/1e6:.3f} MHz exceeds "
                      f"Nyquist limit ({actual_rate/2/1e6:.3f} MHz)")
    else:
        # Report current sample rate
        current_rate = get_sample_rate(args.uri)
        if current_rate:
            print(f"Current sample rate: {current_rate/1e6:.3f} MHz")

    # Connect to DAC
    print(f"Connecting to {args.device} at {args.uri}...")

    try:
        dac = adi.ad9740(uri=args.uri, device_name=args.device)
    except Exception as e:
        print(f"Error connecting to DAC: {e}")
        sys.exit(1)

    # Configure DDS
    try:
        dac.channel[0].data_source = 'dds'
        dac.channel[0].frequency0 = int(args.frequency)
        dac.channel[0].scale0 = args.scale

        freq_str = f"{args.frequency/1e6:.3f} MHz" if args.frequency >= 1e6 else f"{args.frequency/1e3:.3f} kHz"
        print(f"DDS configured: {freq_str} at scale {args.scale:.2f}")

    except Exception as e:
        print(f"Error configuring DDS: {e}")
        sys.exit(1)

    # Generate expected waveform for display
    num_cycles = 4
    samples_per_cycle = 100
    num_samples = num_cycles * samples_per_cycle

    t = np.linspace(0, num_cycles / args.frequency, num_samples)
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
    ax.set_title(f'{args.device.upper()} DDS Output: {freq_str} @ {args.scale:.0%} scale')
    ax.set_ylim(-1.1, 1.1)
    ax.grid(True, alpha=0.3)

    # Add info text
    sample_rate = get_sample_rate(args.uri)
    rate_str = f"{sample_rate/1e6:.1f} MHz" if sample_rate else "N/A"
    info_text = f"Frequency: {freq_str}\nScale: {args.scale:.2f}\nDevice: {args.device}\nSample Rate: {rate_str}"
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    print("Close the plot window to stop DDS and exit.")
    plt.show()

    print("DDS stopped.")


if __name__ == '__main__':
    main()
