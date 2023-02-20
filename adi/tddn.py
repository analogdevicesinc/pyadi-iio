# Copyright (C) 2023 Analog Devices, Inc.
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

from typing import List

from adi.attribute import attribute
from adi.context_manager import context_manager


class tddn(context_manager, attribute):

    """TDD Controller"""

    _device_name: str = ""

    def __init__(self, uri=""):
        """TDD Controller"""
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("iio-axi-tdd-0")

    @property
    def frame_length_ms(self) -> float:
        """frame_length_ms: TDD frame length (ms)"""
        return self._get_iio_dev_attr("frame_length_ms")

    @frame_length_ms.setter
    def frame_length_ms(self, value: float):
        self._set_iio_dev_attr("frame_length_ms", value)

    @property
    def frame_length_raw(self) -> float:
        """frame_length_raw: TDD frame length (clock cycles)"""
        return self._get_iio_dev_attr("frame_length_raw")

    @frame_length_raw.setter
    def frame_length_raw(self, value: float):
        self._set_iio_dev_attr("frame_length_raw", value)

    @property
    def startup_delay_ms(self) -> float:
        """startup_delay_ms: Initial delay before the first frame (ms)"""
        return self._get_iio_dev_attr("startup_delay_ms")

    @startup_delay_ms.setter
    def startup_delay_ms(self, value: float):
        self._set_iio_dev_attr("startup_delay_ms", value)

    @property
    def startup_delay_raw(self) -> float:
        """startup_delay_raw: Initial delay before the first frame (clock cycles)"""
        return self._get_iio_dev_attr("startup_delay_raw")

    @startup_delay_raw.setter
    def startup_delay_raw(self, value: float):
        self._set_iio_dev_attr("startup_delay_raw", value)

    @property
    def internal_sync_period_ms(self) -> float:
        """internal_sync_period_ms: Period of the internal sync generator (ms)"""
        return self._get_iio_dev_attr("internal_sync_period_ms")

    @internal_sync_period_ms.setter
    def internal_sync_period_ms(self, value: float):
        self._set_iio_dev_attr("internal_sync_period_ms", value)

    @property
    def internal_sync_period_raw(self) -> float:
        """internal_sync_period_raw: Period of the internal sync generator (clock cycles)"""
        return self._get_iio_dev_attr("internal_sync_period_raw")

    @internal_sync_period_raw.setter
    def internal_sync_period_raw(self, value: float):
        self._set_iio_dev_attr("internal_sync_period_raw", value)

    @property
    def burst_count(self) -> int:
        """burst_count: Amount of frames to produce, where 0 means repeat indefinetly"""
        return self._get_iio_dev_attr("burst_count")

    @burst_count.setter
    def burst_count(self, value: int):
        self._set_iio_dev_attr("burst_count", value)

    @property
    def sync_soft(self) -> bool:
        """sync_soft: Trigger one software sync pulse"""
        return bool(int(self._get_iio_dev_attr("sync_soft")))

    @sync_soft.setter
    def sync_soft(self, value: bool):
        self._set_iio_dev_attr("sync_soft", int(value))

    @property
    def sync_external(self) -> bool:
        """sync_external: Enable the external sync trigger"""
        return bool(int(self._get_iio_dev_attr("sync_external")))

    @sync_external.setter
    def sync_external(self, value: bool):
        self._set_iio_dev_attr("sync_external", int(value))

    @property
    def sync_internal(self) -> bool:
        """sync_internal: Enable the internal sync trigger"""
        return bool(int(self._get_iio_dev_attr("sync_internal")))

    @sync_internal.setter
    def sync_internal(self, value: bool):
        self._set_iio_dev_attr("sync_internal", int(value))

    @property
    def sync_reset(self) -> bool:
        """sync_reset: Reset the internal counter when receiving a sync event"""
        return bool(int(self._get_iio_dev_attr("sync_reset")))

    @sync_reset.setter
    def sync_reset(self, value: bool):
        self._set_iio_dev_attr("sync_reset", int(value))

    @property
    def enable(self) -> bool:
        """enable: Enable or disable the TDD engine"""
        return bool(int(self._get_iio_dev_attr("enable")))

    @enable.setter
    def enable(self, value: bool):
        self._set_iio_dev_attr("enable", int(value))

    @property
    def state(self) -> int:
        """state: The current state of the internal FSM"""
        return self._get_iio_dev_attr("state")

    @state.setter
    def state(self, value: int):
        self._set_iio_dev_attr("state", value)

    #
    # TDD channels
    #

    # CH0

    @property
    def out_channel0_enable(self) -> bool:
        """out_channel0_enable: CH0 output enable"""
        return bool(int(self._get_iio_attr("channel0", "enable", True)))

    @out_channel0_enable.setter
    def out_channel0_enable(self, value: bool):
        self._set_iio_attr("channel0", "enable", True, int(value))

    @property
    def out_channel0_polarity(self) -> bool:
        """out_channel0_polarity: CH0 output polarity"""
        return bool(int(self._get_iio_attr("channel0", "polarity", True)))

    @out_channel0_polarity.setter
    def out_channel0_polarity(self, value: bool):
        self._set_iio_attr("channel0", "polarity", True, int(value))

    @property
    def out_channel0_on_ms(self) -> float:
        """out_channel0_on_ms: The offset from the beggining of a new frame when CH0 is set (ms)"""
        return self._get_iio_attr("channel0", "on_ms", True)

    @out_channel0_on_ms.setter
    def out_channel0_on_ms(self, value: float):
        self._set_iio_attr("channel0", "on_ms", True, value)

    @property
    def out_channel0_on_raw(self) -> float:
        """out_channel0_on_raw: The offset from the beggining of a new frame when CH0 is set (clock cycles)"""
        return self._get_iio_attr("channel0", "on_raw", True)

    @out_channel0_on_raw.setter
    def out_channel0_on_raw(self, value: float):
        self._set_iio_attr("channel0", "on_raw", True, value)

    @property
    def out_channel0_off_ms(self) -> float:
        """out_channel0_off_ms: The offset from the beggining of a new frame when CH0 is reset (ms)"""
        return self._get_iio_attr("channel0", "off_ms", True)

    @out_channel0_off_ms.setter
    def out_channel0_off_ms(self, value: float):
        self._set_iio_attr("channel0", "off_ms", True, value)

    @property
    def out_channel0_off_raw(self) -> float:
        """out_channel0_off_raw: The offset from the beggining of a new frame when CH0 is reset (clock cycles)"""
        return self._get_iio_attr("channel0", "off_raw", True)

    @out_channel0_off_raw.setter
    def out_channel0_off_raw(self, value: float):
        self._set_iio_attr("channel0", "off_raw", True, value)

    # CH1

    @property
    def out_channel1_enable(self) -> bool:
        """out_channel1_enable: CH1 output enable"""
        return bool(int(self._get_iio_attr("channel1", "enable", True)))

    @out_channel1_enable.setter
    def out_channel1_enable(self, value: bool):
        self._set_iio_attr("channel1", "enable", True, int(value))

    @property
    def out_channel1_polarity(self) -> bool:
        """out_channel1_polarity: CH1 output polarity"""
        return bool(int(self._get_iio_attr("channel1", "polarity", True)))

    @out_channel1_polarity.setter
    def out_channel1_polarity(self, value: bool):
        self._set_iio_attr("channel1", "polarity", True, int(value))

    @property
    def out_channel1_on_ms(self) -> float:
        """out_channel1_on_ms: The offset from the beggining of a new frame when CH1 is set (ms)"""
        return self._get_iio_attr("channel1", "on_ms", True)

    @out_channel1_on_ms.setter
    def out_channel1_on_ms(self, value: float):
        self._set_iio_attr("channel1", "on_ms", True, value)

    @property
    def out_channel1_on_raw(self) -> float:
        """out_channel1_on_raw: The offset from the beggining of a new frame when CH1 is set (clock cycles)"""
        return self._get_iio_attr("channel1", "on_raw", True)

    @out_channel1_on_raw.setter
    def out_channel1_on_raw(self, value: float):
        self._set_iio_attr("channel1", "on_raw", True, value)

    @property
    def out_channel1_off_ms(self) -> float:
        """out_channel1_off_ms: The offset from the beggining of a new frame when CH1 is reset (ms)"""
        return self._get_iio_attr("channel1", "off_ms", True)

    @out_channel1_off_ms.setter
    def out_channel1_off_ms(self, value: float):
        self._set_iio_attr("channel1", "off_ms", True, value)

    @property
    def out_channel1_off_raw(self) -> float:
        """out_channel1_off_raw: The offset from the beggining of a new frame when CH1 is reset (clock cycles)"""
        return self._get_iio_attr("channel1", "off_raw", True)

    @out_channel1_off_raw.setter
    def out_channel1_off_raw(self, value: float):
        self._set_iio_attr("channel1", "off_raw", True, value)

    # CH2

    @property
    def out_channel2_enable(self) -> bool:
        """out_channel2_enable: CH2 output enable"""
        return bool(int(self._get_iio_attr("channel2", "enable", True)))

    @out_channel2_enable.setter
    def out_channel2_enable(self, value: bool):
        self._set_iio_attr("channel2", "enable", True, int(value))

    @property
    def out_channel2_polarity(self) -> bool:
        """out_channel2_polarity: CH2 output polarity"""
        return bool(int(self._get_iio_attr("channel2", "polarity", True)))

    @out_channel2_polarity.setter
    def out_channel2_polarity(self, value: bool):
        self._set_iio_attr("channel2", "polarity", True, int(value))

    @property
    def out_channel2_on_ms(self) -> float:
        """out_channel2_on_ms: The offset from the beggining of a new frame when CH2 is set (ms)"""
        return self._get_iio_attr("channel2", "on_ms", True)

    @out_channel2_on_ms.setter
    def out_channel2_on_ms(self, value: float):
        self._set_iio_attr("channel2", "on_ms", True, value)

    @property
    def out_channel2_on_raw(self) -> float:
        """out_channel2_on_raw: The offset from the beggining of a new frame when CH2 is set (clock cycles)"""
        return self._get_iio_attr("channel2", "on_raw", True)

    @out_channel2_on_raw.setter
    def out_channel2_on_raw(self, value: float):
        self._set_iio_attr("channel2", "on_raw", True, value)

    @property
    def out_channel2_off_ms(self) -> float:
        """out_channel2_off_ms: The offset from the beggining of a new frame when CH2 is reset (ms)"""
        return self._get_iio_attr("channel2", "off_ms", True)

    @out_channel2_off_ms.setter
    def out_channel2_off_ms(self, value: float):
        self._set_iio_attr("channel2", "off_ms", True, value)

    @property
    def out_channel2_off_raw(self) -> float:
        """out_channel2_off_raw: The offset from the beggining of a new frame when CH2 is reset (clock cycles)"""
        return self._get_iio_attr("channel2", "off_raw", True)

    @out_channel2_off_raw.setter
    def out_channel2_off_raw(self, value: float):
        self._set_iio_attr("channel2", "off_raw", True, value)

