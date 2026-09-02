# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""JESD Shim import to handle JESD as optional dependency"""

try:
    from .jesd_internal import jesd
    from .sshfs import sshfs
except ImportError:
    jesd = None
