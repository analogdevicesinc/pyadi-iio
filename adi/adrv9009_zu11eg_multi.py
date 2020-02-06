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

from adi.adrv9009_zu11eg import adrv9009_zu11eg
import time


class adrv9009_zu11eg_multi(object):
    """ ADRV9009-ZU11EG Multi-SOM Manager"""

    __rx_buffer_size_multi = 2 ** 14

    def __init__(self, master_uri="", slave_uris=[]):

        if not isinstance(slave_uris, list):
            Exception("slave_uris must be a list")

        self._dma_show_arming = False
        self._rx_initialized = False
        self.master = adrv9009_zu11eg(uri=master_uri)
        self.slaves = []
        for uri in slave_uris:
            self.slaves.append(adrv9009_zu11eg(uri=uri))

    @property
    def rx_buffer_size(self):
        """rx_buffer_size: Size of receive buffer in samples for each device"""
        return self.__rx_buffer_size_multi

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        self.__rx_buffer_size_multi = value
        for dev in self.slaves + [self.master]:
            dev.rx_buffer_size = value

    def __clock_chips_init(self):
        for dev in self.slaves + [self.master]:
            # disable RF seeder, doing it on SOM and Carrier breaks Sync
            dev._clock_chip_ext.reg_write(0x3, 0xF)
            # SET SOM pulses to 8
            dev._clock_chip.reg_write(0x5A, 0x4)
        self._clock_chips_initialized = True

    def __unsync(self):
        for dev in [self.master] + self.slaves:
            dev._clock_chip.reg_write(0x1, 0x61)
            dev._clock_chip_carrier.reg_write(0x1, 0x61)
            dev._clock_chip_ext.reg_write(0x1, 0x01)
            time.sleep(0.1)
            dev._clock_chip_ext.reg_write(0x1, 0x00)
            time.sleep(0.1)
            dev._clock_chip_carrier.reg_write(0x1, 0x60)
            time.sleep(0.1)
            dev._clock_chip.reg_write(0x1, 0x60)
            time.sleep(0.1)

    def __configure_continuous_sysref(self):
        for dev in self.slaves + [self.master]:
            # CLK2 sync pin mode as SYNC
            dev._clock_chip_carrier.reg_write(0x5, 0x42)
            # CLK3 sync pin mode as SYNC
            dev._clock_chip.reg_write(0x5, 0x43)
            # restart request for all 7044
            # iio_reg hmc7044 0x1 0x62
            dev._clock_chip.reg_write(0x1, 0x62)
            # iio_reg hmc7044-car 0x1 0x62
            dev._clock_chip_carrier.reg_write(0x1, 0x62)
            # iio_reg hmc7044-ext 0x1 0x02
            dev._clock_chip_ext.reg_write(0x1, 0x02)
            # sleep 0.1
            time.sleep(0.1)
            # iio_reg hmc7044-ext 0x1 0x00
            dev._clock_chip_ext.reg_write(0x1, 0x00)
            # sleep 0.1
            time.sleep(0.1)
            # iio_reg hmc7044-car 0x1 0x60
            dev._clock_chip_carrier.reg_write(0x1, 0x60)
            # sleep 0.1
            time.sleep(0.1)
            # iio_reg hmc7044 0x1 0x60
            dev._clock_chip.reg_write(0x1, 0x60)
            # sleep 0.1
            time.sleep(0.1)

    def __sync(self):
        # Reseed request to clk1 -----> syncs the output of the 1st clk
        # iio_reg hmc7044-ext 0x1 0x80
        self.master._clock_chip_ext.reg_write(0x1, 0x80)
        # iio_reg hmc7044-ext 0x1 0x00
        self.master._clock_chip_ext.reg_write(0x1, 0x00)
        time.sleep(0.1)
        # pulse request to CLK1----> syncs the outputs of CLK2
        # iio_attr -q -d hmc7044-ext sysref_request 1
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"
        time.sleep(0.1)

        # CLK2 sync pin mode as Pulsor so it doesn't resync on next pulse
        # iio_reg hmc7044-car 0x5 0x82
        for slave in self.slaves:
            slave._clock_chip_carrier.reg_write(0x5, 0x82)

        # CLK2 sync pin mode as Pulsor so it doesn't resync on next pulse
        # iio_reg hmc7044-car 0x5 0x82
        self.master._clock_chip_carrier.reg_write(0x5, 0x82)
        time.sleep(0.1)

        # pulse request to CLK1----> syncs the outputs of CLK3
        # iio_attr -q -d hmc7044-ext sysref_request 1
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"
        time.sleep(0.1)
        # CLK3 sync pin mode as Pulsor so it doesn't resync on next pulse
        # iio_reg hmc7044 0x5 0x83
        self.master._clock_chip.reg_write(0x5, 0x83)

        # CLK3 sync pin mode as Pulsor so it doesn't resync on next pulse
        # iio_reg hmc7044 0x5 0x83
        for slave in self.slaves:
            slave._clock_chip.reg_write(0x5, 0x83)

    def __mcs(self):
        for dev in self.slaves + [self.master]:
            # 8 pulses on pulse generator request
            # iio_reg hmc7044 0x5a 4
            dev._clock_chip.reg_write(0x5A, 4)
            # step 0 & 1
            dev._ctrl.attrs["multichip_sync"].value = "0"
            dev._ctrl_b.attrs["multichip_sync"].value = "0"
            dev._ctrl.attrs["multichip_sync"].value = "1"
            dev._ctrl_b.attrs["multichip_sync"].value = "1"
        time.sleep(0.1)

        # step 2
        # iio_attr -q -d hmc7044-ext sysref_request 1
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"
        for dev in [self.master] + self.slaves:
            # iio_attr  -q -d adrv9009-phy multichip_sync 11 >/dev/null 2>&1
            # iio_attr  -q -d adrv9009-phy-b multichip_sync 11 >/dev/null 2>&1
            dev._ctrl.attrs["multichip_sync"].value = "11"
            dev._ctrl_b.attrs["multichip_sync"].value = "11"

        # step 3 & 4
        for dev in [self.master] + self.slaves:
            try:
                dev._ctrl.attrs["multichip_sync"].value = "3"
            except:
                pass
            try:
                dev._ctrl_b.attrs["multichip_sync"].value = "3"
            except:
                pass
            try:
                dev._ctrl.attrs["multichip_sync"].value = "4"
            except:
                pass
            try:
                dev._ctrl_b.attrs["multichip_sync"].value = "4"
            except:
                pass

        # step 5
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"

        # step 6
        for dev in [self.master] + self.slaves:
            dev._ctrl.attrs["multichip_sync"].value = "6"
            dev._ctrl_b.attrs["multichip_sync"].value = "6"

        # step 7
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"

        # step 8 & 9
        for dev in [self.master] + self.slaves:
            dev._ctrl.attrs["multichip_sync"].value = "8"
            dev._ctrl_b.attrs["multichip_sync"].value = "8"
            dev._ctrl.attrs["multichip_sync"].value = "9"
            dev._ctrl_b.attrs["multichip_sync"].value = "9"

        # step 10
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"

        # step 11
        for dev in [self.master] + self.slaves:
            dev._ctrl.attrs["multichip_sync"].value = "11"
            dev._ctrl_b.attrs["multichip_sync"].value = "11"
            # 8 pulses on pulse generator request
            dev._clock_chip.reg_write(0x5A, 1)

        # cal RX phase correction
        for dev in self.slaves + [self.master]:
            dev._ctrl.attrs["calibrate_rx_phase_correction_en"].value = "1"
            dev._ctrl.attrs["calibrate"].value = "1"
            dev._ctrl_b.attrs["calibrate_rx_phase_correction_en"].value = "1"
            dev._ctrl_b.attrs["calibrate"].value = "1"
        time.sleep(1)

    def __rx_dma_arm(self):
        for dev in self.slaves + [self.master]:
            if self._dma_show_arming:
                print("--DMA ARMING--", dev.uri)
            dev._rxadc.reg_write(0x80000044, 0x8)
            while dev._rxadc.reg_read(0x80000068) == 0:
                dev._rxadc.reg_write(0x80000044, 0x8)
                if self._dma_show_arming:
                    print(".", end="")
            print("\n--DMA ARMED--", dev.uri)

    def rx(self):
        if not self._rx_initialized:
            self.__clock_chips_init()
            self.__unsync()
            self.__configure_continuous_sysref()
            self.__sync()
            self.__mcs()
            self.__rx_dma_arm()
            # Create buffers but do not pull data yet
            for dev in [self.master] + self.slaves:
                dev._rx_init_channels()
            self._rx_initialized = True
        self.master._clock_chip_ext.attrs["sysref_request"].value = "1"
        data = []
        for dev in [self.master] + self.slaves:
            data = data + dev.rx()
        return data
