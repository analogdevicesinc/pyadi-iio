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
    v = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", s)
    v = [float(i) for i in v]
    if len(v) == 1:
        v = v[0]
        if int(v) == v:
            v = int(v)
    return v


class attribute:
    def _set_iio_attr(self, channel_name, attr_name, output, value, _ctrl=None):
        if _ctrl:
            channel = _ctrl.find_channel(channel_name, output)
        else:
            channel = self._ctrl.find_channel(channel_name, output)
        try:
            channel.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _get_iio_attr_str(self, channel_name, attr_name, output, _ctrl=None):
        if _ctrl:
            channel = _ctrl.find_channel(channel_name, output)
        else:
            channel = self._ctrl.find_channel(channel_name, output)
        return channel.attrs[attr_name].value

    def _get_iio_attr(self, channel_name, attr_name, output, _ctrl=None):
        return get_numbers(
            self._get_iio_attr_str(channel_name, attr_name, output, _ctrl)
        )

    def _set_iio_dev_attr_str(self, attr_name, value, _ctrl=None):
        try:
            if _ctrl:
                _ctrl.attrs[attr_name].value = str(value)
            else:
                self._ctrl.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def _get_iio_dev_attr(self, attr_name, _ctrl=None):
        if _ctrl:
            return _ctrl.attrs[attr_name].value
        else:
            return self._ctrl.attrs[attr_name].value
