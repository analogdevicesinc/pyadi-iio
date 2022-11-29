import pytest
import iio
import adi

hardware = "adrv9009-dual-fmcomms8"
classname = "adi.adrv9009_zu11eg_fmcomms8"


##################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "voltage_raw, low, high",
    [
        ("in_temp0", 20, 50),
        ("in_voltage0", 2064, 2179),
        ("in_voltage1", 2064, 2179),
        ("in_voltage2", 2867, 3031),
        ("in_voltage3", 2867, 3031),
        ("in_voltage4", 2654, 2736),
        ("in_voltage5", 2654, 2736),
        ("in_voltage6", 2654, 2736),
        ("in_voltage7", 2654, 2736),
    ],
)
def test_ad7291(context_desc, voltage_raw, low, high):
    ctx = None
    for ctx_desc in context_desc:
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
                        #calculate celsius temp from raw
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
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx_hardwaregain_chan0_chip_c", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1_chip_c", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan0_chip_d", -41.95, 0.0, 0.05, 0.05),
        ("tx_hardwaregain_chan1_chip_d", -41.95, 0.0, 0.05, 0.05),
        ("trx_lo_chip_c", 70000000, 6000000000, 1000, 0),
        ("trx_lo_chip_d", 70000000, 6000000000, 1000, 0),
    ],
)
def test_adrv9009_zu11eg_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [4, 5, 6, 7])
def test_adrv9009_zu11eg_rx_data(test_dma_rx, iio_uri, classname, channel):
    test_dma_rx(iio_uri, classname, channel)


############################# CHIP C #############################
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [4, 5])
@pytest.mark.parametrize("frequency, scale, sfdr1_min, sfdr2_min", [(4001311, 0.1, 29, 60)])
@pytest.mark.parametrize(
    "param_set, low, high",
    [
        (
            dict(
                trx_lo_chip_c=1000000000,
                trx_lo_chip_d=5000000000,
                gain_control_mode_chan0_chip_c="slow_attack",
                gain_control_mode_chan1_chip_c="slow_attack",
                gain_control_mode_chan0_chip_d="slow_attack",
                gain_control_mode_chan1_chip_d="slow_attack",
                tx_hardwaregain_chan0_chip_c=-10,
                tx_hardwaregain_chan1_chip_c=-10,
                tx_hardwaregain_chan0_chip_d=-10,
                tx_hardwaregain_chan1_chip_d=-10,
                calibrate_rx_qec_en_chip_c=1,
                calibrate_tx_qec_en_chip_c=1,
                calibrate_chip_c=1,
                calibrate_rx_qec_en_chip_d=1,
                calibrate_tx_qec_en_chip_d=1,
                calibrate_chip_d=1,
                ),
            [-22.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0],
            [-18.0, -64.0, -70.0, -90.0, -90.0, -90.0, -90.0, -90.0],
        ),
        (
            dict(
                trx_lo_chip_c=3000000000,
                trx_lo_chip_d=4000000000,
            ),
            [-25.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0],
            [-21.0, -53.0, -57.0, -90.0, -90.0, -90.0, -90.0, -90.0],
        ),
        (
            dict(
                trx_lo_chip_c=5000000000,
                trx_lo_chip_d=1000000000,
            ),
            [-27.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0],
            [-23.0, -52.0, -85.0, -90.0, -90.0, -90.0, -90.0, -90.0],
        ),
    ],
)
def test_adrv9009_zu11eg_sfdrl(
    test_sfdrl, iio_uri, classname, channel, param_set, low, high, sfdr1_min, sfdr2_min, frequency, scale
):
    print("")
    print("Configuration channel:", channel, "(chip c)")
    print("LO chip C: ", param_set["trx_lo_chip_c"], "LO chip D:", param_set["trx_lo_chip_d"])
    print("Frequency ", frequency, "and scale ", scale)
    print("")
    test_sfdrl(classname, iio_uri, channel, param_set, low, high, sfdr1_min, sfdr2_min, frequency, scale, plot=True)

