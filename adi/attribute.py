# Copyright (C) 2019 Analog Devices, Inc.
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

import re
from abc import abstractproperty
from enum import Enum
from typing import List

import iio

from adi.context_manager import ContextManager


class IO(Enum):
    OUTPUT = True
    INPUT = False


def add_dev(devname):
    """ Generate property for IIO device """
    return property(lambda self: self._ctx.find_device(devname))
    # return lambda self: self._ctx.find_device(devname)


class devattr:
    def __init__(self, attr, dev):
        self._dev = dev
        self._attr = attr

    def __get__(self, instance, owner):
        return instance._get_iio_dev_attr(self._attr, self._dev)

    def __set__(self, instance, value):
        instance._set_iio_dev_attr_str(self._attr, value, self._dev)


def get_numbers(string):
    """ Convert string to number """
    val = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", string)
    val = [float(i) for i in val]
    if len(val) == 1:
        val = val[0]
        if int(val) == val:
            val = int(val)
    return val


class Attribute(ContextManager):
    """ IIO Attribute interfaces """

    _ctrls = None

    @abstractproperty
    def _ctrl_names(self) -> List[str]:
        pass

    @abstractproperty
    def _ctrl(self) -> iio.Device:
        pass

    def __new__(cls, **kwargs):
        uri = kwargs.get("uri")
        if not uri:
            uri = ""
        instance = super(Attribute, cls).__new__(cls)
        ContextManager.__init_cc__(instance, uri, instance._device_name)
        Attribute.__init_attr__(instance)
        # __init__ of youngest child will get called on return
        return instance

    def __init_attr__(self):
        if not isinstance(self._ctrl_names, list):
            name_list = [self._ctrl_names]
        else:
            name_list = self._ctrl_names
        self._ctrls = [self._ctx.find_device(name) for name in name_list]

    def _find_device(self, dev_name):
        d = self._ctx.find_device(dev_name)
        if not d:
            raise Exception(dev_name + " not found")
        return d

    def _set_iio_attr_vec(self, channel_name, attr_name, output, values, _ctrls=None):
        """ Set channel Attribute at multiple devices """
        if not _ctrls:
            _ctrls = self._ctrls
        assert len(_ctrls) == len(
            values
        ), "Number of IIO devices must be same as input list"
        for i, _ctrl in enumerate(_ctrls):
            self._set_iio_attr(channel_name, attr_name, output, values[i], _ctrl)

    def _set_iio_attr(self, channel_name, attr_name, output, value, _ctrl=None):
        """ Set channel Attribute """
        if _ctrl:
            channel = _ctrl.find_channel(channel_name, output)
        else:
            channel = self._ctrl.find_channel(channel_name, output)
        try:
            channel.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _set_iio_attr_float_vec(
        self, channel_name, attr_name, output, values, _ctrls=None
    ):
        """ Set channel Attribute with float at multiple devices """
        if not _ctrls:
            _ctrls = self._ctrls
        if not isinstance(_ctrls, list):
            _ctrls = [_ctrls]
        assert len(_ctrls) == len(
            values
        ), "Number of IIO devices must be same as input list"
        for i, _ctrl in enumerate(_ctrls):
            self._set_iio_attr_int(channel_name, attr_name, output, values[i], _ctrl)

    def _set_iio_attr_float(self, channel_name, attr_name, output, value, _ctrl=None):
        """ Set channel Attribute with float """
        if isinstance(value, int):
            value = float(value)
        if not isinstance(value, float):
            raise Exception("Value must be a float")
        self._set_iio_attr(channel_name, attr_name, output, value, _ctrl)

    def _set_iio_attr_int_vec(
        self, channel_name, attr_name, output, values, _ctrls=None
    ):
        """ Set channel Attribute with int at multiple devices """
        if not _ctrls:
            _ctrls = self._ctrls
        if not isinstance(_ctrls, list):
            _ctrls = [_ctrls]
        assert len(_ctrls) == len(
            values
        ), "Number of IIO devices must be same as input list"
        for i, _ctrl in enumerate(_ctrls):
            self._set_iio_attr_int(channel_name, attr_name, output, values[i], _ctrl)

    def _set_iio_attr_int(self, channel_name, attr_name, output, value, _ctrl=None):
        """ Set channel Attribute with int """
        if not isinstance(value, int):
            raise Exception("Value must be an int")
        self._set_iio_attr(channel_name, attr_name, output, value, _ctrl)

    def _get_iio_attr_str(self, channel_name, attr_name, output, _ctrl=None):
        """ Get channel Attribute as string """
        if _ctrl:
            channel = _ctrl.find_channel(channel_name, output)
        else:
            channel = self._ctrl.find_channel(channel_name, output)
        return channel.attrs[attr_name].value

    def _get_iio_attr_vec(self, channel_name, attr_name, output, _ctrls=None):
        """ Get vector of channel Attributes as numbers """
        if not _ctrls:
            _ctrls = self._ctrls
        if not isinstance(_ctrls, list):
            _ctrls = [_ctrls]
        vec = [
            get_numbers(self._get_iio_attr_str(channel_name, attr_name, output, _ctrl))
            for _ctrl in _ctrls
        ]
        if len(vec) == 1:
            vec = vec[0]
        return vec

    def _get_iio_attr(self, channel_name, attr_name, output, _ctrl=None):
        """ Get channel Attribute as number """
        return get_numbers(
            self._get_iio_attr_str(channel_name, attr_name, output, _ctrl)
        )

    def _set_iio_dev_attr_str(self, attr_name, value, _ctrl=None):
        """ Set device Attribute with string """
        try:
            if _ctrl:
                _ctrl.attrs[attr_name].value = str(value)
            else:
                self._ctrl.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _get_iio_dev_attr_str(self, attr_name, _ctrl=None):
        """ Get device Attribute as string """
        if _ctrl:
            return _ctrl.attrs[attr_name].value
        return self._ctrl.attrs[attr_name].value

    def _get_iio_dev_attr(self, attr_name, _ctrl=None):
        """ Set device Attribute as number """
        return get_numbers(self._get_iio_dev_attr_str(attr_name, _ctrl))

    def _set_iio_debug_attr_str(self, attr_name, value, _ctrl=None):
        """ Set debug Attribute with string """
        try:
            if _ctrl:
                _ctrl.debug_attrs[attr_name].value = str(value)
            else:
                self._ctrl.debug_attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _get_iio_debug_attr_str(self, attr_name, _ctrl=None):
        """ Get debug Attribute as string """
        if _ctrl:
            return _ctrl.debug_attrs[attr_name].value
        return self._ctrl.debug_attrs[attr_name].value

    def _get_iio_debug_attr(self, attr_name, _ctrl=None):
        """ Set debug Attribute as number """
        return get_numbers(self._get_iio_debug_attr_str(attr_name, _ctrl))
