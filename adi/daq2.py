# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.ad9144 import ad9144
from adi.ad9680 import ad9680


class DAQ2(ad9144, ad9680):
    """ DAQ2 High-Speed Data Aquistion Device """

    def __init__(self, uri=""):

        ad9144.__init__(self, uri=uri)
        ad9680.__init__(self, uri=uri)