############################# CHIP D #############################
#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [6, 7])
@pytest.mark.parametrize("frequency, scale, sfdr1_min, sfdr2_min", [(4001311, 0.1, 29, 60)])
@pytest.mark.parametrize(
    "param_set, low, high",
    [
        (
            dict(
                trx_lo_chip_c=5000000000,
                trx_lo_chip_d=1000000000,
                gain_control_mode_chan0_chip_c="slow_attack",
                gain_control_mode_chan1_chip_c="slow_attack",
                gain_control_mode_chan0_chip_d="slow_attack",
                gain_control_mode_chan1_chip_d="slow_attack",
                tx_hardwaregain_chan0_chip_c=-10,
                tx_hardwaregain_chan1_chip_c=-10,
                tx_hardwaregain_chan0_chip_d=-10,
                tx_hardwaregain_chan1_chip_d=-10,
                calibrate_rx_qec_en_chip_c=1,
                calibrate_tx_qec_en_chip_c=1,
                calibrate_chip_c=1,
                calibrate_rx_qec_en_chip_d=1,
                calibrate_tx_qec_en_chip_d=1,
                calibrate_chip_d=1,
                ),
            [-22.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0],
            [-18.0, -70.0, -70.0, -82.0, -90.0, -90.0, -90.0, -90.0],
        ),
        (
            dict(
                trx_lo_chip_c=3000000000,
                trx_lo_chip_d=4000000000,
            ),
            [-25.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0],
            [-21.0, -53.0, -78.0, -90.0, -90.0, -90.0, -90.0, -90.0],
        ),
        (
            dict(
                trx_lo_chip_c=1000000000,
                trx_lo_chip_d=5000000000,
            ),
            [-27.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0],
            [-23.0, -52.0, -84.0, -90.0, -90.0, -90.0, -90.0, -90.0],
        ),
    ],
)
def test_adrv9009_zu11eg_sfdrl_chipd(
    test_sfdrl, iio_uri, classname, channel, param_set, low, high, sfdr1_min, sfdr2_min, frequency, scale
):
    print("")
    print("Configuration channel:", channel, "(chip d)")
    print("LO chip C: ", param_set["trx_lo_chip_c"], "LO chip D:", param_set["trx_lo_chip_d"])
    print("Frequency ", frequency, "and scale ", scale)
    print("")
    test_sfdrl(classname, iio_uri, channel, param_set, low, high, sfdr1_min, sfdr2_min, frequency, scale, plot=True)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [4, 5, 6, 7])
@pytest.mark.parametrize("dds_scale, min_rssi, max_rssi", [(0, 35, 60), (0.9, 0, 22)])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            trx_lo_chip_c=1000000000,
            trx_lo_chip_d=5000000000,
            gain_control_mode_chan0_chip_c="slow_attack",
            gain_control_mode_chan1_chip_c="slow_attack",
            gain_control_mode_chan0_chip_d="slow_attack",
            gain_control_mode_chan1_chip_d="slow_attack",
            rx_hardwaregain_chan0_chip_c=0,
            rx_hardwaregain_chan1_chip_c=0,
            rx_hardwaregain_chan0_chip_d=0,
            rx_hardwaregain_chan1_chip_d=0,
            tx_hardwaregain_chan0_chip_c=-10,
            tx_hardwaregain_chan1_chip_c=-10,
            tx_hardwaregain_chan0_chip_d=-10,
            tx_hardwaregain_chan1_chip_d=-10,
            calibrate_tx_qec_en_chip_c=1,
            calibrate_tx_qec_en_chip_d=1,
            calibrate_chip_c=1,
            calibrate_chip_d=1,
        ),
        dict(
            trx_lo_chip_c=5000000000,
            trx_lo_chip_d=1000000000,
        ),
    ],
)
def test_adrv9009_zu11eg_dds_gain_check_vary_power(
    test_gain_check,
    iio_uri,
    classname,
    channel,
    param_set,
    dds_scale,
    min_rssi,
    max_rssi,
):
    test_gain_check(
        iio_uri, classname, channel, param_set, dds_scale, min_rssi, max_rssi
    )

