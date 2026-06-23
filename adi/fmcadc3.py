# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.ad9625 import ad9625
from adi.ada4961 import ada4961


class fmcadc3(ad9625, ada4961):

    """ FMCADC3 High-Speed Data Aquistion Device """

    def __init__(self, uri=""):

        ad9625.__init__(self, uri=uri)
        ada4961.__init__(self, uri=uri)
