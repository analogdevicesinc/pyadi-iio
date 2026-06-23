# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.ad9152 import ad9152
from adi.ad9680 import ad9680


class DAQ3(ad9152, ad9680):
    """ DAQ3 High-Speed Data Aquistion Device """

    def __init__(self, uri=""):

        ad9152.__init__(self, uri=uri)
        ad9680.__init__(self, uri=uri)
