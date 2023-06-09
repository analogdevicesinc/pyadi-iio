# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import math

import adi


class adpd2140_gesture_sensor(adi.adpd1080):
    """ADPD2140 gesture sensing class."""

    _L0_thresh = 1000
    _L1_thresh = 1000
    _d0_thresh = 0.07
    _d1_thresh = 0.07

    g0_incr = 0
    g1_incr = 0
    has_gest0 = False
    has_gest1 = False
    algo_time0 = False
    algo_time1 = False

    avg = [0, 0, 0, 0, 0, 0, 0, 0]

    def __init__(
        self, uri="", device_index=0, adpd2140_0=[0, 1, 2, 3], adpd2140_1=[4, 5, 6, 7]
    ):
        """ADPD1080 class constructor."""
        adi.adpd1080.__init__(self, uri)

        self._adpd2140_0 = adpd2140_0
        self._adpd2140_1 = adpd2140_1

    def gain_calibration(self):
        for _ in range(5):
            data = self.rx()
            for idx, val in enumerate(data):
                self.avg[idx] += val.sum()
        self.avg = [int(x / 5) for x in self.avg]

    #        for i in range(8):
    #            self.channel[i].offset = self.channel[i].offset + avg[i]

    @property
    def L0_thresh(self):
        return self._L0_thresh

    @L0_thresh.setter
    def L0_thresh(self, value):
        self._L0_thresh = value

    @property
    def L1_thresh(self):
        return self._L1_thresh

    @L1_thresh.setter
    def L1_thresh(self, value):
        self._L1_thresh = value

    @property
    def d0_thresh(self):
        return self._d0_thresh

    @d0_thresh.setter
    def d0_thresh(self, value):
        self._d0_thresh = value

    @property
    def d1_thresh(self):
        return self._d1_thresh

    @d1_thresh.setter
    def d1_thresh(self, value):
        self._d1_thresh = value

    def get_gesture_0(self):
        data = self.rx()
        for i in range(4):
            data[i] -= min(data[i], self.avg[i])

        L0 = (
            data[self._adpd2140_0[0]].sum()
            + data[self._adpd2140_0[1]].sum()
            + data[self._adpd2140_0[2]].sum()
            + data[self._adpd2140_0[3]].sum()
        )

        if L0 > self.L0_thresh and not self.has_gest0:
            self.has_gest0 = True
            self.start_x0 = (
                int(data[self._adpd2140_0[1]].sum())
                - int(data[self._adpd2140_0[0]].sum())
            ) / (
                int(data[self._adpd2140_0[1]].sum())
                + int(data[self._adpd2140_0[0]].sum())
            )
            self.start_y0 = (
                int(data[self._adpd2140_0[3]].sum())
                - int(data[self._adpd2140_0[2]].sum())
            ) / (
                int(data[self._adpd2140_0[3]].sum())
                + int(data[self._adpd2140_0[2]].sum())
            )
            return -1

        if L0 < self.L0_thresh and self.has_gest0 and self.g0_incr >= 5:
            self.has_gest0 = False
            try:
                self.end_x0 = (
                    int(data[self._adpd2140_0[1]].sum())
                    - int(data[self._adpd2140_0[0]].sum())
                ) / (
                    int(data[self._adpd2140_0[1]].sum())
                    + int(data[self._adpd2140_0[0]].sum())
                )
                self.end_y0 = (
                    int(data[self._adpd2140_0[3]].sum())
                    - int(data[self._adpd2140_0[2]].sum())
                ) / (
                    int(data[self._adpd2140_0[3]].sum())
                    + int(data[self._adpd2140_0[2]].sum())
                )
            except ZeroDivisionError:
                self.end_x0 = 0.000001
                self.end_y0 = 0.000001
            self.algo_time0 = True

        if self.algo_time0:
            self.algo_time0 = False
            m = (self.start_y0 - self.end_y0) / (self.start_x0 - self.end_x0 + 0.000001)
            d = math.sqrt(
                (self.start_x0 - self.end_x0) ** 2 + (self.start_y0 - self.end_y0) ** 2
            )
            if d < self.d0_thresh:
                return 0
            else:
                if abs(m) > 1:
                    if self.start_y0 < self.end_y0:
                        return 1
                    else:
                        return 2
                elif abs(m) < 1:
                    if self.start_x0 > self.end_x0:
                        return 3
                    else:
                        return 4
                else:
                    return 0

        if L0 >= self.L0_thresh:
            self.g0_incr += 1
            return -1
        else:
            self.g0_incr = 0
            return -1

    def get_gesture_1(self):
        data = self.rx()
        for i in range(4):
            data[i + 4] -= min(data[i + 4], self.avg[i + 4])

        L1 = (
            data[self._adpd2140_1[0]].sum()
            + data[self._adpd2140_1[1]].sum()
            + data[self._adpd2140_1[2]].sum()
            + data[self._adpd2140_1[3]].sum()
        )

        if L1 > self.L1_thresh and not self.has_gest1:
            self.has_gest1 = True
            self.start_x1 = (
                int(data[self._adpd2140_1[1]].sum())
                - int(data[self._adpd2140_1[0]].sum())
            ) / (
                int(data[self._adpd2140_1[1]].sum())
                + int(data[self._adpd2140_1[0]].sum())
            )
            self.start_y1 = (
                int(data[self._adpd2140_1[3]].sum())
                - int(data[self._adpd2140_1[2]].sum())
            ) / (
                int(data[self._adpd2140_1[3]].sum())
                + int(data[self._adpd2140_1[2]].sum())
            )
            return -1

        if L1 < self.L1_thresh and self.has_gest1 and self.g1_incr >= 5:
            self.has_gest1 = False
            try:
                self.end_x1 = (
                    int(data[self._adpd2140_1[1]].sum())
                    - int(data[self._adpd2140_1[0]].sum())
                ) / (
                    int(data[self._adpd2140_1[1]].sum())
                    + int(data[self._adpd2140_1[0]].sum())
                )
                self.end_y1 = (
                    int(data[self._adpd2140_1[3]].sum())
                    - int(data[self._adpd2140_1[2]].sum())
                ) / (
                    int(data[self._adpd2140_1[3]].sum())
                    + int(data[self._adpd2140_1[2]].sum())
                )
            except ZeroDivisionError:
                self.end_x1 = 0.000001
                self.end_y1 = 0.000001
            self.algo_time1 = True

        if self.algo_time1:
            self.algo_time1 = False
            m = (self.start_y1 - self.end_y1) / (self.start_x1 - self.end_x1 + 0.000001)
            d = math.sqrt(
                (self.start_x1 - self.end_x1) ** 2 + (self.start_y1 - self.end_y1) ** 2
            )
            if d < self.d1_thresh:
                return 0
            else:
                if abs(m) > 1:
                    if self.start_y1 < self.end_y1:
                        return 1
                    else:
                        return 2
                elif abs(m) < 1:
                    if self.start_x1 > self.end_x1:
                        return 3
                    else:
                        return 4
                else:
                    return 0

        if L1 >= self.L1_thresh:
            self.g1_incr += 1
            return -1
        else:
            self.g1_incr = 0
            return -1


if __name__ == "__main__":

    adpd1080 = adpd2140_gesture_sensor(uri="serial:COM4")
    adpd1080.rx_buffer_size = 8
    # adpd1080.sample_rate = 512
    adpd1080.gain_calibration()

    gestures = [
        "CLICK_0",
        "UP_0",
        "DOWN_0",
        "LEFT_0",
        "RIGHT_0",
        "CLICK_1",
        "UP_1",
        "DOWN_1",
        "LEFT_1",
        "RIGHT_1",
    ]

    while True:
        gesture0 = adpd1080.get_gesture_0()
        gesture1 = adpd1080.get_gesture_1()
        if gesture0 >= 0:
            print(gestures[gesture0])
        if gesture1 >= 0:
            print(gestures[gesture1 + 4])
