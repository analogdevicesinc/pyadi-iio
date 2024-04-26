# Copyright (C) 2019-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np
from adi.attribute import attribute


class dds(attribute):
    """ DDS Signal generators: Each reference design contains two DDSs per channel.
        this allows for two complex tones to be generated per complex channel.
    """

    # Set to True if there are multiple DDS drivers (FMComms5)
    _split_cores = False

    def __update_dds(self, attr, value):
        split_cores_indx = 0
        altvoltage_channels = []
        for chan in self._txdac.channels:
            if hasattr(chan, "id") and chan.id.startswith("altvoltage"):
                altvoltage_channels.append(chan.id)
        # Sort channels by name. Names are in the format altvoltageX
        altvoltage_channels.sort(key=lambda x: int(x[10:]))
        if len(value) > len(altvoltage_channels):
            raise Exception(
                f"Number of values ({len(value)}) exceeds number of DDS channels ({len(altvoltage_channels)})"
            )

        if not self._split_cores:
            for i, chan_name in enumerate(altvoltage_channels):
                if i >= len(value):
                    return
                chan = self._txdac.find_channel(chan_name, True)
                if attr == "raw":
                    chan.attrs[attr].value = str(int(value[i]))
                else:
                    chan.attrs[attr].value = str(value[i])
            return
        # old implementation since it handles split cores
        for indx in range(len(self._txdac.channels)):
            chan = self._txdac.find_channel(f"altvoltage{str(indx)}", True)
            # Special FMComms5 case
            if not chan and self._split_cores:
                chan = self._txdac_chip_b.find_channel(
                    f"altvoltage{str(split_cores_indx)}", True
                )
                split_cores_indx = split_cores_indx + 1
            if not chan:
                return
            if indx >= len(value):
                return
            if attr == "raw":
                chan.attrs[attr].value = str(int(value[indx]))
            else:
                chan.attrs[attr].value = str(value[indx])
            indx = indx + 1

    def _read_dds(self, attr):
        values = []
        split_cores_indx = 0

        altvoltage_channels = []
        for chan in self._txdac.channels:
            if hasattr(chan, "id") and chan.id.startswith("altvoltage"):
                altvoltage_channels.append(chan.id)
        # Sort channels by name. Names are in the format altvoltageX
        altvoltage_channels.sort(key=lambda x: int(x[10:]))

        if not self._split_cores:
            for chan_name in altvoltage_channels:
                chan = self._txdac.find_channel(chan_name, True)
                values.append(chan.attrs[attr].value)
            return values

        # old implementation since it handles split cores
        for indx in range(len(self._txdac.channels)):
            chan = self._txdac.find_channel("altvoltage" + str(indx), True)
            if not chan and self._split_cores:
                chan = self._txdac_chip_b.find_channel(
                    "altvoltage" + str(split_cores_indx), True
                )
                split_cores_indx = split_cores_indx + 1
            if not chan:
                continue
            values.append(chan.attrs[attr].value)
            indx = indx + 1
        if values == []:
            return None
        return values

    def disable_dds(self):
        """Disable all DDS channels and set all output sources to zero."""
        self.dds_enabled = np.zeros(self._num_tx_channels * 2, dtype=bool)

    @property
    def dds_frequencies(self):
        """ Frequencies of DDSs in Hz"""
        return self._read_dds("frequency")

    @dds_frequencies.setter
    def dds_frequencies(self, value):
        self.__update_dds("frequency", value)

    @property
    def dds_scales(self):
        """ Scale of DDS signal generators
            Ranges [0,1]
        """
        return self._read_dds("scale")

    @dds_scales.setter
    def dds_scales(self, value):
        self.__update_dds("scale", value)

    @property
    def dds_phases(self):
        """ Phases of DDS signal generators.
            Range in millidegrees [0,360000]
        """
        return self._read_dds("phase")

    @dds_phases.setter
    def dds_phases(self, value):
        self.__update_dds("phase", value)

    @property
    def dds_enabled(self):
        """ DDS generator enable state """
        return self._read_dds("raw")

    @dds_enabled.setter
    def dds_enabled(self, value):
        self.__update_dds("raw", value)

    def dds_single_tone(self, frequency, scale, channel=0):
        """ Generate a single tone using the DDSs
            For complex data devices this will create a complex
            or single sided tone spectrally using two DDSs.
            For non-complex devices the tone will use a single DDS.

            parameters:
                frequency: type=integer
                    Frequency in hertz of the generated tone. This must be
                    less than 1/2 the sample rate.

                scale: type=float
                    Scale of the generated tone in range [0,1]. At 1 the tone
                    will be full-scale.

                channel: type=integer
                    Channel index to generate tone from. This is zero based
                    and for complex devices this index relates to the pair
                    of related converters. For non-complex devices this is
                    the index of the individual converters.

        """
        chans = len(self.dds_scales)
        self.dds_scales = [0] * chans
        self.dds_phases = [0] * chans
        self.dds_enabled = [1] * chans
        # Set up tone
        if self._complex_data:
            if frequency < 0:
                frequency = np.abs(frequency)
                A = "Q"
                B = "I"
            else:
                A = "I"
                B = "Q"
            chan = self._txdac.find_channel(
                "TX" + str(channel + 1) + "_" + A + "_F1", True
            )
            if not chan and self._split_cores:
                chan = self._txdac_chip_b.find_channel(
                    "TX"
                    + str(channel - int(self._num_tx_channels / 4) + 1)
                    + "_"
                    + A
                    + "_F1",
                    True,
                )
            if not chan:
                Exception(f"Cannot find channel {channel}")
            chan.attrs["frequency"].value = str(frequency)
            chan.attrs["phase"].value = str(90000)
            chan.attrs["scale"].value = str(scale)
            chan = self._txdac.find_channel(
                "TX" + str(channel + 1) + "_" + B + "_F1", True
            )
            if not chan and self._split_cores:
                chan = self._txdac_chip_b.find_channel(
                    "TX"
                    + str(channel - int(self._num_tx_channels / 4) + 1)
                    + "_"
                    + B
                    + "_F1",
                    True,
                )
            if not chan:
                Exception(f"Cannot find channel {channel}")
            chan.attrs["frequency"].value = str(frequency)
            chan.attrs["phase"].value = str(0)
            chan.attrs["scale"].value = str(scale)
        else:
            if frequency < 0:
                Exception("Frequency must be positive")
            chan = self._txdac.find_channel(str(channel + 1) + "A", True)
            chan.attrs["frequency"].value = str(frequency)
            chan.attrs["phase"].value = str(0)
            chan.attrs["scale"].value = str(scale)

    def dds_dual_tone(self, frequency1, scale1, frequency2, scale2, channel=0):
        """ Generate two tones simultaneously using the DDSs
            For complex data devices this will create two complex
            or single sided tones spectrally using four DDSs.
            For non-complex devices the tone will use two DDSs.

            parameters:
                frequency1: type=integer
                    Frequency of first tone in hertz of the generated tone.
                    This must be less than 1/2 the sample rate.

                scale1: type=float
                    Scale of the first tone generated tone in range [0,1].
                    At 1 the tone will be full-scale.

                frequency2: type=integer
                    Frequency of second tone in hertz of the generated tone.
                    This must be less than 1/2 the sample rate.

                scale2: type=float
                    Scale of the second tone generated tone in range [0,1].
                    At 1 the tone will be full-scale.

                channel: type=integer
                    Channel index to generate tone from. This is zero based
                    and for complex devices this index relates to the pair
                    of related converters. For non-complex devices this is
                    the index of the individual converters.

        """
        chans = len(self.dds_scales)
        self.dds_scales = [0] * chans
        self.dds_phases = [0] * chans
        self.dds_enabled = [1] * chans
        # Set up tone
        if self._complex_data:
            # Channel 1
            if frequency1 < 0:
                frequency1 = np.abs(frequency1)
                A = "Q"
                B = "I"
            else:
                A = "I"
                B = "Q"
            chan = self._txdac.find_channel(
                "TX" + str(channel + 1) + "_" + A + "_F1", True
            )
            if not chan and self._split_cores:
                chan = self._txdac_chip_b.find_channel(
                    "TX"
                    + str(channel - int(self._num_tx_channels / 4) + 1)
                    + "_"
                    + A
                    + "_F1",
                    True,
                )
            chan.attrs["frequency"].value = str(frequency1)
            chan.attrs["phase"].value = str(90000)
            chan.attrs["scale"].value = str(scale1)
            chan = self._txdac.find_channel(
                "TX" + str(channel + 1) + "_" + B + "_F1", True
            )
            if not chan and self._split_cores:
                chan = self._txdac_chip_b.find_channel(
                    "TX"
                    + str(channel - int(self._num_tx_channels / 4) + 1)
                    + "_"
                    + B
                    + "_F1",
                    True,
                )
            chan.attrs["frequency"].value = str(frequency1)
            chan.attrs["phase"].value = str(0)
            chan.attrs["scale"].value = str(scale1)
            # Channel 2
            if frequency2 < 0:
                frequency2 = np.abs(frequency2)
                A = "Q"
                B = "I"
            else:
                A = "I"
                B = "Q"
            chan = self._txdac.find_channel(
                "TX" + str(channel + 1) + "_" + A + "_F2", True
            )
            if not chan and self._split_cores:
                chan = self._txdac_chip_b.find_channel(
                    "TX"
                    + str(channel - int(self._num_tx_channels / 4) + 1)
                    + "_"
                    + A
                    + "_F2",
                    True,
                )
            chan.attrs["frequency"].value = str(frequency2)
            chan.attrs["phase"].value = str(90000)
            chan.attrs["scale"].value = str(scale2)
            chan = self._txdac.find_channel(
                "TX" + str(channel + 1) + "_" + B + "_F2", True
            )
            if not chan and self._split_cores:
                chan = self._txdac_chip_b.find_channel(
                    "TX"
                    + str(channel - int(self._num_tx_channels / 4) + 1)
                    + "_"
                    + B
                    + "_F2",
                    True,
                )
            chan.attrs["frequency"].value = str(frequency2)
            chan.attrs["phase"].value = str(0)
            chan.attrs["scale"].value = str(scale2)
        else:
            if frequency1 < 0:
                Exception("Frequency must be positive")
            if frequency2 < 0:
                Exception("Frequency must be positive")
            chan = self._txdac.find_channel(str(channel + 1) + "A", True)
            chan.attrs["frequency"].value = str(frequency1)
            chan.attrs["phase"].value = str(0)
            chan.attrs["scale"].value = str(scale1)
            chan = self._txdac.find_channel(str(channel + 1) + "B", True)
            chan.attrs["frequency"].value = str(frequency2)
            chan.attrs["phase"].value = str(0)
            chan.attrs["scale"].value = str(scale2)
