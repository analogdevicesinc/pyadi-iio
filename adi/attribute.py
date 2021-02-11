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


def get_numbers(s):
    v = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", s)
    v = [float(i) for i in v]
    if len(v) == 1:
        v = v[0]
        if int(v) == v:
            v = int(v)
    return v


class attribute:
    def _get_iio_attr_str_multi_dev(self, channel_names, attr_name, output, ctrls):
        """ Get the same channel attribute across multiple devices
            which are assumed to be strings
        """
        if not isinstance(channel_names, list):
            channel_names = [channel_names]
        return {
            ctrl.name: [
                self._get_iio_attr_str(chan_name, attr_name, output, ctrl)
                for chan_name in channel_names
            ]
            for ctrl in ctrls
        }

    def _set_iio_attr_multi_dev(self, channel_names, attr_name, output, values, ctrls):
        """ Set the same channel attribute across multiple devices
            Unique parameters:
                values: type=list
                    Must be of length <= len(ctrls)*len(channel_names)
        """
        if len(values) > len(ctrls) * len(channel_names):
            raise Exception("Too many values to write")
        i = 0
        for ctrl in ctrls:
            for chan_name in channel_names:
                self._set_iio_attr(chan_name, attr_name, output, values[i], ctrl)
                i += 1

    def _set_iio_attr_float_multi_dev(
        self, channel_names, attr_name, output, values, ctrls
    ):
        """ Set the same float channel attribute(s) across multiple devices
            Unique parameters:
                values: type=list
                    Must be of length <= len(ctrls)*len(channel_names)
        """
        for i, value in enumerate(values):
            if isinstance(value, int):
                values[i] = float(value)
            if not isinstance(values[i], float):
                raise Exception("Values must be floats")
        self._set_iio_attr_multi_dev(channel_names, attr_name, output, values, ctrls)

    def _set_iio_attr(self, channel_name, attr_name, output, value, _ctrl=None):
        """ Set channel attribute """
        if _ctrl:
            channel = _ctrl.find_channel(channel_name, output)
        else:
            channel = self._ctrl.find_channel(channel_name, output)
        try:
            channel.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _set_iio_attr_float(self, channel_name, attr_name, output, value, _ctrl=None):
        """ Set channel attribute with float """
        if isinstance(value, int):
            value = float(value)
        if not isinstance(value, float):
            raise Exception("Value must be a float")
        self._set_iio_attr(channel_name, attr_name, output, value, _ctrl)

    def _set_iio_attr_float_vec(
        self, channel_names, attr_name, output, values, _ctrl=None
    ):
        """ Set channel attribute with list of floats """
        if not isinstance(values, list):
            raise Exception("Value must be a list")
        for i, v in enumerate(values):
            self._set_iio_attr_float(channel_names[i], attr_name, output, v, _ctrl)

    def _set_iio_attr_int(self, channel_name, attr_name, output, value, _ctrl=None):
        """ Set channel attribute with int """
        if not isinstance(value, int):
            raise Exception("Value must be an int")
        self._set_iio_attr(channel_name, attr_name, output, value, _ctrl)

    def _set_iio_attr_int_vec(
        self, channel_names, attr_name, output, values, _ctrl=None
    ):
        """ Set channel attribute with list of ints """
        if not isinstance(values, list):
            raise Exception("Value must be a list")
        for i, v in enumerate(values):
            self._set_iio_attr_int(channel_names[i], attr_name, output, v, _ctrl)

    def _get_iio_attr_str(self, channel_name, attr_name, output, _ctrl=None):
        """ Get channel attribute as string """
        if _ctrl:
            channel = _ctrl.find_channel(channel_name, output)
        else:
            channel = self._ctrl.find_channel(channel_name, output)
        if not channel:
            raise Exception("No channel found with name: " + channel_name)
        return channel.attrs[attr_name].value

    def _get_iio_attr(self, channel_name, attr_name, output, _ctrl=None):
        """ Get channel attribute as number """
        return get_numbers(
            self._get_iio_attr_str(channel_name, attr_name, output, _ctrl)
        )

    def _get_iio_attr_vec(self, channel_names, attr_name, output, _ctrl=None):
        """ Get channel attributes as list of numbers """
        vals = []
        for chn in channel_names:
            v = self._get_iio_attr(chn, attr_name, output, _ctrl)
            vals.append(v)
        return vals

    def _set_iio_dev_attr_str(self, attr_name, value, _ctrl=None):
        """ Set device attribute with string """
        try:
            if _ctrl:
                _ctrl.attrs[attr_name].value = str(value)
            else:
                self._ctrl.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _get_iio_dev_attr_str(self, attr_name, _ctrl=None):
        """ Get device attribute as string """
        if _ctrl:
            return _ctrl.attrs[attr_name].value
        else:
            return self._ctrl.attrs[attr_name].value

    def _set_iio_dev_attr(self, attr_name, value, _ctrl=None):
        """ Set device attribute """
        _dev = _ctrl or self._ctrl
        try:
            _dev.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _get_iio_dev_attr(self, attr_name, _ctrl=None):
        """ Set device attribute as number """
        return get_numbers(self._get_iio_dev_attr_str(attr_name, _ctrl))

    def _set_iio_debug_attr_str(self, attr_name, value, _ctrl=None):
        """ Set debug attribute with string """
        try:
            if _ctrl:
                _ctrl.debug_attrs[attr_name].value = str(value)
            else:
                self._ctrl.debug_attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _get_iio_debug_attr_str(self, attr_name, _ctrl=None):
        """ Get debug attribute as string """
        if _ctrl:
            return _ctrl.debug_attrs[attr_name].value
        else:
            return self._ctrl.debug_attrs[attr_name].value

    def _get_iio_debug_attr(self, attr_name, _ctrl=None):
        """ Set debug attribute as number """
        return get_numbers(self._get_iio_debug_attr_str(attr_name, _ctrl))
