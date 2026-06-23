"""
Unit tests for refactored device classes using device_base pattern.
These tests verify the refactoring maintains correct structure and interfaces.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest

import adi


def channel_definitions(device_class, iio_uri):
    with eval(f"adi.{device_class}(uri=iio_uri)") as dev:
        assert hasattr(dev, "channel"), f"{device_class} missing channel attribute"
        assert isinstance(
            dev.channel, list
        ), f"{device_class} channel attribute is not a list"
        assert len(dev.channel) > 0, f"{device_class} has no channels defined"
        for ch in dev.channel:
            # assert hasattr(
            #     ch, "raw"
            # ), f"{device_class} channel {ch.name} missing raw property"
            assert hasattr(
                ch, "scale"
            ), f"{device_class} channel {ch.name} missing scale property"


@pytest.fixture()
def test_channel_definitions(request):
    yield channel_definitions


@pytest.mark.iio_hardware("ad7124-8")
@pytest.mark.parametrize("device_class", ["ad7124"])
def test_ad7124_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7490")
@pytest.mark.parametrize("device_class", ["ad7490"])
def test_ad7490_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7091r-8")
@pytest.mark.parametrize("device_class", ["ad7091rx"])
def test_ad7091rx_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7770")
@pytest.mark.parametrize("device_class", ["ad777x"])
def test_ad777x_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7405")
@pytest.mark.parametrize("device_class", ["ad7405"])
def test_ad7405_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7134", True)  # Bad emulation file
@pytest.mark.parametrize("device_class", ["ad7134"])
def test_ad7134_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad4020", True)  # Bad emulation file (missing scale value)
@pytest.mark.parametrize("device_class", ["ad4020"])
def test_ad4020_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad4080")
@pytest.mark.parametrize("device_class", ["ad4080"])
def test_ad4080_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad4170")
@pytest.mark.parametrize("device_class", ["ad4170"])
def test_ad4170_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad738x")
@pytest.mark.parametrize("device_class", ["ad738x"])
def test_ad738x_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad405x", True)  # Bad emulation file
@pytest.mark.parametrize("device_class", ["ad405x"])
def test_ad405x_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad4858")
@pytest.mark.parametrize("device_class", ["ad4858"])
def test_ad4858_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad579x")
@pytest.mark.parametrize("device_class", ["ad579x"])
def test_ad579x_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad5754r")
@pytest.mark.parametrize("device_class", ["ad5754r"])
def test_ad5754r_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ltc2314-14", True)
@pytest.mark.parametrize("device_class", ["ltc2314_14"])
def test_ltc2314_14_channel_definitions(
    test_channel_definitions, iio_uri, device_class
):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad5686", True)
@pytest.mark.parametrize("device_class", ["ad5686"])
def test_ad5686_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)


@pytest.mark.iio_hardware("ad7291", True)
@pytest.mark.parametrize("device_class", ["ad7291"])
def test_ad7291_channel_definitions(test_channel_definitions, iio_uri, device_class):
    test_channel_definitions(device_class, iio_uri)
