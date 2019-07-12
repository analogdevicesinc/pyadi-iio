from adi.attribute import attribute
import numpy as np


class dds(attribute):
    """ DDS Signal generators: Each reference design contains two DDSs per channel.
        this allows for two complex tones to be generated per complex channel.
    """

    dds_frequencies = []
    dds_scales = []
    dds_enabled = []

    def __init__(self):
        self.dds_frequencies = np.zeros(self.num_tx_channels * 2)
        self.dds_scales = np.zeros(self.num_tx_channels * 2)
        self.dds_enabled = np.zeros(self.num_tx_channels * 2, dtype=bool)

    def update_dds(self, attr, value):
        indx = 0
        for chan in self.txdac.channels:
            if not chan.name:
                continue
            if attr == 'raw':
                chan.attrs[attr].value = str(int(value[indx]))
            else:
                chan.attrs[attr].value = str(value[indx])
            indx = indx + 1

    def read_dds(self, attr):
        values = []
        indx = 0
        for chan in self.txdac.channels:
            if not chan.name:
                continue
            values.append(chan.attrs[attr].value)
            indx = indx + 1
        return values

    def disable_dds(self):
        self.dds_enabled = np.zeros(self.num_tx_channels * 2, dtype=bool)

    @property
    def dds_frequencies(self):
        """ Frequencies of DDSs in Hz"""
        return self.read_dds("frequency")

    @dds_frequencies.setter
    def dds_frequencies(self, value):
        self.update_dds("frequency", value)

    @property
    def dds_scales(self):
        """ Scale of DDS signal generators"""
        return self.read_dds("scale")

    @dds_scales.setter
    def dds_scales(self, value):
        self.update_dds("scale", value)

    @property
    def dds_enabled(self):
        """ DDS generator enable state """
        return self.read_dds("raw")

    @dds_enabled.setter
    def dds_enabled(self, value):
        self.update_dds("raw", value)
