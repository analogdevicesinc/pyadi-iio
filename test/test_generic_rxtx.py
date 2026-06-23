import iio
import pytest

import adi

hardware = ["pluto", "adrv9361", "fmcomms2"]
classname = ""

#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_generic_rx(iio_uri):
    class MyAD9361(adi.rx_tx.rx_tx_def):
        _complex_data = True
        _control_device_name = "ad9361-phy"
        _rx_data_device_name = "cf-ad9361-lpc"
        _tx_data_device_name = "cf-ad9361-dds-core-lpc"

        def __post_init__(self):
            pass

    dev = MyAD9361(iio_uri)
    dev.rx()
    assert dev._rxadc
    assert dev._txdac
    assert dev._ctrl


#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_generic_rx_with_ctx(iio_uri):
    class MyAD9361(adi.rx_tx.rx_tx_def):
        _complex_data = True
        _control_device_name = "ad9361-phy"
        _rx_data_device_name = "cf-ad9361-lpc"
        _tx_data_device_name = "cf-ad9361-dds-core-lpc"

        def __post_init__(self):
            pass

    ctx = iio.Context(iio_uri)

    dev = MyAD9361(ctx)
    dev.rx()
    assert dev._rxadc
    assert dev._txdac
    assert dev._ctrl


#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_generic_rx_pv_old(iio_uri):
    class MyAD9361(adi.rx_tx.rx_tx_def):
        _complex_data = True
        _control_device_name = "ad9361-phy"
        _rx_data_device_name = "cf-ad9361-lpc"
        _tx_data_device_name = "cf-ad9361-dds-core-lpc"

        def __post_init__(self):
            pass

    dev = MyAD9361(uri=iio_uri)
    dev.rx()
    assert dev._rxadc
    assert dev._txdac
    assert dev._ctrl


#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_generic_rx_pv(iio_uri):
    class MyAD9361(adi.rx_tx.rx_tx_def):
        _complex_data = True
        _control_device_name = "ad9361-phy"
        _rx_data_device_name = "cf-ad9361-lpc"
        _tx_data_device_name = "cf-ad9361-dds-core-lpc"

        def __post_init__(self):
            pass

    dev = MyAD9361(uri_ctx=iio_uri)
    dev.rx()
    assert dev._rxadc
    assert dev._txdac
    assert dev._ctrl


#########################################
@pytest.mark.iio_hardware(hardware, True)
def test_generic_rx_with_ctx_pv(iio_uri):
    class MyAD9361(adi.rx_tx.rx_tx_def):
        _complex_data = True
        _control_device_name = "ad9361-phy"
        _rx_data_device_name = "cf-ad9361-lpc"
        _tx_data_device_name = "cf-ad9361-dds-core-lpc"

        def __post_init__(self):
            pass

    ctx = iio.Context(iio_uri)

    dev = MyAD9361(uri_ctx=ctx)
    dev.rx()
    assert dev._rxadc
    assert dev._txdac
    assert dev._ctrl
