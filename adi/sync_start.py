# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import time

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
        if "sync_start_enable" in self._txdac.attrs:
            return self._get_iio_dev_attr_str("sync_start_enable", _ctrl=self._txdac)
        else:
            if self._txdac.reg_read(0x80000068) & 0x1 == 0x1:
                return "arm"
            else:
                return "disarm"

    @tx_sync_start.setter
    def tx_sync_start(self, value):
        if "sync_start_enable" in self._txdac.attrs:
            self._set_iio_dev_attr_str("sync_start_enable", value, _ctrl=self._txdac)
        else:
            chan = self._txdac.find_channel("altvoltage0", True)
            chan.attrs["raw"].value = "1"

    @property
    def tx_sync_start_available(self):
        """ tx_sync_start_available: Returns a list of possible keys used for tx_sync_start """
        if "sync_start_enable_available" in self._txdac.attrs:
            return self._get_iio_dev_attr_str(
                "sync_start_enable_available", _ctrl=self._txdac
            )
        else:
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
        if "sync_start_enable" in self._rxadc.attrs:
            return self._get_iio_dev_attr_str("sync_start_enable", _ctrl=self._rxadc)
        else:
            if self._rxadc.reg_read(0x80000068) & 1 == 1:
                return "arm"
            else:
                return "disarm"

    @rx_sync_start.setter
    def rx_sync_start(self, value):
        if "sync_start_enable" in self._rxadc.attrs:
            self._set_iio_dev_attr_str("sync_start_enable", value, _ctrl=self._rxadc)
        else:
            start_time = time.time()
            self._rxadc.reg_write(0x80000044, 0x8)
            while self._rxadc.reg_read(0x80000068) == 0:
                if time.time() - start_time > 5:
                    raise Exception("Timeout reached. Sync start failed")
                self._rxadc.reg_write(0x80000044, 0x8)

    @property
    def rx_sync_start_available(self):
        """ rx_sync_start_available: Returns a list of possible keys used for rx_sync_start """
        if "sync_start_enable_available" in self._rxadc.attrs:
            return self._get_iio_dev_attr_str(
                "sync_start_enable_available", _ctrl=self._rxadc
            )
        else:
            return "arm"


class sync_start_b(attribute):
    """ Synchronization Control: This class allows for synchronous transfers
        between transmit and receive data movement or captures.
    """

    @property
    def tx_b_sync_start(self):
        """ tx_b_sync_start: Issue a synchronisation request

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
        if "sync_start_enable" in self._txdac2.attrs:
            return self._get_iio_dev_attr_str("sync_start_enable", _ctrl=self._txdac2)
        else:
            if self._txdac2.reg_read(0x80000068) & 0x1 == 0x1:
                return "arm"
            else:
                return "disarm"

    @tx_b_sync_start.setter
    def tx_b_sync_start(self, value):
        if "sync_start_enable" in self._txdac2.attrs:
            self._set_iio_dev_attr_str("sync_start_enable", value, _ctrl=self._txdac2)
        else:
            chan = self._txdac2.find_channel("altvoltage0", True)
            chan.attrs["raw"].value = "1"

    @property
    def tx_b_sync_start_available(self):
        """ tx_sync_start_available: Returns a list of possible keys used for tx_sync_start """
        if "sync_start_enable_available" in self._txdac2.attrs:
            return self._get_iio_dev_attr_str(
                "sync_start_enable_available", _ctrl=self._txdac2
            )
        else:
            return "arm"

    @property
    def rx_b_sync_start(self):
        """ rx_b_sync_start: Issue a synchronisation request

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
        if "sync_start_enable" in self._rxadc2.attrs:
            return self._get_iio_dev_attr_str("sync_start_enable", _ctrl=self._rxadc2)
        else:
            if self._rxadc2.reg_read(0x68) & 1 == 1:
                return "arm"
            else:
                return "disarm"

    @rx_b_sync_start.setter
    def rx_b_sync_start(self, value):
        if "sync_start_enable" in self._rxadc2.attrs:
            self._set_iio_dev_attr_str("sync_start_enable", value, _ctrl=self._rxadc2)
        else:
            start_time = time.time()
            self._rxadc2.reg_write(0x48, 0x2)
            while self._rxadc2.reg_read(0x68) == 0:
                if time.time() - start_time > 5:
                    raise Exception("Timeout reached. Sync start failed")
                self._rxadc2.reg_write(0x48, 0x2)

    @property
    def rx_b_sync_start_available(self):
        """ rx_sync_start_available: Returns a list of possible keys used for rx_sync_start """
        if "sync_start_enable_available" in self._rxadc2.attrs:
            return self._get_iio_dev_attr_str(
                "sync_start_enable_available", _ctrl=self._rxadc2
            )
        else:
            return "arm"
