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

import pytest
import adi
from examples.swiot import swiot_utils, constants


@pytest.mark.parametrize(
    "configuration",
    [[
        ["ad74413r", "digital_input"],
        ["ad74413r", "digital_input"],
        ["ad74413r", "digital_input_loop"],
        ["ad74413r", "digital_input_loop"]
    ]]
)
def test_switch_config_runtime_threshold(configuration: list):
    """
    Test that the threshold steps are set correctly and that all channels change their threshold once one of them
    changes it
    :param configuration:
    """
    swiot_utils.setup_config_mode(configuration=configuration)

    # reconnect to the new context
    ad74413r = adi.ad74413r(uri=constants.URI)

    # test that the value of threshold is propagated across all channels
    ad74413r.channel["voltage0"].threshold = 552
    assert ad74413r.channel["voltage1"].threshold == 551
    assert ad74413r.channel["voltage2"].threshold == 551
    assert ad74413r.channel["voltage3"].threshold == 551

    ad74413r.channel["voltage1"].threshold = 1104
    assert ad74413r.channel["voltage0"].threshold == 1103
    assert ad74413r.channel["voltage2"].threshold == 1103
    assert ad74413r.channel["voltage3"].threshold == 1103

    ad74413r.channel["voltage2"].threshold = 552
    assert ad74413r.channel["voltage1"].threshold == 551
    assert ad74413r.channel["voltage0"].threshold == 551
    assert ad74413r.channel["voltage3"].threshold == 551

    ad74413r.channel["voltage3"].threshold = 1104
    assert ad74413r.channel["voltage1"].threshold == 1103
    assert ad74413r.channel["voltage2"].threshold == 1103
    assert ad74413r.channel["voltage0"].threshold == 1103

    # test 2 random threshold steps
    ad74413r.channel["voltage0"].threshold = 700
    assert ad74413r.channel["voltage0"].threshold == 551
