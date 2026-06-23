# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
# Author: Ivan Gil Mercano <ivangil.mercano@analog.com>

import numpy as np

from adi.ad5940 import ad5940
from adi.adg2128 import adg2128
from adi.context_manager import context_manager


class cn0565(ad5940, adg2128, context_manager):

    """The CN0565 class inherits features from both the AD5940 (providing high
    precision in impedance and electrochemical frontend) and the ADG2128
    (enabling arbitrary assignment of force and sense electrodes). '
    These combined functionalities are utilized for Electrical
    Impedance Tomography.

    parameters:
        uri: type=string
            URI of the platform
    """

    _device_name = "cn0565"

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        ad5940.__init__(self)
        adg2128.__init__(self)
        self._switch_sequence = None
        self.add(0x71)
        self.add(0x70)
        self._electrode_count = 8
        self._force_distance = 1
        self._sense_distance = 1
        self.excitation_frequency = 10000

    @property
    def electrode_count(self):
        """electrode_count: Number of electrodes"""
        return self._electrode_count

    @electrode_count.setter
    def electrode_count(self, value):
        self._electrode_count = value

    @property
    def force_distance(self):
        """force_distance: Number of electrodes between forcing electrodes. 1 means they are adjacent"""
        return self._force_distance

    @force_distance.setter
    def force_distance(self, value):
        self._force_distance = value

    @property
    def sense_distance(self):
        """sense_distance: Number of electrodes between sensing electrodes. 1 means they are adjacent"""
        return self._sense_distance

    @sense_distance.setter
    def sense_distance(self, value):
        self._sense_distance = value

    @property
    def switch_sequence(self):
        """switch_sequence: type=np.array
            Sequence of combinations of forcing electrodes and sensing electrodes in the form of
            f+, s+, s-, s+
        """
        seq = 0
        ret = []
        for i in range(self.electrode_count):
            f_plus = i
            f_minus = (i + self.force_distance) % self.electrode_count
            for j in range(self.electrode_count):
                s_plus = j % self.electrode_count
                if s_plus == f_plus or s_plus == f_minus:
                    continue
                s_minus = (s_plus + self.sense_distance) % self.electrode_count
                if s_minus == f_plus or s_minus == f_minus:
                    continue
                ret.append((f_plus, s_plus, s_minus, f_minus))
                seq += 1

        return np.array(ret)

    @property
    def all_voltages(self):
        """all_voltages: type=np.array
            Voltage readings from different electrode combinations
        """
        if self._switch_sequence is None:
            self._switch_sequence = self.switch_sequence

        self.impedance_mode = False
        ret = []
        for seq in self._switch_sequence:
            # reset cross point switch
            self.gpio1_toggle = True

            # set new cross point switch configuration from pregenerated sequence
            self._xline[seq[0]][0] = True
            self._xline[seq[1]][1] = True
            self._xline[seq[2]][2] = True
            self._xline[seq[3]][3] = True

            # read impedance
            s = self.channel["voltage0"].raw
            ret.append([s.real, s.imag])

        return np.array(ret).reshape(len(ret), 2)

    @property
    def electrode_count_available(self):
        """electrode_count_available: type=np.array
            Supported Electrode Counts
        """
        return np.array([8, 16, 32])
