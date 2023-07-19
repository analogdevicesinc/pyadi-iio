# Copyright (C) 2022-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


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
