# Copyright (C) 2020 Analog Devices, Inc.
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
        self._complex_data = complex_data
        rx.__init__(self)

    def __del__(self):
        rx.__del__(self)


class tx_two(tx):
    """ Buffer Handling for secondary transmit channels """

    def __init__(self, ctx, obs_dev, channel_names, complex_data=True):
        self._ctx = ctx
        self._txdac = obs_dev
        self._tx_channel_names = channel_names
        self._complex_data = complex_data
        tx.__init__(self)

    def __del__(self):
        tx.__del__(self)
