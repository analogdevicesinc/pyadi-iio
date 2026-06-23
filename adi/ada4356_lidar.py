# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""ADA4356 LiDAR System"""

from adi.ada4355 import ada4355
from adi.tddn import tddn


class ada4356_lidar(ada4355):
    """ADA4356 LiDAR System with TDD Controller"""

    def __init__(self, uri=""):
        ada4355.__init__(self, uri)
        self.tdd = tddn(uri)
