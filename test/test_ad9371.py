import pytest

hardware = "ad9371"
classname = "adi.ad9371"


#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain_chan0", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1", -41.95, 0.0, 0.05, 0.05),
        ("rx_lo", 70000000, 6000000000, 1000, 0),
        ("rx_lo", 70000000, 6000000000, 1000, 0),
    ],
)
def test_ad9371_attr(
    test_attribute_single_value, classname, hardware, attr, start, stop, step, tol
):
    test_attribute_single_value(classname, hardware, attr, start, stop, step, tol)

#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", range(2))
def test_ad9371_rx_data(test_dma_rx, classname, hardware, channel):
    test_dma_rx(classname, hardware, channel)

#########################################
@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0])
@pytest.mark.parametrize("frequency", [2000000])
@pytest.mark.parametrize("scale", [0.9])
@pytest.mark.parametrize("peak_min", [-50])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            rx_lo=1000000000,
            tx_lo=1000000000,
            rx_enabled_dec8=False
        )
    ],
)
def test_ad9371_dds_loopback(
    test_dds_loopback, classname, hardware, param_set, channel, frequency, scale, peak_min
):
    test_dds_loopback(classname, hardware, param_set, channel, frequency, scale, peak_min
)
