#!/usr/bin/env python3
# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Filter IIO coverage results to hardware entries relevant to new device classes
and generate a markdown report suitable for posting as a PR comment."""

import argparse
import json
import os


def load_coverage(folder, hw_name):
    """Load coverage JSON for a hardware entry. Returns None if not found."""
    path = os.path.join(folder, f"{hw_name}_coverage.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def compute_stats(data):
    """Compute coverage statistics from raw coverage JSON data."""
    dev_attrs = data.get("device_attr_reads_writes", {})
    chan_attrs = data.get("channel_attr_reads_writes", {})

    # Device attribute stats
    dev_total = 0
    dev_covered = 0
    for device in dev_attrs.values():
        for count in device.values():
            dev_total += 1
            if count > 0:
                dev_covered += 1

    # Channel attribute stats
    chan_total = 0
    chan_covered = 0
    for device in chan_attrs.values():
        for direction in device.values():
            for channel in direction.values():
                for count in channel.values():
                    chan_total += 1
                    if count > 0:
                        chan_covered += 1

    total = dev_total + chan_total
    covered = dev_covered + chan_covered

    return {
        "dev_total": dev_total,
        "dev_covered": dev_covered,
        "dev_pct": (dev_covered / dev_total * 100) if dev_total else 0,
        "chan_total": chan_total,
        "chan_covered": chan_covered,
        "chan_pct": (chan_covered / chan_total * 100) if chan_total else 0,
        "total": total,
        "covered": covered,
        "total_pct": (covered / total * 100) if total else 0,
    }


def format_untested_details(data):
    """Generate markdown details of untested attributes."""
    lines = []
    dev_attrs = data.get("device_attr_reads_writes", {})
    chan_attrs = data.get("channel_attr_reads_writes", {})

    # Untested device attributes
    for dev_name, attrs in sorted(dev_attrs.items()):
        untested = [a for a, c in sorted(attrs.items()) if c == 0]
        if untested:
            lines.append(
                f"  - **{dev_name}** device attrs untested: `{'`, `'.join(untested)}`"
            )

    # Untested channel attributes
    for dev_name, directions in sorted(chan_attrs.items()):
        for direction, channels in sorted(directions.items()):
            for ch_id, attrs in sorted(channels.items()):
                untested = [a for a, c in sorted(attrs.items()) if c == 0]
                if untested:
                    lines.append(
                        f"  - **{dev_name}** {direction} ch `{ch_id}` untested: "
                        f"`{'`, `'.join(untested)}`"
                    )

    return lines


def generate_report(hardware_names, new_classes, coverage_folder):
    """Generate the full markdown report."""
    lines = []
    lines.append("# IIO Context Coverage Report")
    lines.append("")
    lines.append(f"New device classes in this PR: **{', '.join(sorted(new_classes))}**")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "| Hardware | Device Attr Coverage | Channel Attr Coverage | Total Coverage |"
    )
    lines.append(
        "|----------|---------------------|----------------------|----------------|"
    )

    details_lines = []
    missing = []

    for hw_name in sorted(hardware_names):
        data = load_coverage(coverage_folder, hw_name)
        if data is None:
            missing.append(hw_name)
            lines.append(f"| {hw_name} | N/A | N/A | No coverage data |")
            continue

        stats = compute_stats(data)
        lines.append(
            f"| {hw_name} "
            f"| {stats['dev_covered']}/{stats['dev_total']} ({stats['dev_pct']:.1f}%) "
            f"| {stats['chan_covered']}/{stats['chan_total']} ({stats['chan_pct']:.1f}%) "
            f"| {stats['covered']}/{stats['total']} ({stats['total_pct']:.1f}%) |"
        )

        # Collect untested details
        untested = format_untested_details(data)
        if untested:
            details_lines.append(f"### {hw_name}")
            details_lines.append("")
            details_lines.extend(untested)
            details_lines.append("")

    # Untested details section
    if details_lines:
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Untested attributes (click to expand)</summary>")
        lines.append("")
        lines.extend(details_lines)
        lines.append("</details>")

    # Warnings
    if missing:
        lines.append("")
        lines.append(
            f"> **Note:** No coverage data found for: {', '.join(missing)}. "
            "These hardware entries may not have matching tests or emulation support."
        )

    lines.append("")
    lines.append("---")
    lines.append("*Generated by IIO Context Coverage workflow*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Filter and format IIO coverage report"
    )
    parser.add_argument(
        "--hardware-names", required=True, help="JSON array of hardware names"
    )
    parser.add_argument(
        "--new-classes", required=True, help="JSON array of new class names"
    )
    parser.add_argument(
        "--coverage-folder",
        default="iio_coverage_results",
        help="Coverage results folder",
    )
    parser.add_argument("--output", required=True, help="Output markdown file path")
    args = parser.parse_args()

    hardware_names = json.loads(args.hardware_names)
    new_classes = json.loads(args.new_classes)

    if not hardware_names:
        report = (
            "# IIO Context Coverage Report\n\n"
            f"New device classes in this PR: **{', '.join(sorted(new_classes))}**\n\n"
            "> No hardware map entries found for these classes. "
            "Context coverage tracking requires an emulation entry in "
            "`test/emu/hardware_map.yml`.\n"
        )
    else:
        report = generate_report(hardware_names, new_classes, args.coverage_folder)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)

    print(f"Coverage report written to {args.output}")


if __name__ == "__main__":
    main()
