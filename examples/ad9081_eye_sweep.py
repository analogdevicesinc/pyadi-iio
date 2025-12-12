#!/usr/bin/env python3
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""AD9081 JESD Eye Diagram Sweep

Sweeps CTLE filter values (0-4) and boost mask (on/off) combinations,
captures eye diagrams, calculates eye openings, and saves results.
"""

import csv
import os
import time
from datetime import datetime

import adi
import matplotlib.pyplot as plt
import numpy as np

# Configuration
URI = "ip:10.44.3.71"
FSM_POLL_INTERVAL = 0.5  # seconds
FSM_TIMEOUT = 30  # seconds
CTLE_VALUES = range(1, 5)  # 1-4
BOOST_VALUES = [0x00, 0xFF]  # Off, On (all lanes)
NUM_LANES = 8
NUM_CAPTURES = 3  # Number of captures per configuration for averaging
OUTPUT_DIR = "eye_sweep_results"


def set_ctle_filter(dev, ctle_value):
    """Set CTLE filter value for all lanes."""
    for lane in range(NUM_LANES):
        dev._ctrl.debug_attrs[f"adi,jrx-ctle-filter-lane{lane}"].value = str(ctle_value)


def set_boost_mask(dev, boost_mask):
    """Set lane boost mask."""
    dev._ctrl.debug_attrs["adi,jrx-lane-boost-mask"].value = str(boost_mask)


def apply_settings(dev):
    """Apply CTLE/boost settings by power cycling and waiting for FSM.

    Toggles powerdown to apply the new settings, then polls the JESD FSM
    state until it returns to opt_post_running_stage.

    Returns:
        dict: JRX status information
    """
    # Power cycle to apply settings
    dev._set_iio_dev_attr_str("powerdown", "1")
    time.sleep(0.1)
    dev._set_iio_dev_attr_str("powerdown", "0")
    time.sleep(2)
    # Wait for FSM to return to running state
    start_time = time.time()
    while True:
        fsm_state = dev._get_iio_dev_attr_str("jesd204_fsm_state")
        if fsm_state == "opt_post_running_stage":
            break

        elapsed = time.time() - start_time
        if elapsed > FSM_TIMEOUT:
            raise TimeoutError(
                f"JESD FSM did not return to opt_post_running_stage within {FSM_TIMEOUT}s. "
                f"Current state: {fsm_state}"
            )

        time.sleep(FSM_POLL_INTERVAL)

    # Read and parse JESD status
    status = dev._get_iio_debug_attr_str("status")
    return parse_jrx_status(status)


def parse_jrx_status(status_str):
    """Parse JRX status from JESD status string.

    Args:
        status_str: Full status string from debug attribute

    Returns:
        dict: Parsed JRX status with link_status
    """
    jrx_info = {"link_status": ""}

    for line in status_str.splitlines():
        if "JESD TX (JRX)" in line:
            jrx_info["link_status"] = "good" if "Link is good" in line else "bad"
            break

    return jrx_info


def calculate_eye_opening(x, y1, y2):
    """Calculate vertical and horizontal eye opening.

    Args:
        x: SPO values (horizontal axis)
        y1: One eye boundary (mV)
        y2: Other eye boundary (mV)

    Returns:
        tuple: (vertical_opening_mv, horizontal_opening_spo)
    """
    y1 = np.array(y1)
    y2 = np.array(y2)
    x = np.array(x)

    # Calculate the eye opening (gap) at each x point
    eye_gap = np.abs(y1 - y2)

    # Vertical opening: gap at center (x=0)
    # Find index closest to x=0
    center_idx = np.argmin(np.abs(x))
    vertical_opening = eye_gap[center_idx]

    # Horizontal opening: width of x range where eye is open
    # Eye is open where there's a positive gap (y1 != y2)
    open_indices = np.where(eye_gap > 0)[0]
    if len(open_indices) > 0:
        x_open = x[open_indices]
        horizontal_opening = np.max(x_open) - np.min(x_open)
    else:
        horizontal_opening = 0

    return vertical_opening, horizontal_opening


def save_eye_plot(all_captures, ctle, boost, output_dir):
    """Save eye diagram plot as PNG with multiple captures overlaid.

    Args:
        all_captures: List of eye_data_per_lane dicts, one per capture
        ctle: CTLE filter value
        boost: Boost mask value
        output_dir: Output directory path
    """
    fig = plt.figure(figsize=(16, 12))

    # Use first capture to get lane list and metadata
    first_capture = all_captures[0]
    num_lanes = len(first_capture.keys())
    boost_str = "ON" if boost == 0xFF else "OFF"

    # Colors for different captures
    colors_y1 = ["blue", "dodgerblue", "cyan"]
    colors_y2 = ["red", "orangered", "salmon"]

    for i, lane in enumerate(first_capture):
        ax1 = plt.subplot(int(num_lanes / 2), 2, int(i) + 1)

        # Plot each capture
        for cap_idx, eye_data in enumerate(all_captures):
            x = eye_data[lane]["x"]
            y1 = eye_data[lane]["y1"]
            y2 = eye_data[lane]["y2"]

            alpha = 0.7 if cap_idx > 0 else 1.0
            plt.scatter(
                x, y1, marker="+", color=colors_y1[cap_idx % len(colors_y1)],
                s=10, alpha=alpha, label=f"Cap {cap_idx+1}" if i == 0 else ""
            )
            plt.scatter(
                x, y2, marker="+", color=colors_y2[cap_idx % len(colors_y2)],
                s=10, alpha=alpha
            )

        plt.xlim(first_capture[lane]["graph_helpers"]["xlim"])
        plt.xlabel(first_capture[lane]["graph_helpers"]["xlabel"])
        plt.ylabel(first_capture[lane]["graph_helpers"]["ylabel"])
        plt.title(f"Lane {lane}", loc="left", fontweight="bold")
        plt.axvline(0, color="black", linewidth=0.5)
        plt.axhline(0, color="black", linewidth=0.5)
        plt.grid(True, alpha=0.3)

    fig.suptitle(
        f"JESD204 Eye Scan - CTLE={ctle}, Boost={boost_str} ({NUM_CAPTURES} captures)\n"
        f"({first_capture[list(first_capture.keys())[0]]['mode']}) "
        f"Rate {first_capture[list(first_capture.keys())[0]]['graph_helpers']['rate_gbps']} Gbps",
        fontsize=14,
        fontweight="bold",
    )

    # Add legend to first subplot
    fig.axes[0].legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    filename = f"eye_ctle{ctle}_boost{boost_str}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close(fig)
    return filepath


def print_results_table(results):
    """Pretty print results table to stdout."""
    print("\n" + "=" * 80)
    print("EYE SWEEP RESULTS")
    print("=" * 80)
    print(
        f"{'CTLE':>6} {'Boost':>8} {'Lane':>6} {'Vert (mV)':>12} {'Horiz (SPO)':>14} "
        f"{'JRX Link':>10}"
    )
    print("-" * 80)

    current_config = None
    for r in results:
        config = (r["ctle"], r["boost"])
        if config != current_config:
            if current_config is not None:
                print("-" * 80)
            current_config = config

        boost_str = "ON" if r["boost"] == 0xFF else "OFF"
        print(
            f"{r['ctle']:>6} {boost_str:>8} {r['lane']:>6} "
            f"{r['vertical_opening']:>12.2f} {r['horizontal_opening']:>14.1f} "
            f"{r['jrx_link_status']:>10}"
        )

    print("=" * 80)


def print_summary(results):
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print("SUMMARY BY CONFIGURATION")
    print("=" * 80)
    print(
        f"{'CTLE':>6} {'Boost':>8} {'Avg Vert (mV)':>14} {'Avg Horiz':>12} {'Min Vert':>12} {'Max Vert':>12}"
    )
    print("-" * 80)

    # Group by configuration
    configs = {}
    for r in results:
        key = (r["ctle"], r["boost"])
        if key not in configs:
            configs[key] = []
        configs[key].append(r)

    for (ctle, boost), data in sorted(configs.items()):
        vert_values = [d["vertical_opening"] for d in data]
        horiz_values = [d["horizontal_opening"] for d in data]
        boost_str = "ON" if boost == 0xFF else "OFF"
        print(
            f"{ctle:>6} {boost_str:>8} {np.mean(vert_values):>14.2f} "
            f"{np.mean(horiz_values):>12.1f} {np.min(vert_values):>12.2f} {np.max(vert_values):>12.2f}"
        )

    print("=" * 80)


def main():
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{OUTPUT_DIR}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Connect to device
    print(f"Connecting to {URI}...")
    dev = adi.ad9081(URI, disable_jesd_control=False)
    dev._ctx.set_timeout(90000)

    results = []
    total_configs = len(CTLE_VALUES) * len(BOOST_VALUES)
    config_num = 0

    for ctle in CTLE_VALUES:
        for boost in BOOST_VALUES:
            config_num += 1
            boost_str = "ON" if boost == 0xFF else "OFF"
            print(
                f"\n[{config_num}/{total_configs}] Testing CTLE={ctle}, Boost={boost_str}"
            )

            # Set configuration
            set_ctle_filter(dev, ctle)
            set_boost_mask(dev, boost)

            # Apply settings to hardware
            print("  Applying settings (power cycle)...")
            jrx_status = apply_settings(dev)
            print(f"  JRX Status: Link={jrx_status['link_status']}")

            # Capture eye data multiple times
            all_captures = []
            lane_measurements = {}  # lane -> list of (vert, horiz) tuples

            for cap_num in range(NUM_CAPTURES):
                print(f"  Capture {cap_num + 1}/{NUM_CAPTURES}...")
                eye_data = dev._jesd.get_eye_data()
                all_captures.append(eye_data)
                if cap_num < NUM_CAPTURES - 1:
                    time.sleep(1)  # Brief delay between captures

                # Calculate eye openings for each lane
                for lane in eye_data:
                    x = eye_data[lane]["x"]
                    y1 = eye_data[lane]["y1"]
                    y2 = eye_data[lane]["y2"]

                    vert, horiz = calculate_eye_opening(x, y1, y2)

                    if lane not in lane_measurements:
                        lane_measurements[lane] = []
                    lane_measurements[lane].append((vert, horiz))

            # Calculate averages and store results
            for lane in lane_measurements:
                measurements = lane_measurements[lane]
                avg_vert = np.mean([m[0] for m in measurements])
                avg_horiz = np.mean([m[1] for m in measurements])

                results.append(
                    {
                        "ctle": ctle,
                        "boost": boost,
                        "lane": lane,
                        "vertical_opening": avg_vert,
                        "horizontal_opening": avg_horiz,
                        "jrx_link_status": jrx_status["link_status"],
                    }
                )

                # Show individual measurements and average
                verts = [m[0] for m in measurements]
                horizs = [m[1] for m in measurements]
                print(
                    f"  Lane {lane}: Vert={avg_vert:.2f}mV (avg of {[f'{v:.1f}' for v in verts]}), "
                    f"Horiz={avg_horiz:.1f} SPO (avg of {[f'{h:.1f}' for h in horizs]})"
                )

            # Save plot with all captures overlaid
            plot_path = save_eye_plot(all_captures, ctle, boost, output_dir)
            print(f"  Saved: {plot_path}")

    # Write CSV
    csv_path = os.path.join(output_dir, "eye_sweep_results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ctle",
                "boost",
                "lane",
                "vertical_opening",
                "horizontal_opening",
                "jrx_link_status",
            ],
        )
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResults saved to: {csv_path}")

    # Print results
    print_results_table(results)
    print_summary(results)


if __name__ == "__main__":
    main()
