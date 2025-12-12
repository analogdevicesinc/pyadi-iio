# Copyright (C) 2022-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""JESD Shim import to handle JESD as optional dependency"""

try:
    from .sshfs import sshfs
    from .jesd_internal import jesd, jesd_eye_scan
except ImportError:
    jesd = None
    jesd_eye_scan = None
