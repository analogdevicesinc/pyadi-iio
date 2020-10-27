# Copyright (C) 2020 Analog Devices, Inc.
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

import datetime
import threading
import time
from typing import List

from adi.adrv9009_zu11eg import adrv9009_zu11eg
from adi.adrv9009_zu11eg_fmcomms8 import adrv9009_zu11eg_fmcomms8


class adrv9009_zu11eg_multi(object):
    """ ADRV9009-ZU11EG Multi-SOM Manager"""

    __rx_buffer_size_multi = 2 ** 14
    slaves: List[adrv9009_zu11eg] = []

    def __init__(
        self,
        master_uri="",
        slave_uris=[],
        master_jesd=None,
        slave_jesds=[None],
        fmcomms8=False,
    ):

        if not isinstance(slave_uris, list):
            Exception("slave_uris must be a list")
        if not isinstance(slave_jesds, list):
            Exception("slave_jesds must be a list")

        self._dma_show_arming = False
        self._jesd_show_status = False
        self._rx_initialized = False
        self.fmcomms8 = fmcomms8
        if fmcomms8:
            self.master = adrv9009_zu11eg_fmcomms8(uri=master_uri, jesd=master_jesd)
        else:
            self.master = adrv9009_zu11eg(uri=master_uri, jesd=master_jesd)
        self.slaves = []
        self.samples_master = []
        self.samples_slave = []
        for i, uri in enumerate(slave_uris):
            if fmcomms8:
                self.slaves.append(
                    adrv9009_zu11eg_fmcomms8(uri=uri, jesd=slave_jesds[i])
                )
            else:
                self.slaves.append(adrv9009_zu11eg(uri=uri, jesd=slave_jesds[i]))

        for dev in self.slaves + [self.master]:
            dev._rxadc.set_kernel_buffers_count(1)

    def reinitialize(self):
        for dev in self.slaves + [self.master]:
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
        for dev in self.slaves + [self.master]:
            dev.rx_buffer_size = value

    def __read_jesd_status_all_devs(self, attr, islink=False):
        for dev in self.slaves + [self.master]:
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

    def __setup_framers(self):
        # adi,jesd204-framer-a-lmfc-offset 15
        for dev in self.slaves + [self.master]:
            v1 = (
                dev._get_iio_debug_attr_str(
                    "adi,jesd204-framer-a-lmfc-offset", dev._ctrl_b
                )
                == "15"
            )
            v2 = (
                dev._get_iio_debug_attr_str(
                    "adi,jesd204-framer-a-lmfc-offset", dev._ctrl
                )
                == "15"
            )
            if (not v1) or (not v2):
                dev._set_iio_debug_attr_str(
                    "adi,jesd204-framer-a-lmfc-offset", "15", dev._ctrl_b
                )
                dev._set_iio_debug_attr_str(
                    "adi,jesd204-framer-a-lmfc-offset", "15", dev._ctrl
                )
                dev._set_iio_debug_attr_str("initialize", "1", dev._ctrl_b)
                dev._set_iio_debug_attr_str("initialize", "1", dev._ctrl)
                print("Re-initializing JESD links")
                time.sleep(10)

    def device_is_running(self, dev, index, verbose):
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

        return "undef"

    def __jesd204_fsm_is_done(self):
        cnt = 0
        for index, dev in enumerate([self.master] + self.slaves):
            ret = self.device_is_running(dev, index, 0)
            if ret == "done":
                cnt += 1

        if cnt == len([self.master] + self.slaves):
            return "done"

    def jesd204_fsm_sync(self):
        while True:
            if self.__jesd204_fsm_is_done() == "done":
                return "done"

            for index, dev in enumerate(self.slaves + [self.master]):
                ret = self.device_is_running(dev, index, 1)
                if ret == "paused":
                    # print ("RESUME device %d" % index)
                    dev.jesd204_fsm_resume = "1"

                if ret == "error":
                    return ret

    def __unsync(self):
        for dev in [self.master] + self.slaves:
            dev._clock_chip.attrs["sleep_request"].value = "1"
            if self.fmcomms8:
                dev._clock_chip_fmc.attrs["sleep_request"].value = "1"
            dev._clock_chip_carrier.attrs["sleep_request"].value = "1"

        self.master._clock_chip_ext.attrs["sleep_request"].value = "1"
        time.sleep(0.1)
        self.master._clock_chip_ext.attrs["sleep_request"].value = "0"

        for dev in [self.master] + self.slaves:
            time.sleep(0.1)
            dev._clock_chip_carrier.attrs["sleep_request"].value = "0"
            time.sleep(0.1)
            if self.fmcomms8:
                dev._clock_chip_fmc.attrs["sleep_request"].value = "0"
            dev._clock_chip.attrs["sleep_request"].value = "0"

    def __rx_dma_arm(self):
        for dev in self.slaves + [self.master]:
            if self._dma_show_arming:
                print("--DMA ARMING--", dev.uri)
            dev._rxadc.reg_write(0x80000044, 0x8)
            while dev._rxadc.reg_read(0x80000068) == 0:
                dev._rxadc.reg_write(0x80000044, 0x8)
                if self._dma_show_arming:
                    print(".", end="")
            if self._dma_show_arming:
                print("\n--DMA ARMED--", dev.uri)

    def __dds_sync_enable(self, enable):
        for dev in self.slaves + [self.master]:
            if self._dma_show_arming:
                print("--DAC SYNC ARMING--", dev.uri)
            chan = dev._txdac.find_channel("altvoltage0", True)
            chan.attrs["raw"].value = str(enable)

        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"

    def set_trx_lo_frequency(self, freq):
        for dev in self.slaves + [self.master]:
            dev._set_iio_debug_attr_str("adi,trx-pll-lo-frequency_hz", freq, dev._ctrl)
            dev._set_iio_debug_attr_str(
                "adi,trx-pll-lo-frequency_hz", freq, dev._ctrl_b
            )
            dev._set_iio_debug_attr_str(
                "adi,trx-pll-lo-frequency_hz", freq, dev._ctrl_c
            )
            dev._set_iio_debug_attr_str(
                "adi,trx-pll-lo-frequency_hz", freq, dev._ctrl_d
            )

    def __refill_samples(self, dev, is_master):
        if is_master:
            self.samples_master = dev.rx()
        else:
            self.samples_slave = dev.rx()

    def _pre_rx_setup(self):
        retries = 3
        for _ in range(retries):
            try:
                for dev in [self.master] + self.slaves:
                    dev.jesd204_fsm_ctrl = 0

                self.__unsync()

                for dev in [self.master] + self.slaves:
                    dev.jesd204_fsm_ctrl = 1

                self.jesd204_fsm_sync()
                self.__dds_sync_enable(1)

                if self._jesd_show_status:
                    self.__read_jesd_status()
                    self.__read_jesd_link_status()

                for dev in [self.master] + self.slaves:
                    dev.rx_destroy_buffer()
                    dev._rx_init_channels()
                return
            except:
                print("Re-initializing due to lock-up")
                self.reinitialize()
            raise Exception("Unable to initialize (Board reboot required)")

    def rx(self):
        if not self._rx_initialized:
            self._pre_rx_setup()
            self._rx_initialized = True
        data = []
        self.__rx_dma_arm()
        # Recreate all buffers
        for dev in [self.master] + self.slaves:
            dev.rx_destroy_buffer()
            dev._rx_init_channels()
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"
        for dev in [self.master] + self.slaves:
            data += dev.rx()
        return data
