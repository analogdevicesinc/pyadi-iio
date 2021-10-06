# Copyright (C) 2021 Analog Devices, Inc.
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

import time
from typing import List

from adi.ad9081_mc import QuadMxFE


class QuadMxFE_multi(object):
    """ADQUADMXFExEBZ Multi-SOM Manager

    parameters:
        primary_uri: type=string
            URI of primary ADQUADMXFExEBZ. Parent HMC7044 is connected
            to this SOM
        secondary_uris: type=list[string]
            URI(s) of secondary ADQUADMXFExEBZ(s).
        primary_jesd: type=adi.jesd
            JESD object associated with primary ADQUADMXFExEBZ
        secondary_jesds: type=list[adi.jesd]
            JESD object(s) associated with secondary ADQUADMXFExEBZ(s)
    """

    __rx_buffer_size_multi = 2 ** 14
    secondaries: List[QuadMxFE] = []

    def __init__(
        self,
        primary_uri="",
        secondary_uris=[],
        primary_jesd=None,
        secondary_jesds=[None],
    ):

        if not isinstance(secondary_uris, list):
            Exception("secondary_uris must be a list")
        if not isinstance(secondary_jesds, list):
            Exception("secondary_jesds must be a list")

        self._dma_show_arming = False
        self._jesd_show_status = False
        self._jesd_fsm_show_status = False
        self._clk_chip_show_cap_bank_sel = False
        self._resync_tx = False
        self._rx_initialized = False
        self._request_sysref_carrier = False
        self.primary = QuadMxFE(uri=primary_uri)
        self.secondaries = []
        self.samples_primary = []
        self.samples_secondary = []
        for uri in secondary_uris:
            self.secondaries.append(QuadMxFE(uri=uri))

        for dev in self.secondaries + [self.primary]:
            dev._rxadc.set_kernel_buffers_count(1)

        self.primary._clock_chip_ext = self.primary._ctx.find_device("hmc7044-ext")

    def reinitialize(self):
        """ reinitialize: reinitialize all transceivers """
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
        for dev in self.secondaries + [self.primary]:
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
        for index, dev in enumerate([self.primary] + self.secondaries):
            ret = self._device_is_running(dev, index, 0)

            if ret == "done":
                cnt += 1

        if cnt == len([self.primary] + self.secondaries):
            return "done"

    def _jesd204_fsm_sync(self):
        while True:
            stat = self.__jesd204_fsm_is_done()
            if stat == "done":
                return "done"

            for index, dev in enumerate(self.secondaries + [self.primary]):
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

    def __unsync(self):
        for dev in [self.primary] + self.secondaries:
            dev._clock_chip.attrs["sleep_request"].value = "1"

        self.primary._clock_chip_ext.attrs["sleep_request"].value = "1"
        time.sleep(0.1)
        self.primary._clock_chip_ext.attrs["sleep_request"].value = "0"

        for dev in [self.primary] + self.secondaries:
            dev._clock_chip.attrs["sleep_request"].value = "0"

    def hmc7044_cap_sel(self):
        vals = []
        for dev in [self.primary] + self.secondaries:
            vals.append(dev._clock_chip.reg_read(0x8C))

        vals.append(self.primary._clock_chip_ext.reg_read(0x8C))
        return vals

    def hmc7044_set_cap_sel(self, vals):
        """hmc7044_set_cap_sel:

        parameters:
            vals: type=list
                Forces certain Capacitor bank seletions.
                Typically the list returned form hmc7044_cap_sel
        """
        for dev in [self.primary] + self.secondaries:
            dev._clock_chip.reg_write(0xB2, vals.pop(0) << 2 | 1)

        self.primary._clock_chip_ext.reg_write(0xB2, vals.pop(0) << 2 | 1)

    def hmc7044_ext_output_delay(self, chan, digital, analog_ps):
        """hmc7044_ext_output_delay:

        parameters:
            digital: type=int
                Digital delay. Adjusts the phase of the divider signal
                by up to 17 half cycles of the VCO.
            analog_ps: type=int
                Analog delay. Adjusts the delay of the divider signal in
                increments of ~25 ps. Range is from 100ps to 700ps.
        """
        assert 0 <= chan <= 13
        if analog_ps - 100 >= 0:
            enable = 1
            val = (analog_ps - 100) / 25
        else:
            enable = 0
            val = 0

        offs = chan * 10
        self.primary._clock_chip_ext.reg_write(0xCF + offs, enable)
        self.primary._clock_chip_ext.reg_write(0xCB + offs, int(val) & 0x1F)
        self.primary._clock_chip_ext.reg_write(0xCC + offs, int(digital) & 0x1F)

    def hmc7044_car_output_delay(self, chan, digital, analog_ps):
        """hmc7044_car_output_delay:

        parameters:
            digital: type=int
                Digital delay. Adjusts the phase of the divider signal
                by up to 17 half cycles of the VCO.
            analog_ps: type=int
                Analog delay. Adjusts the delay of the divider signal in
                increments of ~25 ps. Range is from 100ps to 700ps.
        """
        assert 0 <= chan <= 13
        if analog_ps - 100 >= 0:
            enable = 1
            val = (analog_ps - 100) / 25
        else:
            enable = 0
            val = 0

        offs = chan * 10

        for dev in [self.primary] + self.secondaries:
            dev._clock_chip.reg_write(0xCF + offs, enable)
            dev._clock_chip.reg_write(0xCB + offs, int(val) & 0x1F)
            dev._clock_chip.reg_write(0xCC + offs, int(digital) & 0x1F)

    def __rx_dma_arm(self):
        for dev in self.secondaries + [self.primary]:
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
        for dev in self.secondaries + [self.primary]:
            if self._dma_show_arming:
                print("--DAC SYNC ARMING--", dev.uri)
            chan = dev._txdac.find_channel("altvoltage0", True)
            chan.attrs["raw"].value = str(enable)

    def sysref_request(self):
        """ sysref_request: Sysref request for parent HMC7044 """
        self.primary._clock_chip_ext.attrs["sysref_request"].value = "1"

    def __refill_samples(self, dev, is_primary):
        if is_primary:
            self.samples_primary = dev.rx()
        else:
            self.samples_secondary = dev.rx()

    def _pre_rx_setup(self):
        retries = 10
        for _ in range(retries):
            try:
                for dev in [self.primary] + self.secondaries:
                    dev.jesd204_fsm_ctrl = 0

                self.__unsync()

                for dev in [self.primary] + self.secondaries:
                    dev.jesd204_fsm_ctrl = 1

                self._jesd204_fsm_sync()

                if not self._resync_tx:
                    self.__dds_sync_enable(1)

                if self._clk_chip_show_cap_bank_sel:
                    print("HMC7044s CAP bank select: ", self.hmc7044_cap_sel())

                if self._jesd_show_status:
                    self.__read_jesd_status()
                    self.__read_jesd_link_status()

                for dev in [self.primary] + self.secondaries:
                    dev.rx_destroy_buffer()
                    dev._rx_init_channels()
                return
            except:  # noqa: E722
                print("Re-initializing due to lock-up")
                self.reinitialize()
        raise Exception("Unable to initialize (Board reboot required)")

    def rx(self):
        """Receive data from multiple hardware buffers for each channel index in
        rx_enabled_channels of each child object (primary,secondaries[indx]).

        returns: type=numpy.array or list of numpy.array
            An array or list of arrays when more than one receive channel
            is enabled containing samples from a channel or set of channels.
            Data will be complex when using a complex data device.
        """
        if not self._rx_initialized:
            self._pre_rx_setup()
            self._rx_initialized = True
        data = []
        self.__rx_dma_arm()
        # Recreate all buffers
        for dev in [self.primary] + self.secondaries:
            dev.rx_destroy_buffer()
            dev._rx_init_channels()

        if self._resync_tx:
            self.__dds_sync_enable(1)

        self.sysref_request()

        for dev in [self.primary] + self.secondaries:
            data += dev.rx()
        return data
