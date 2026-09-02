# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from adi.rx_tx import rx, tx


class _property_remap:
    def __init__(self, attr, dev):
        self._dev = dev
        self._attr = attr

    def __get__(self, instance, owner):
        return getattr(self._dev, self._attr)

    def __set__(self, instance, value):
        setattr(self._dev, self._attr, value)


def remap(object_source, old, new, classname):
    """ Remap methods to new names to different object """

    method_list = [
        func
        for func in dir(object_source)
        if not func.startswith("__") and not func.startswith("_")
    ]
    for method in method_list:
        if old not in method:
            continue
        new_method = method.replace(old, new)
        setattr(
            classname, new_method, _property_remap(method, object_source),
        )


class obs(rx):
    """ Buffer handling for observation devices """

    def __init__(self, ctx, obs_dev, channel_names, complex_data=True):
        self._ctx = ctx
        self._rxadc = obs_dev
        self._rx_channel_names = channel_names
        self._rx_complex_data = complex_data
        rx.__init__(self)

    def __del__(self):
        rx.__del__(self)


class tx_two(tx):
    """ Buffer Handling for secondary transmit channels """

    def __init__(self, ctx, obs_dev, channel_names, complex_data=True):
        self._ctx = ctx
        self._txdac = obs_dev
        self._tx_channel_names = channel_names
        self._tx_complex_data = complex_data
        tx.__init__(self)

    def __del__(self):
        tx.__del__(self)
