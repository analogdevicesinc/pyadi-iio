# Copyright (C) 2022-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""JESD Shim import to handle JESD as optional dependency"""

try:
    from .sshfs import sshfs
    from .jesd_internal import jesd
except ImportError:
    jesd = None
