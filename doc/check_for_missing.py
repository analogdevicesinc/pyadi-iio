"""Utility script to check for missing classes"""

import glob
import os

import update_devs

root = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(root, "source", "devices", "adi.*.rst")

# Get current list of devices
devices_before_gen = glob.glob(path)

update_devs.update_devs()

# Check for missing classes
devices_after_gen = glob.glob(path)
missing = list(set(devices_before_gen) - set(devices_after_gen)) + list(
    set(devices_after_gen) - set(devices_before_gen)
)

if missing:
    print(
        f"Missing classes detected.\n{list(missing)}\n\nPlease run `update_devs.py` before committing code"
    )
    exit(1)
