import iio
import adi
import pytest

hardware = "daq3"
classname = "adi.DAQ3"


##################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "voltage_raw, low, high",
    [
        ("in_temp0", 20, 50),
        ("in_voltage0", 3101, 3265),
        ("in_voltage1", 2540, 2867),
        ("in_voltage2", 2540, 2867),
        ("in_voltage3", 1229, 1393),
        ("in_voltage4", 1884, 2179),
        ("in_voltage5", 2458, 2876),
        ("in_voltage6", 1966, 5734),
        ("in_voltage7", 2540, 2867),
    ],
)
def test_ad7291(context_desc, voltage_raw, low, high):
    ctx = None
    for ctx_desc in context_desc:
        if ctx_desc["hw"] == "adrv9361":
            pytest.skip("ad7291 not tested for SOM")
        if ctx_desc["hw"] in hardware:
            ctx = iio.Context(ctx_desc["uri"])
    if not ctx:
        pytest.skip("No valid hardware found")

    ad7291 = ctx.find_device("ad7291")

    for channel in ad7291.channels:
        c_name = "out" if channel.output else "in"
        c_name += "_" + str(channel.id)
        if c_name == voltage_raw:
            for attr in channel.attrs:
                if attr == "raw":
                    if c_name == "in_temp0":
                        temp = (2.5 * (int(channel.attrs[attr].value)/10 + 109.3) - 273.15)
                        print(temp)
                        assert low <= temp <= high
                    else:
                        try:
                            print(channel.attrs[attr].value)
                            assert low <= int(channel.attrs[attr].value) <= high
                        except OSError:
                            continue


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
def test_daq3_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency, scale",
    [
        (
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                sample_rate=1233333333,
            ),
            97014318,
            1,
        ),
        (
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                sample_rate=1233333333,
            ),
            169996185,
            1,
        ),
        (
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                sample_rate=1233333333,
            ),
            185014114,
            1,
        ),
    ],
)
@pytest.mark.parametrize(
    "low, high",
    [([-15.0, -150.0, -150.0, -150.0, -150.0, -150.0], [0.0, -67.0, -55.0, -72.0, -54.0, -74.0])],
)
def test_harmonic_values(
    test_harmonics, classname, iio_uri, channel, param_set, low, high, frequency, scale, plot=True
):
    test_harmonics(classname, iio_uri, channel, param_set, low, high, frequency, scale, plot)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set, frequency, scale",
    [
        (
            dict(
                tx_lo=2400000000,
                rx_lo=2400000000,
                sample_rate=1233333333,
            ),
            97014318,
            0.0
        ),
    ],
)
@pytest.mark.parametrize(
    "low, high",
    [([-120.0, -120.0, -120.0, -120.0, -120.0, -120.0, -120.0], [-50, -50.0, -50.0, -90.0, -90.0, -90.0, -90.0])],
)
def test_peaks(
    test_sfdrl, classname, iio_uri, channel, param_set, low, high, frequency, scale, plot=True
):
    test_sfdrl(classname, iio_uri, channel, param_set, low, high, frequency, scale, plot)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("masterfile", [("AD-FMCDAQ3-EBZ.bin")])
@pytest.mark.parametrize("eeprom_path", [("/sys/devices/soc0/fpga-axi@0/41600000.i2c/i2c-0/i2c-6/6-0050/eeprom")])
def test_write_eeprom(
    test_save_eeprom, iio_uri, snumber, masterfile, eeprom_path
):
    test_save_eeprom(iio_uri, snumber, masterfile, eeprom_path)
