import pytest

import adi


@pytest.mark.iio_hardware("daq2")
def test_daq2(iio_uri):
    dev = adi.DAQ2(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware("daq3")
def test_daq3(iio_uri):
    dev = adi.DAQ3(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware(["fmcomms2", "ad9361"])
def test_ad9361(iio_uri):
    dev = adi.ad9361(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware("fmcomms4")
def test_ad9364(iio_uri):
    dev = adi.ad9364(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware("fmcomms5")
def test_fmcomms5(iio_uri):
    dev = adi.FMComms5(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware("pluto")
def test_pluto(iio_uri):
    dev = adi.Pluto(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware("ad9081")
def test_ad9081(iio_uri):
    dev = adi.ad9081(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware("adrv9002")
def test_adrv9002(iio_uri):
    dev = adi.adrv9002(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware("adrv9009")
def test_adrv9009(iio_uri):
    dev = adi.adrv9009(iio_uri)
    assert dev
    del dev


@pytest.mark.iio_hardware("adrv9371")
def test_ad9371(iio_uri):
    dev = adi.ad9371(iio_uri, disable_jesd_control=True)
    assert dev
    del dev


@pytest.mark.iio_hardware("adxl345")
def test_adxl345(iio_uri):
    dev = adi.adxl345(iio_uri)
    assert dev
    del dev
