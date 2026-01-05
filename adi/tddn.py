# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from typing import List

from adi.attribute import attribute
from adi.context_manager import context_manager


class tddn(context_manager, attribute):

    """TDDN Controller"""

    channel = []  # type: ignore
    _device_name: str = ""

    def __init__(self, uri=""):
        """TDDN Controller"""
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("iio-axi-tdd-0")

        for ch in self._ctrl.channels:
            name = ch._id
            self.channel.append(self._channel(self._ctrl, name))

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
        """burst_count: Amount of frames to produce, where 0 means repeat indefinitely"""
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

    class _channel(attribute):

        """TDDN channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def enable(self) -> bool:
            """channel_enable: Selected channel output enable"""
            return bool(int(self._get_iio_attr(self.name, "enable", True)))

        @enable.setter
        def enable(self, value: bool):
            self._set_iio_attr(self.name, "enable", True, int(value))

        @property
        def polarity(self) -> bool:
            """channel_polarity: Selected channel output polarity"""
            return bool(int(self._get_iio_attr(self.name, "polarity", True)))

        @polarity.setter
        def polarity(self, value: bool):
            self._set_iio_attr(self.name, "polarity", True, int(value))

        @property
        def on_ms(self) -> float:
            """channel_on_ms: The offset from the beginning of a new frame when the selected channel is set (ms)"""
            return self._get_iio_attr(self.name, "on_ms", True)

        @on_ms.setter
        def on_ms(self, value: float):
            self._set_iio_attr(self.name, "on_ms", True, value)

        @property
        def on_raw(self) -> float:
            """channel_on_raw: The offset from the beginning of a new frame when the selected channel is set (clock cycles)"""
            return self._get_iio_attr(self.name, "on_raw", True)

        @on_raw.setter
        def on_raw(self, value: float):
            self._set_iio_attr(self.name, "on_raw", True, value)

        @property
        def off_ms(self) -> float:
            """channel_off_ms: The offset from the beginning of a new frame when the selected channel is reset (ms)"""
            return self._get_iio_attr(self.name, "off_ms", True)

        @off_ms.setter
        def off_ms(self, value: float):
            self._set_iio_attr(self.name, "off_ms", True, value)

        @property
        def off_raw(self) -> float:
            """channel_off_raw: The offset from the beginning of a new frame when the selected channel is reset (clock cycles)"""
            return self._get_iio_attr(self.name, "off_raw", True)

        @off_raw.setter
        def off_raw(self, value: float):
            self._set_iio_attr(self.name, "off_raw", True, value)
