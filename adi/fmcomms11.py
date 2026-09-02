# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.ad9162 import ad9162
from adi.ad9625 import ad9625


class FMComms11(
    ad9162, ad9625,
):
    """ FMCOMMS11 Transceiver """

    def __init__(self, uri=""):

        ad9162.__init__(self, uri=uri)
        ad9625.__init__(self, uri=uri)
