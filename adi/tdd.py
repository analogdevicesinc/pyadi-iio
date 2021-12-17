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

from typing import List

from adi.attribute import attribute
from adi.context_manager import context_manager


class tdd(context_manager, attribute):

    """TDD Controller"""

    _device_name: str = ""

    def __init__(self, uri=""):
        """TDD Controller"""
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device("axi-core-tdd")

    @property
    def frame_length_ms(self) -> float:
        """frame_length_ms: TDD frame length in ms"""
        return self._get_iio_dev_attr("frame_length_ms")

    @frame_length_ms.setter
    def frame_length_ms(self, value: float):
        self._set_iio_dev_attr("frame_length_ms", value)

    @property
    def frame_length_raw(self) -> float:
        """frame_length_raw: TDD frame length in cycles of the input clock"""
        return self._get_iio_dev_attr("frame_length_raw")

    @frame_length_raw.setter
    def frame_length_raw(self, value: float):
        self._set_iio_dev_attr("frame_length_raw", value)

    @property
    def burst_count(self) -> int:
        """burst_count: Amount of frames to produce.
        Should be 0 <= burst_count <= 255, where 0 means don't stop
        """
        return self._get_iio_dev_attr("burst_count")

    @burst_count.setter
    def burst_count(self, value: int):
        self._set_iio_dev_attr("burst_count", value)

    @property
    def counter_int(self) -> int:
        """counter_init: Internal counter start value"""
        return self._get_iio_dev_attr("counter_int")

    @counter_int.setter
    def counter_int(self, value: int):
        self._set_iio_dev_attr("counter_int", value)

    @property
    def dma_gateing_mode(self) -> str:
        """dma_gateing_mode: Which of the two DMA (dp) ports should be gated"""
        return self._get_iio_dev_attr("dma_gateing_mode")

    @dma_gateing_mode.setter
    def dma_gateing_mode(self, value: str):
        return self._set_iio_dev_attr("dma_gateing_mode", value)

    @property
    def en(self) -> bool:
        """en: Enable or disable the TDD engine"""
        return bool(int(self._get_iio_dev_attr("en")))

    @en.setter
    def en(self, value: bool):
        self._set_iio_dev_attr("en", int(value))

    @property
    def en_mode(self) -> str:
        """en_mode: In which mode the TDD engine should run"""
        return self._get_iio_dev_attr("en_mode")

    @en_mode.setter
    def en_mode(self, value: str):
        return self._set_iio_dev_attr("en_mode", value)

    @property
    def secondary(self) -> bool:
        """secondary: Enable secondary times. This allows one signal to go high
        twice at two times within a single frame
        """
        return bool(int(self._get_iio_dev_attr("secondary")))

    @secondary.setter
    def secondary(self, value: bool):
        self._set_iio_dev_attr("secondary", int(value))

    #
    # TDD channels
    #

    def __get_tdd_channel(self, name: str, output: bool, raw: bool) -> List:
        return [
            self._get_iio_attr(
                "data{}".format(c),
                "{}{}_{}".format(name, d, "raw" if raw else "ms"),
                output,
            )
            for d, c in [("on", 0), ("off", 0), ("on", 1), ("off", 1)]
        ]

    def __set_tdd_channel(
        self, name: str, output: bool, raw: bool, values: List
    ) -> List:
        if len(values) != 4:
            raise RuntimeError("Expected four values, received {}".format(len(values)))

        for v, d, c in zip(values, ["on", "off", "on", "off"], [0, 0, 1, 1]):
            self._set_iio_attr(
                "data{}".format(c),
                "{}{}_{}".format(name, d, "raw" if raw else "ms"),
                output,
                v,
            )

    @property
    def tx_dma_raw(self) -> List[int]:
        """tx_dma_raw: TX DMA port timing parameters in clock cycles.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("dp_", True, True)

    @tx_dma_raw.setter
    def tx_dma_raw(self, values: List[int]):
        self.__set_tdd_channel("dp_", True, True, values)

    @property
    def rx_dma_raw(self) -> List[int]:
        """rx_dma_raw: RX DMA port timing parameters in clock cycles.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("dp_", False, True)

    @rx_dma_raw.setter
    def rx_dma_raw(self, values: List[int]):
        self.__set_tdd_channel("dp_", False, True, values)

    @property
    def tx_dma_ms(self) -> List[int]:
        """tx_dma_ms: TX DMA port timing parameters in ms.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("dp_", True, False)

    @tx_dma_ms.setter
    def tx_dma_ms(self, values: List[int]):
        self.__set_tdd_channel("dp_", True, False, values)

    @property
    def rx_dma_ms(self) -> List[int]:
        """rx_dma_ms: RX DMA port timing parameters in ms.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("dp_", False, False)

    @rx_dma_ms.setter
    def rx_dma_ms(self, values: List[int]):
        self.__set_tdd_channel("dp_", False, False, values)

    @property
    def tx_rf_raw(self) -> List[int]:
        """tx_rf_raw: TX RF port timing parameters in clock cycles.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("", True, True)

    @tx_rf_raw.setter
    def tx_rf_raw(self, values: List[int]):
        self.__set_tdd_channel("", True, True, values)

    @property
    def rx_rf_raw(self) -> List[int]:
        """rx_rf_raw: RX RF port timing parameters in clock cycles.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("", False, True)

    @rx_rf_raw.setter
    def rx_rf_raw(self, values: List[int]):
        self.__set_tdd_channel("", False, True, values)

    @property
    def tx_rf_ms(self) -> List[int]:
        """tx_rf_ms: TX RF port timing parameters in ms.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("", True, False)

    @tx_rf_ms.setter
    def tx_rf_ms(self, values: List[int]):
        self.__set_tdd_channel("", True, False, values)

    @property
    def rx_rf_ms(self) -> List[int]:
        """rx_rf_ms: RX RF port timing parameters in ms.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("", False, False)

    @rx_rf_ms.setter
    def rx_rf_ms(self, values: List[int]):
        self.__set_tdd_channel("", False, False, values)

    @property
    def tx_vco_raw(self) -> List[int]:
        """tx_vco_raw: TX VCO port timing parameters in clock cycles.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("vco_", True, True)

    @tx_vco_raw.setter
    def tx_vco_raw(self, values: List[int]):
        self.__set_tdd_channel("vco_", True, True, values)

    @property
    def rx_vco_raw(self) -> List[int]:
        """rx_vco_raw: RX VCO port timing parameters in clock cycles.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("vco_", False, True)

    @rx_vco_raw.setter
    def rx_vco_raw(self, values: List[int]):
        self.__set_tdd_channel("vco_", False, True, values)

    @property
    def tx_vco_ms(self) -> List[int]:
        """tx_vco_ms: TX VCO port timing parameters in ms.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("vco_", True, False)

    @tx_vco_ms.setter
    def tx_vco_ms(self, values: List[int]):
        self.__set_tdd_channel("vco_", True, False, values)

    @property
    def rx_vco_ms(self) -> List[int]:
        """rx_vco_ms: RX VCO port timing parameters in ms.
        List of four values: [primary_on, primary_off, secondary_on, secondary_off]
        """
        return self.__get_tdd_channel("vco_", False, False)

    @rx_vco_ms.setter
    def rx_vco_ms(self, values: List[int]):
        self.__set_tdd_channel("vco_", False, False, values)
