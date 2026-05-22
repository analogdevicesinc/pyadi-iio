#!/usr/bin/env python3
# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Filter IIO coverage results to hardware entries relevant to new device classes
and generate a markdown report suitable for posting as a PR comment."""

import argparse
import json
import os
import sys


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


def generate_report(hardware_names, new_classes, coverage_folder, fail_under):
    """Generate the report; return (markdown, parts_below_threshold)."""
    lines = []
    lines.append("# IIO Context Coverage Report")
    lines.append("")
    lines.append(f"New device classes in this PR: **{', '.join(sorted(new_classes))}**")
    lines.append("")
    lines.append(f"Minimum required total coverage: **{fail_under:.1f}%**")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "| Hardware | Device Attr Coverage | Channel Attr Coverage "
        "| Total Coverage | Status |"
    )
    lines.append(
        "|----------|---------------------|----------------------"
        "|----------------|--------|"
    )

    details_lines = []
    missing = []
    below_threshold = []

    for hw_name in sorted(hardware_names):
        data = load_coverage(coverage_folder, hw_name)
        if data is None:
            missing.append(hw_name)
            lines.append(f"| {hw_name} | N/A | N/A | No coverage data | ⚠️ |")
            continue

        stats = compute_stats(data)
        passed = stats["total_pct"] >= fail_under
        if not passed:
            below_threshold.append(hw_name)
        status = "✅" if passed else "❌"
        lines.append(
            f"| {hw_name} "
            f"| {stats['dev_covered']}/{stats['dev_total']} ({stats['dev_pct']:.1f}%) "
            f"| {stats['chan_covered']}/{stats['chan_total']} ({stats['chan_pct']:.1f}%) "
            f"| {stats['covered']}/{stats['total']} ({stats['total_pct']:.1f}%) "
            f"| {status} |"
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

    # Threshold result
    lines.append("")
    if below_threshold:
        lines.append(
            f"> ❌ **Coverage check failed.** The following new parts are below "
            f"the {fail_under:.1f}% minimum total coverage: "
            f"{', '.join(sorted(below_threshold))}."
        )
    else:
        lines.append(
            f"> ✅ **Coverage check passed.** All new parts meet the "
            f"{fail_under:.1f}% minimum total coverage."
        )

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

    return "\n".join(lines), below_threshold


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
    parser.add_argument(
        "--fail-under",
        type=float,
        default=75.0,
        help="Minimum total coverage percent required for each new part. "
        "The script exits non-zero if any new part falls below this value "
        "(default: 75).",
    )
    args = parser.parse_args()

    hardware_names = json.loads(args.hardware_names)
    new_classes = json.loads(args.new_classes)

    below_threshold = []
    if not hardware_names:
        report = (
            "# IIO Context Coverage Report\n\n"
            f"New device classes in this PR: **{', '.join(sorted(new_classes))}**\n\n"
            "> No hardware map entries found for these classes. "
            "Context coverage tracking requires an emulation entry in "
            "`test/emu/hardware_map.yml`.\n"
        )
    else:
        report, below_threshold = generate_report(
            hardware_names, new_classes, args.coverage_folder, args.fail_under
        )

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)

    print(f"Coverage report written to {args.output}")

    if below_threshold:
        print(
            f"::error::IIO context coverage below {args.fail_under:.1f}% for new "
            f"parts: {', '.join(sorted(below_threshold))}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
