# Copyright (C) 2022 Analog Devices, Inc.
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


from adi.attribute import attribute


class sync_start(attribute):
    """ Synchronization Control: This class allows for synchronous transfers
        between transmit and receive data movement or captures.
    """

    @property
    def tx_sync_start(self):
        """ tx_sync_start: Issue a synchronisation request

        Possible values are:
            - **arm**: Writing this key will arm the trigger mechanism sensitive to an
              external sync signal. Once the external sync signal goes high
              it synchronizes channels within a DAC, and across multiple
              instances. This bit has an effect only the EXT_SYNC
              synthesis parameter is set.
            - **disarm**: Writing this key will disarm the trigger mechanism
              sensitive to an external sync signal. This bit has an
              effect only the EXT_SYNC synthesis parameter is set.
            - **trigger_manual**: Writing this key will issue an external sync event
              if it is hooked up inside the fabric. This key has an effect
              only the EXT_SYNC synthesis parameter is set.
              This key self clears.
        """
        try:
            return self._get_iio_dev_attr_str("sync_start_enable", _ctrl=self._txdac)
        except:  # noqa: E722
            if self._txdac.reg_read(0x80000068) & 0x1 == 0x1:
                return "arm"
            else:
                return "disarm"

    @tx_sync_start.setter
    def tx_sync_start(self, value):
        try:
            self._set_iio_dev_attr_str("sync_start_enable", value, _ctrl=self._txdac)
        except:  # noqa: E722
            chan = self._txdac.find_channel("altvoltage0", True)
            chan.attrs["raw"].value = "1"

    @property
    def tx_sync_start_available(self):
        """ tx_sync_start_available: Returns a list of possible keys used for tx_sync_start """
        try:
            return self._get_iio_dev_attr_str(
                "sync_start_enable_available", _ctrl=self._txdac
            )
        except:  # noqa: E722
            return "arm"

    @property
    def rx_sync_start(self):
        """ rx_sync_start: Issue a synchronisation request

        Possible values are:
            - **arm**: Writing this key will arm the trigger mechanism sensitive to an
              external sync signal. Once the external sync signal goes high
              it synchronizes channels within a ADC, and across multiple
              instances. This bit has an effect only the EXT_SYNC
              synthesis parameter is set.
            - **disarm**: Writing this key will disarm the trigger mechanism
              sensitive to an external sync signal. This bit has an
              effect only the EXT_SYNC synthesis parameter is set.
            - **trigger_manual**: Writing this key will issue an external sync event
              if it is hooked up inside the fabric. This key has an effect
              only the EXT_SYNC synthesis parameter is set.
              This key self clears.
        """
        try:
            return self._get_iio_dev_attr_str("sync_start_enable", _ctrl=self._rxadc)
        except:  # noqa: E722
            if self._rxadc.reg_read(0x80000068) & 1 == 1:
                return "arm"
            else:
                return "disarm"

    @rx_sync_start.setter
    def rx_sync_start(self, value):
        try:
            self._set_iio_dev_attr_str("sync_start_enable", value, _ctrl=self._rxadc)
        except:  # noqa: E722
            self._rxadc.reg_write(0x80000044, 0x8)
            while self._rxadc.reg_read(0x80000068) == 0:
                self._rxadc.reg_write(0x80000044, 0x8)

    @property
    def rx_sync_start_available(self):
        """ rx_sync_start_available: Returns a list of possible keys used for rx_sync_start """
        try:
            return self._get_iio_dev_attr_str(
                "sync_start_enable_available", _ctrl=self._rxadc
            )
        except:  # noqa: E722
            return "arm"
