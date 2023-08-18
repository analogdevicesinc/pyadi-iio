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
from time import sleep

@pytest.mark.parametrize(
    "configuration, set_value, expected_value, measurement",
    [
        [
            [
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [0, 0], [0, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [1, 0], [0, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"]
            ], [2, 0], [0, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"]
            ], [3, 0], [0, 30], "voltage"
        ],


        [
            [
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [0, 1342], [1342, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [1, 1342], [1342, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"]
            ], [2, 1342], [1342, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"]
            ], [3, 1342], [1342, 30], "voltage"
        ],


        [
            [
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [0, 5371], [5371, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [1, 5371], [5371, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"]
            ], [2, 5371], [5371, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"]
            ], [3, 5371], [5371, 30], "voltage"
        ],


        [
            [
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [0, 10000], [10000, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [1, 10000], [10000, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"]
            ], [2, 10000], [10000, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"]
            ], [3, 10000], [10000, 30], "voltage"
        ],


        [
            [
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [0, 10998], [10000, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"]
            ], [1, 10998], [10000, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"],
                ["ad74413r", "voltage_in"]
            ], [2, 10998], [10000, 30], "voltage"
        ],

        [
            [
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_in"],
                ["ad74413r", "voltage_out"]
            ], [3, 10998], [10000, 30], "voltage"
        ],


        [
            [
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[0, 0], [0, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[1, 0], [0, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"]
            ],[1, 0], [0, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"]
            ],[2, 0], [0, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"]
            ],[3, 0], [0, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"]
            ],[2, 0], [0, 0.1], "current"
        ],

        

        [
            [
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[0, 3.05], [3.05, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[1, 3.05], [3.05, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"]
            ],[1, 3.05], [3.05, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"]
            ],[2, 3.05], [3.05, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"]
            ],[3, 3.05], [3.05, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"]
            ],[2, 3.05], [3.05, 0.1], "current"
        ],



        [
            [
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[0, 12.21], [12.21, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[1, 12.21], [12.21, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"]
            ],[1, 12.21], [12.21, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"]
            ],[2, 12.21], [12.21, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"]
            ],[3, 12.21], [12.21, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"]
            ],[2, 12.21], [12.21, 0.1], "current"
        ],



        [
            [
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[0, 24.41], [24.41, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[1, 24.41], [24.41, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"]
            ],[1, 24.41], [24.41, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"]
            ],[2, 24.41], [24.41, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"]
            ],[3, 24.41], [24.41, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"]
            ],[2, 24.41], [24.41, 0.1], "current"
        ],



        [
            [
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[0, 24.99], [24.99, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"]
            ],[1, 24.99], [24.99, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "high_z"]
            ],[1, 24.99], [24.99, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"],
                ["ad74413r", "high_z"]
            ],[2, 24.99], [24.99, 0.1], "current"
        ],

        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_in_ext"],
                ["ad74413r", "current_out"]
            ],[3, 24.99], [24.99, 0.1], "current"
        ],
        [
            [
                ["ad74413r", "high_z"],
                ["ad74413r", "high_z"],
                ["ad74413r", "current_out"],
                ["ad74413r", "current_in_ext"]
            ],[2, 24.99], [24.99, 0.1], "current"
        ],
    ]
)
def test_ad74413r_loopback(configuration: list, set_value: list, expected_value: list, measurement: str):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    ad74413r = adi.ad74413r(uri=constants.URI)

    dac_ch_index = set_value[0]
    dac_ch_name = measurement + str(dac_ch_index)
    dac_scale = ad74413r.channel[dac_ch_name].scale
    dac_offset = ad74413r.channel[dac_ch_name].offset
    dac_raw = set_value[1] / dac_scale - dac_offset
    ad74413r.channel[dac_ch_name].raw = dac_raw

    expected = expected_value[0]
    limit = expected_value[1]

    for i in range(4):
        if i == dac_ch_index:
            continue

        adc_ch_name = measurement + str(i)
        if adc_ch_name not in ad74413r._rx_channel_names:
            continue

        adc_raw = ad74413r.channel[adc_ch_name].raw
        adc_scale = ad74413r.channel[adc_ch_name].scale
        adc_offset = ad74413r.channel[adc_ch_name].offset
        adc_val = (adc_raw + adc_offset) * adc_scale

        assert (adc_val >= expected - limit) and (adc_val <= expected + limit)


@pytest.mark.parametrize(
    "configuration",
    [
        [
            ["max14906", "input"],
            ["max14906", "output"],
            ["max14906", "input"],
            ["max14906", "input"]
        ],

        [
            ["max14906", "input"],
            ["max14906", "input"],
            ["max14906", "output"],
            ["max14906", "input"]
        ],

        [
            ["max14906", "input"],
            ["max14906", "input"],
            ["max14906", "input"],
            ["max14906", "output"]
        ],
    ]
)
def test_max14906_loopback(configuration: list):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    max14906 = adi.max14906(uri=constants.URI)

    out_ch = 0
    for i in range(len(configuration)):
        if configuration[i][1] == "output":
            break
        
        out_ch = out_ch + 1

    max14906.channel["voltage" + str(out_ch)].raw = 1

    for i in range(4):
        if i == out_ch:
            continue

        assert max14906.channel["voltage" + str(i)].raw == 1

