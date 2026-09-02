# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import datetime
import time
from typing import List

from adi.adrv9009_zu11eg import adrv9009_zu11eg
from adi.adrv9009_zu11eg_fmcomms8 import adrv9009_zu11eg_fmcomms8
from adi.jesd import jesd as jesd_api


class adrv9009_zu11eg_multi(object):
    """ADRV9009-ZU11EG Multi-SOM Manager

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
        fmcomms8: type=boolean
            Boolean flag to idenify is FMComms8(s) are attached to SOMs
    """

    __rx_buffer_size_multi = 2 ** 14
    secondaries: List[adrv9009_zu11eg] = []

    def __init__(
        self,
        primary_uri="",
        secondary_uris=[],
        primary_jesd=None,
        secondary_jesds=[None],
        fmcomms8=False,
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
        self._clk_chip_show_cap_bank_sel = False
        self._resync_tx = False
        self._rx_initialized = False
        self._request_sysref_carrier = False
        self.fmcomms8 = fmcomms8
        if fmcomms8:
            self.primary = adrv9009_zu11eg_fmcomms8(
                uri=primary_uri, jesd_monitor=True, jesd=primary_jesd
            )
        else:
            self.primary = adrv9009_zu11eg(
                uri=primary_uri, jesd_monitor=True, jesd=primary_jesd
            )
        self.secondaries = []
        self.samples_primary = []
        self.samples_secondary = []
        for i, uri in enumerate(secondary_uris):
            if fmcomms8:
                self.secondaries.append(
                    adrv9009_zu11eg_fmcomms8(
                        uri=uri, jesd_monitor=True, jesd=secondary_jesds[i]
                    )
                )
            else:
                self.secondaries.append(
                    adrv9009_zu11eg(uri=uri, jesd_monitor=True, jesd=secondary_jesds[i])
                )

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

    def __setup_framers(self):
        # adi,jesd204-framer-a-lmfc-offset 15
        for dev in self.secondaries + [self.primary]:
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
            if self.__jesd204_fsm_is_done() == "done":
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
            if self.fmcomms8:
                dev._clock_chip_fmc.attrs["sleep_request"].value = "1"
            dev._clock_chip_carrier.attrs["sleep_request"].value = "1"

        self.primary._clock_chip_ext.attrs["sleep_request"].value = "1"
        time.sleep(0.1)
        self.primary._clock_chip_ext.attrs["sleep_request"].value = "0"

        for dev in [self.primary] + self.secondaries:
            time.sleep(0.1)
            dev._clock_chip_carrier.attrs["sleep_request"].value = "0"
            time.sleep(0.1)
            if self.fmcomms8:
                dev._clock_chip_fmc.attrs["sleep_request"].value = "0"
            dev._clock_chip.attrs["sleep_request"].value = "0"

    def hmc7044_cap_sel(self):
        vals = []
        for dev in [self.primary] + self.secondaries:
            vals.append(dev._clock_chip.reg_read(0x8C))
            if self.fmcomms8:
                vals.append(dev._clock_chip_fmc.reg_read(0x8C))
            vals.append(dev._clock_chip_carrier.reg_read(0x8C))

        vals.append(self.primary._clock_chip_ext.reg_read(0x8C))
        return vals

    def hmc7044_set_cap_sel(self, vals):
        """hmc7044_set_cap_sel:

        parameters:
            vals: type=list
                Forces certain Capacitor bank selections.
                Typically the list returned form hmc7044_cap_sel
        """
        for dev in [self.primary] + self.secondaries:
            dev._clock_chip.reg_write(0xB2, vals.pop(0) << 2 | 1)
            if self.fmcomms8:
                dev._clock_chip_fmc.reg_write(0xB2, vals.pop(0) << 2 | 1)
            dev._clock_chip_carrier.reg_write(0xB2, vals.pop(0) << 2 | 1)

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
            dev._clock_chip_carrier.reg_write(0xCF + offs, enable)
            dev._clock_chip_carrier.reg_write(0xCB + offs, int(val) & 0x1F)
            dev._clock_chip_carrier.reg_write(0xCC + offs, int(digital) & 0x1F)

    def __rx_dma_arm(self):
        for dev in self.secondaries + [self.primary]:
            if self._dma_show_arming:
                print("--DMA ARMING--", dev.uri)
            dev.rx_sync_start = "arm"
            if self._dma_show_arming:
                print("\n--DMA ARMED--", dev.uri)

    def __dds_sync_enable(self, enable):
        for dev in self.secondaries + [self.primary]:
            if self._dma_show_arming:
                print("--DAC SYNC ARMING--", dev.uri)
            dev.tx_sync_start = "arm"

    def sysref_request(self):
        """sysref_request: Sysref request for parent HMC7044"""
        if self._request_sysref_carrier:
            self.primary._clock_chip_carrier.attrs["sysref_request"].value = "1"
        else:
            self.primary._clock_chip_ext.attrs["sysref_request"].value = "1"

    def set_trx_lo_frequency(self, freq):
        """set_trx_lo_frequency:

        parameters:
            freq: type=int
                Frequency in hertz to be applied to all LOs
        """
        for dev in self.secondaries + [self.primary]:
            dev._set_iio_debug_attr_str("adi,trx-pll-lo-frequency_hz", freq, dev._ctrl)
            dev._set_iio_debug_attr_str(
                "adi,trx-pll-lo-frequency_hz", freq, dev._ctrl_b
            )
            if self.fmcomms8:
                dev._set_iio_debug_attr_str(
                    "adi,trx-pll-lo-frequency_hz", freq, dev._ctrl_c
                )
                dev._set_iio_debug_attr_str(
                    "adi,trx-pll-lo-frequency_hz", freq, dev._ctrl_d
                )

    def set_trx_framer_a_loopback(self, enable):
        """set_trx_framer_a_loopback: Set bist_framer_a_loopback
        """
        for dev in self.secondaries + [self.primary]:
            dev._set_iio_debug_attr_str("bist_framer_a_loopback", enable, dev._ctrl)
            dev._set_iio_debug_attr_str("bist_framer_a_loopback", enable, dev._ctrl_b)
            if self.fmcomms8:
                dev._set_iio_debug_attr_str(
                    "bist_framer_a_loopback", enable, dev._ctrl_c
                )
                dev._set_iio_debug_attr_str(
                    "bist_framer_a_loopback", enable, dev._ctrl_d
                )

    def __refill_samples(self, dev, is_primary):
        if is_primary:
            self.samples_primary = dev.rx()
        else:
            self.samples_secondary = dev.rx()

    def _pre_rx_setup(self):
        retries = 3
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
