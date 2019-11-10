from test.core import *


class TestAD9361(CoreTests):
    # a map specifying multiple argument sets for a test method
    params = {
        "test_attribute_single_value": [
            dict(
                devname="adi.ad9361",
                attr="tx_hardwaregain",
                start=-89.75,
                stop=0.0,
                step=0.25,
                tol=0,
            ),
            dict(
                devname="adi.ad9361",
                attr="rx_lo",
                start=70000000,
                stop=6000000000,
                step=1,
                tol=8,
            ),
        ],
        "test_attribute_single_value_str": [
            dict(devname="adi.ad9361", attr="loopback", val=2, tol=0),
            dict(devname="adi.ad9361", attr="loopback", val=1, tol=0),
            dict(devname="adi.ad9361", attr="loopback", val=0, tol=0),
        ],
        "test_dma": [dict(devname="adi.ad9361", channel=0)],
    }
    devicename = "packrf"


class TestAD9361DSP(DSPTests):
    # a map specifying multiple argument sets for a test method
    params = {
        "test_iq_loopback": [
            dict(
                devname="adi.ad9361",
                channel=0,
                param_set=dict(
                    tx_lo=1000000000,
                    rx_lo=1000000000,
                    gain_control_mode="slow_attack",
                    tx_hardwaregain=-30,
                    sample_rate=4000000,
                ),
            ),
            dict(
                devname="adi.ad9361",
                channel=1,
                param_set=dict(
                    tx_lo=1000000000,
                    rx_lo=1000000000,
                    gain_control_mode="slow_attack",
                    tx_hardwaregain=-30,
                    sample_rate=4000000,
                ),
            ),
        ]
    }
    devicename = "packrf"
