# Copyright (C) 2023 Analog Devices, Inc.
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

import iio
import pytest

from examples.swiot import swiot_utils, constants


@pytest.mark.parametrize("runtime_devices", [
    ["swiot", "ad74413r", "max14906", "adt75", "ad74413r-dev0", "sw_trig"]
])
def test_runtime_devices(runtime_devices):
    swiot = swiot_utils.get_runtime_swiot(uri=constants.URI)

    devices: [iio.Device] = swiot.ctx.devices
    device_names = [device.name for device in devices]

    # check that every device from constants.py is present in the config context
    for device in runtime_devices:
        assert device in device_names
        device_names.remove(device)

    # check that there are no extra devices added
    assert not device_names


@pytest.mark.parametrize("trigger_name", ["ad74413r-dev0"])
@pytest.mark.parametrize("ad74413r_name", ["ad74413r"])
def test_ad74413r_trigger(trigger_name, ad74413r_name):
    swiot_utils.get_runtime_swiot(uri=constants.URI)

    context = iio.Context(constants.URI)
    trigger: iio.Trigger | None = None
    ad74413r: iio.Device | None = None

    for device in context.devices:
        if device.name == trigger_name:
            trigger = device
        if device.name == ad74413r_name:
            ad74413r = device

    assert trigger is not None, F"Trigger trigger with name {trigger_name} could not be found in SWIOT trigger list"
    assert ad74413r is not None, F"Trigger device with name {ad74413r_name} could not be found in SWIOT devices list"

    ad74413r.trigger = trigger