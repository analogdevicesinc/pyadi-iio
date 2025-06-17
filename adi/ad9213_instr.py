# Copyright (C) 2020-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import datetime
import time
from typing import List
from adi.ad9213 import ad9213
from adi.ad4080 import ad4080

from adi.jesd import jesd as jesd_api


class ad9213_instr(object):
    """ad9213_instr Manager

    parameters:
        primary_uri: type=string
            URI of primary ADRV9009-ZU11EG. Parent HMC7044 is connected
            to this SOM
        secondary_uris: type=list[string]
            URI(s) of secondary ADRV9009-ZU11EG(s).
        primary_jesd: type=adi.jesd
            JESD object associated with primary ADRV9009-ZU11EG
        secondary_jesds: type=list[adi.jesd]
            JESD object(s) associated with secondary ADRV9009-ZU11EG(s)
    """

    __rx_buffer_size_multi = 2 ** 14
    secondaries: List[ad4080] = []

    def __init__(
        self,
        primary_uri="",
        secondary_uris=[],
        primary_jesd=None,
        secondary_jesds=[None],
    ):

        if not jesd_api:
            raise Exception(
                "JESD optional dependencies are required.\n"
                + "Please install them using pip install pyadi-iio[jesd] "
                + "or pip install paramiko"
            )

        if not isinstance(secondary_uris, list):
            Exception("secondary_uris must be a list")
        if not isinstance(secondary_jesds, list):
            Exception("secondary_jesds must be a list")

        self._dma_show_arming = False
        self._jesd_show_status = False
        self._jesd_fsm_show_status = False
        self._rx_initialized = False
        self.primary = ad9213(uri=primary_uri,device_name="ad9213")
        self.secondaries = []
        self.samples_primary = []
        self.samples_secondary = []
        self.secondaries.append(ad4080(uri=primary_uri))

        for dev in self.secondaries + [self.primary]:
            dev._rxadc.set_kernel_buffers_count(1)

    def reinitialize(self):
        """reinitialize: reinitialize all transceivers"""
        for dev in self.secondaries + [self.primary]:
            property_names = [p for p in dir(dev) if "reinitialize" in p]
            for p in property_names:
                eval("dev." + p + "()")

    @property
    def rx_buffer_size(self):
        """rx_buffer_size: Size of receive buffer in samples for each device"""
        return self.__rx_buffer_size_multi

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        self.__rx_buffer_size_multi = value
        for dev in self.secondaries + [self.primary]:
            dev.rx_buffer_size = value

    def __read_jesd_status_all_devs(self, attr, islink=False):
        for dev in [self.primary]:
            if islink:
                devs = dev._jesd.get_all_link_statuses()
                for dev in devs:
                    lanes = devs[dev]
                    print("JESD {}: ".format(dev), end="")
                    for lane in lanes:
                        if attr in lanes[lane]:
                            print(" {}".format(lanes[lane][attr]), end="")
                    print("")
            else:
                s = dev._jesd.get_all_statuses()
                for dev in s:
                    if attr in s[dev]:
                        print("JESD {}: {} ({})".format(attr, s[dev][attr], dev))

    def __read_jesd_status(self):
        self.__read_jesd_status_all_devs("Link status")
        self.__read_jesd_status_all_devs("SYSREF captured")
        self.__read_jesd_status_all_devs("SYSREF alignment error")

    def __read_jesd_link_status(self):
        self.__read_jesd_status_all_devs("Errors", True)
        self.__read_jesd_status_all_devs("Initial Lane Alignment Sequence", True)
        self.__read_jesd_status_all_devs("Initial Frame Synchronization", True)

    def _device_is_running(self, dev, index, verbose):
        err = dev.jesd204_fsm_error
        paused = dev.jesd204_fsm_paused
        state = dev.jesd204_fsm_state

        if verbose:
            print(
                "%s: DEVICE%d: Is <%s> in state <%s> with status <%d>"
                % (dev.uri, index, "Paused" if paused else "Running", state, err)
            )

        if err:
            print(
                "\nERROR %s: DEVICE%d: Is <%s> in state <%s> with status <%d>\n"
                % (dev.uri, index, "Paused" if paused else "Running", state, err)
            )
            return "error"

        state_last = state == "opt_post_running_stage"

        if (state_last == 0) and (paused == 0):
            return "running"

        if (state_last == 0) and (paused == 1):
            return "paused"

        if (state_last == 1) and (paused == 0):
            return "done"

        assert False

    def __jesd204_fsm_is_done(self):
        cnt = 0
        for index, dev in enumerate([self.primary]):
            ret = self._device_is_running(dev, index, 0)
            if ret == "done":
                cnt += 1

        if cnt == len([self.primary]):
            return "done"

    def _jesd204_fsm_sync(self):
        while True:
            if self.__jesd204_fsm_is_done() == "done":
                return "done"

            for index, dev in enumerate([self.primary]):
                ret = self._device_is_running(dev, index, self._jesd_fsm_show_status)
                if index == 0:
                    statep = dev.jesd204_fsm_state
                else:
                    state = dev.jesd204_fsm_state
                    assert state == statep

                if ret == "paused":
                    dev.jesd204_fsm_resume = "1"

                if ret == "error":
                    return ret

    def __rx_dma_arm(self):
        for dev in self.secondaries + [self.primary]:
            if self._dma_show_arming:
                print("--DMA ARMING--", dev.uri)
            dev.rx_sync_start = "arm"
            if self._dma_show_arming:
                print("\n--DMA ARMED--", dev.uri)

    def sysref_request(self):
        """sysref_request: Sysref request for parent HMC7044"""
        self.primary._clock_chip_fmc.attrs["sysref_request"].value = "1"


    def __refill_samples(self, dev, is_primary):
        if is_primary:
            self.samples_primary = dev.rx()
        else:
            self.samples_secondary = dev.rx()

    def _pre_rx_setup(self):
        retries = 3
        for _ in range(retries):
            try:

                self._jesd204_fsm_sync()

                if self._jesd_show_status:
                    self.__read_jesd_status()
                    self.__read_jesd_link_status()

                for dev in [self.primary] + self.secondaries:
                    dev.rx_destroy_buffer()
                return

            except:  # noqa: E722
                print("Re-initializing due to lock-up")
                self.reinitialize()
        raise Exception("Unable to initialize (Board reboot required)")



    def rx_destroy_buffer(self):
        for dev in [self.primary] + self.secondaries:
            dev.rx_destroy_buffer()
    def rx(self):
        """Receive data from multiple hardware buffers for each channel index in
        rx_enabled_channels of each child object (primary,secondaries[indx]).

        returns: type=numpy.array or list of numpy.array
            An array or list of arrays when more than one receive channel
            is enabled containing samples from a channel or set of channels.
            Data will be complex when using a complex data device.
        """
        if not self._rx_initialized:
            self._rx_initialized = True
        data = []
        self.__rx_dma_arm()
        # Recreate all buffers
        for dev in [self.primary] + self.secondaries:
            dev.rx_destroy_buffer()
            dev._rx_init_channels()

        self.sysref_request()

        rx_data1 = self.primary.rx()
        rx_data2 = self.secondaries[0].rx()
        return rx_data1, rx_data2
