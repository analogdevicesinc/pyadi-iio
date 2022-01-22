# Copyright (C) 2019 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from adi.context_manager import context_manager
from adi.jesd import jesd
from adi.rx_tx import tx


class ad9136(tx, context_manager):
    """ AD9136 High-Speed DAC """

    _complex_data = False
    _tx_channel_names = ["voltage0", "voltage1"]
    _device_name = ""

    def __init__(self, uri="", username="root", password="analog"):

        context_manager.__init__(self, uri, self._device_name)

        self._txdac = self._ctx.find_device("axi-ad9136-tx-hpc")
        if jesd:
            self._jesd = jesd(uri, username="root", password=password)

        tx.__init__(self)

    @property
    def sample_rate(self):
        """sample_rate: Sample rate RX and TX paths in samples per second."""
        return self._get_iio_attr("voltage0", "sampling_frequency", True, self._txdac)

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_iio_attr("voltage0", "sampling_frequency", True, value, self._txdac)

    @property
    def jesd204_statuses(self):
        """jesd204_statuses: JESD204 low-level driver data."""
        return self._jesd.get_all_statuses()
