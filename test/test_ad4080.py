import pytest

hardware = ["ad4080"]
classname = ["adi.ad4080"]


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0])
def test_ad4080_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


# #########################################
# @pytest.mark.iio_hardware(hardware)
# @pytest.mark.parametrize("classname", [(classname)])
# @pytest.mark.parametrize(
#     "attr, val",
#     [
#         (
#             "test_mode",
#             [
#                 "off",
#                 "midscale_short",
#                 "pos_fullscale",
#                 "neg_fullscale",
#                 "checkerboard",
#                 "pn_long",
#                 "pn_short",
#                 "one_zero_toggle",
#                 "user",
#                 "bit_toggle",
#                 "sync",
#                 "one_bit_high",
#                 "mixed_bit_frequency",
#             ],
#         ),
#     ],
# )
# def test_ad4080_attr(test_attribute_multipe_values, iio_uri, classname, attr, val):
#     test_attribute_multipe_values(iio_uri, classname, attr, val, 0)
