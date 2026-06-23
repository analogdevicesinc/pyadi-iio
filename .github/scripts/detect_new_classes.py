#!/usr/bin/env python3
# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Detect new device classes added in a PR by diffing adi/__init__.py against the base branch.

Maps new classes to hardware entries in the emulation hardware map and outputs
results as GitHub Actions outputs.
"""

import json
import os
import re
import subprocess

import yaml


def parse_imports(text):
    """Extract all class names imported from adi submodules.

    Handles lines like:
        from adi.ad936x import Pluto, ad9361, ad9363, ad9364
        from adi.ad9081 import ad9081
    """
    classes = set()
    for match in re.finditer(r"from adi\.\w+ import (.+)", text):
        names = match.group(1).split(",")
        for name in names:
            name = name.strip()
            if name:
                classes.add(name)
    return classes


def get_base_init(base_ref):
    """Get adi/__init__.py content from the base branch."""
    try:
        result = subprocess.run(
            ["git", "show", f"origin/{base_ref}:adi/__init__.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        print(f"Warning: Could not read adi/__init__.py from origin/{base_ref}")
        return ""


def find_hardware_for_classes(new_classes, hw_map):
    """Find hardware map entries that support any of the new classes."""
    hardware_names = []
    class_to_hw = {}

    for hw_name, hw_entries in hw_map.items():
        for entry in hw_entries:
            if isinstance(entry, dict) and "pyadi_iio_class_support" in entry:
                supported = entry["pyadi_iio_class_support"]
                matching = new_classes & set(supported)
                if matching:
                    hardware_names.append(hw_name)
                    for cls in matching:
                        class_to_hw.setdefault(cls, []).append(hw_name)

    return hardware_names, class_to_hw


def main():
    base_ref = os.environ.get("GITHUB_BASE_REF", "main")

    # Parse base branch imports
    base_text = get_base_init(base_ref)
    base_classes = parse_imports(base_text)

    # Parse current branch imports
    with open("adi/__init__.py") as f:
        current_text = f.read()
    current_classes = parse_imports(current_text)

    # Find new classes
    new_classes = current_classes - base_classes

    if not new_classes:
        print("No new device classes detected.")
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
            f.write("has_new_classes=false\n")
            f.write("new_classes=[]\n")
            f.write("hardware_names=[]\n")
        return

    print(f"New device classes detected: {sorted(new_classes)}")

    # Load hardware map
    hw_map_path = os.path.join("test", "emu", "hardware_map.yml")
    with open(hw_map_path) as f:
        hw_map = yaml.safe_load(f)

    # Map classes to hardware entries
    hardware_names, class_to_hw = find_hardware_for_classes(new_classes, hw_map)

    # Report unmapped classes
    mapped_classes = set(class_to_hw.keys())
    unmapped = new_classes - mapped_classes
    if unmapped:
        print(f"Warning: No hardware map entry found for: {sorted(unmapped)}")

    print(f"Relevant hardware entries: {sorted(hardware_names)}")
    print(f"Class to hardware mapping: {class_to_hw}")

    # Write GitHub Actions outputs
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write("has_new_classes=true\n")
        f.write(f"new_classes={json.dumps(sorted(new_classes))}\n")
        f.write(f"hardware_names={json.dumps(sorted(hardware_names))}\n")


if __name__ == "__main__":
    main()
