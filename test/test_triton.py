import pytest

hardware = ["fmcomms7"]
classname = "adi.ad9364"


# def test_something():
#     print("here 123")
#
#     assert True
#
# def test_2():
#     print("HERE")

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


@pytest.mark.iio_hardware(hardware)
def test_iio_attr(iio_uri):
    print("iio_uri", iio_uri)