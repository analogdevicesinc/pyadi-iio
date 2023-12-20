
import adi
import pytest
import matplotlib.pyplot as plt
import numpy as np
from test.test_ad9084 import scale_field


hardware = ["Triton"]
classname = "adi.Triton"



## Set DSA and Filters

adi.ad9084_mc._set_iio_attr(channel_name="voltage0", attr_name="hardwaregain", output=True, value=0)

# adi.Triton._get_iio_attr()

# def test_something():
#     print("here 123")

#     assert True 


# def test_2():
#     print("HERE")
#     return

# @pytest.mark.parametrize(
#     "in1, in2, in3",
#     [
#         (1,"A",20),
#         (2,"B",20),
#         ("D", 10, 1),
#     ],
# )
# @pytest.mark.parametrize("v1, v2", [(1,"A"),(2,"B")])
# def test_p(in1, in2, in3, v1, v2):
#     print(in1,in2,in3, v1,v2)


##########################################

def test_iio_attr(iio_uri):
    print("iio_uri", iio_uri)


# #########################################
# @pytest.mark.iio_hardware(hardware, True)
# @pytest.mark.parametrize("classname", [(classname)])
# @pytest.mark.parametrize("channel", [0])
# def test_Triton_rx_data(test_dma_rx, iio_uri, classname, channel):
#     test_dma_rx(iio_uri, classname, channel)


# #########################################
# # @pytest.mark.iio_hardware(hardware)
# @pytest.mark.parametrize("classname", [(classname)])
# @pytest.mark.parametrize("channel", [0])
# def test_Triton_tx_data(test_dma_tx, iio_uri, classname, channel):
#     test_dma_tx(iio_uri, classname, channel)


#########################################
# DDS Loopback Test 
#########################################

@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
@pytest.mark.parametrize("frequency, scale", [(10000000, 0.5)])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx_main_nco_frequencies=[10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000],
            rx_main_nco_frequencies=[-2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000],
            tx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            rx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            tx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            rx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            tx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            rx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
    ],
)



@pytest.mark.parametrize("peak_min", [-30])
def test_ad9084_dds_loopback(
    test_dds_loopback,
    iio_uri,
    classname,
    param_set,
    channel,
    frequency,
    scale,
    peak_min,
):
    param_set = scale_field(param_set, iio_uri)
    test_dds_loopback(
        iio_uri, classname, param_set, channel, frequency, scale, peak_min
    )

# adi.Triton.rx_dsa_gain(15)
# adi.Triton.rx_main_nco_frequencies



