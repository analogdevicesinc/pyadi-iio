import iio
import pytest
from os.path import dirname, realpath
from random import randint
from numpy import floor

hardware = "adrv9002"
classname = "adi.adrv9002"
profile_path = dirname(realpath(__file__)) + "/adrv9002_profiles/"
nco_test_profile = profile_path + "lte_10_lvds_nco_api_68_0_6.json"
nco_test_stream = profile_path + "lte_10_lvds_nco_api_68_0_6.stream"
lte_20_lvds_profile = profile_path + "lte_20_lvds_api_68_0_6.json"
lte_20_lvds_stream = profile_path + "lte_20_lvds_api_68_0_6.stream"
lte_40_lvds_profile = profile_path + "lte_40_lvds_api_68_0_6.json"
lte_40_lvds_stream = profile_path + "lte_40_lvds_api_68_0_6.stream"
lte_5_cmos_profile = profile_path + "lte_5_cmos_api_68_0_6.json"
lte_5_cmos_stream = profile_path + "lte_5_cmos_api_68_0_6.stream"

def random_values_in_range(start, stop, step, to_generate=1):
    """random_values_in_range:
    Generate random values in range
    This is performed a defined number of times and the value written
    is randomly determined based in input parameters

    parameters:
        start: type=integer
            Lower bound of possible values attribute can be
        stop: type=integer
            Upper bound of possible values attribute can be
        step: type=integer
            Difference between successive values attribute can be
        to_generate: type=integer
            Number of random values to tests. Generated from uniform distribution
    """
    # Pick random number in operational range
    values = []
    for _ in range(to_generate):
        numints = int((stop - start) / step)
        ind = randint(0, numints)
        val = start + step * ind
        if isinstance(val, float):
            val = floor(val / step) * step
        values.append(val)
    return values

#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, start, stop, step, tol",
    [
        ("tx0_lo", 30000000, 6000000000, 1, 8),
        ("tx1_lo", 30000000, 6000000000, 1, 8),
        ("rx0_lo", 30000000, 6000000000, 1, 8),
        ("rx1_lo", 30000000, 6000000000, 1, 8),
    ],
)
def test_adrv9002_float_attr(
    test_attribute_single_value, iio_uri, classname, attr, start, stop, step, tol
):
    test_attribute_single_value(iio_uri, classname, attr, start, stop, step, tol)


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val, depends",
    [
        (
            "rx_hardwaregain_chan0",
            random_values_in_range(0, 34, 0.5, 10),
            dict(gain_control_mode_chan0="spi", rx_ensm_mode_chan0="rf_enabled",),
        ),
        (
            "rx_hardwaregain_chan0",
            random_values_in_range(0, 34, 0.5, 10),
            dict(gain_control_mode_chan1="spi", rx_ensm_mode_chan1="rf_enabled",),
        ),
        (
            "tx_hardwaregain_chan0",
            random_values_in_range(-40, 0, 0.05, 10),
            dict(atten_control_mode_chan0="spi"),
        ),
        (
            "tx_hardwaregain_chan1",
            random_values_in_range(-40, 0, 0.05, 10),
            dict(atten_control_mode_chan1="spi"),
        ),
    ],
)
def test_adrv9002_hardware_gain(
    test_attribute_multipe_values_with_depends, iio_uri, classname, attr, depends, val
):
    test_attribute_multipe_values_with_depends(
        iio_uri, classname, attr, depends, val, 0.0000001
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            tx0_lo=1000000000,
            rx0_lo=1000000000,
            tx1_lo=1000000000,
            rx1_lo=1000000000,
            rx_ensm_mode_chan0="rf_enabled",
            rx_ensm_mode_chan1="rf_enabled",
            digital_gain_control_mode_chan0="automatic",
            digital_gain_control_mode_chan1="automatic",
            gain_control_mode_chan0="automatic",
            gain_control_mode_chan1="automatic",
            tx_hardwaregain_chan0=-20,
            tx_hardwaregain_chan1=-20,
            tx_ensm_mode_chan0="rf_enabled",
            tx_ensm_mode_chan1="rf_enabled",
        )
    ],
)
@pytest.mark.parametrize("use_tx2rx2", [False, True])
def test_adrv9002_cw_loopback_split_dma(
    test_cw_loopback, iio_uri, classname, channel, param_set, use_tx2rx2
):
    import adi

    sdr = adi.adrv9002(iio_uri)
    # it's safe to only look at TX as we cannot TX in MIMO and RX in split mode
    if sdr._tx_dma_mode == "combined" and use_tx2rx2:
        pytest.skip("Combined DMA mode does not have RX2/TX2 ADC/DDS")
    elif sdr._tx_dma_mode == "split" and channel > 0:
        pytest.skip("Split DMA mode does not have more than one channel per ADC/DDS")

    test_cw_loopback(iio_uri, classname, channel, param_set, use_tx2rx2, use_tx2rx2)

@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("frequency, scale, sfdr1_min, sfdr2_min", [(1999952, 0.1, 30, 60)])
@pytest.mark.parametrize(
    "channel, param_set, low, high, rxtx2",
    [
        (
	    0,
            dict(
                tx0_lo=2400000000,
                rx0_lo=2400000000,
                tx1_lo=2400000000,
                rx1_lo=2400000000,
                # rx_ensm_mode_chan0="rf_enabled",
                # rx_ensm_mode_chan1="rf_enabled",
                # digital_gain_control_mode_chan0="automatic",
                # digital_gain_control_mode_chan1="automatic",
                # gain_control_mode_chan0="automatic",
                # gain_control_mode_chan1="automatic",
                # tx_hardwaregain_chan0=-10,
                # tx_hardwaregain_chan1=-10,
                # tx_ensm_mode_chan0="rf_enabled",
                # tx_ensm_mode_chan1="rf_enabled",
            ),
            [-35.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0],
            [-9.0, -52.0, -61.0, -80.0, -80.0, -85.0, -85.0, -85.0],
            False,
        ),
        (
	    1,
            dict(
                tx0_lo=2400000000,
                rx0_lo=2400000000,
                tx1_lo=2400000000,
                rx1_lo=2400000000,
                # rx1_rf_bandwidth=18000000,
                # tx1_rf_bandwidth=18000000,
                # rx1_sample_rate=30720000,
                # tx1_sample_rate=30720000,
                # rx_ensm_mode_chan0="rf_enabled",
                # rx_ensm_mode_chan1="rf_enabled",
                # digital_gain_control_mode_chan0="automatic",
                # digital_gain_control_mode_chan1="automatic",
                # gain_control_mode_chan0="automatic",
                # gain_control_mode_chan1="automatic",
                # tx_hardwaregain_chan0=-10,
                # tx_hardwaregain_chan1=-10,
                # tx_ensm_mode_chan0="rf_enabled",
                # tx_ensm_mode_chan1="rf_enabled",
            ),
            [-35.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0, -150.0],
            [-9.0, -52.0, -61.0, -80.0, -80.0, -85.0, -85.0, -85.0],
            True,
        ),
    ],
)
def test_adrv9002_sfdr(
    context_desc, test_sfdrl, classname, iio_uri, channel, param_set, low, high, sfdr1_min, sfdr2_min, frequency, scale, rxtx2
):
    print("")
    print("Configuration channel:", channel)
    # print("LO chip A: ", param_set["tx0_lo"], "LO chip B:", param_set["tx1_lo"])
    print("Frequency ", frequency, "and scale ", scale)
    print("")
    # ctx = None
    # for ctx_desc in context_desc:
    #     if ctx_desc["hw"] in hardware:
    #         ctx = iio.Context(ctx_desc["uri"])
    # phy = ctx.find_device("adrv9002-phy")
    # tx1_ch = phy.find_channel("voltage0", True)
    # tx2_ch = phy.find_channel("voltage1", True)
    # rx1adc = ctx.find_device("axi-adrv9002-rx-lpc")
    # rx2adc = ctx.find_device("axi-adrv9002-rx2-lpc")  # RX/ADC Core in HDL for DMA
    # tx1dac = ctx.find_device("axi-adrv9002-tx-lpc")  # TX/DAC Core in HDL for DMA (plus DDS)
    # tx2dac = ctx.find_device("axi-adrv9002-tx2-lpc")
    # rx1_ch = phy.find_channel("voltage0")
    # rx1_ch.attrs['agc_tracking_en'].value = str(1)
    # rx1_ch.attrs['bbdc_rejection_en'].value = str(1)
    # rx1_ch.attrs['bbdc_rejection_tracking_en'].value = str(1)
    # rx1_ch.attrs['quadrature_fic_tracking_en'].value = str(1)
    # rx1_ch.attrs['en'].value = str(int(1))

    # v0_i = rx1adc.find_channel("voltage0_i")
    # v0_q = rx1adc.find_channel("voltage0_q")
    # v1_i = rx2adc.find_channel("voltage0_i")
    # v1_q = rx2adc.find_channel("voltage0_q")
    # if channel == 0:
    #     v0_i.enabled = True
    #     v0_q.enabled = True
    #     v1_i.enabled = False
    #     v1_q.enabled = False
    # elif channel == 1:
    #     v0_i.enabled = False
    #     v0_q.enabled = False
    #     v1_i.enabled = True
    #     v1_q.enabled = True

    
    # tx1_ch.attrs['hardwaregain'].value = str(int(0))
    # tx1_ch.attrs['lo_leakage_tracking_en'].value = str(0)
    # tx1_ch.attrs['quadrature_tracking_en'].value = str(0)
    # tx1_ch.attrs["en"].value = str(int(1))

    # tx2_ch.attrs['hardwaregain'].value = str(int(0))
    # tx2_ch.attrs['lo_leakage_tracking_en'].value = str(0)
    # tx2_ch.attrs['quadrature_tracking_en'].value = str(0)
    # tx2_ch.attrs["en"].value = str(int(1))

    # tx1_i_f1 = tx1dac.find_channel('altvoltage0', True)
    # tx1_i_f2 = tx1dac.find_channel('altvoltage1', True)
    # tx1_q_f1 = tx1dac.find_channel('altvoltage2', True)
    # tx1_q_f2 = tx1dac.find_channel('altvoltage3', True)
    # tx2_i_f1 = tx2dac.find_channel('altvoltage0', True)
    # tx2_i_f2 = tx2dac.find_channel('altvoltage1', True)
    # tx2_q_f1 = tx2dac.find_channel('altvoltage2', True)
    # tx2_q_f2 = tx2dac.find_channel('altvoltage3', True)

    # tx1_i_f1.attrs["raw"].value = str(int(0))
    # tx1_q_f1.attrs["raw"].value = str(int(0))
    # tx1_i_f2.attrs["raw"].value = str(int(0))
    # tx1_q_f2.attrs["raw"].value = str(int(0))
    # tx2_i_f1.attrs["raw"].value = str(int(0))
    # tx2_q_f1.attrs["raw"].value = str(int(0))
    # tx2_i_f2.attrs["raw"].value = str(int(0))
    # tx2_q_f2.attrs["raw"].value = str(int(0))

    # if channel == 0:
    #     tx1_i_f1.attrs["frequency"].value = str(frequency)
    #     tx1_i_f1.attrs["scale"].value = str(scale)
    #     tx1_i_f1.attrs["phase"].value = "90000"
    #     tx1_i_f1.attrs["frequency"].value = str(frequency)
    #     tx1_q_f1.attrs["scale"].value = str(scale)
    #     tx1_q_f1.attrs["phase"].value = "0"
    #     tx1_i_f2.attrs["frequency"].value = "2000000"
    #     tx1_i_f2.attrs["scale"].value = "0.0"
    #     tx1_q_f2.attrs["frequency"].value = "2000000"
    #     tx1_q_f2.attrs["scale"].value = "0.0"
    #     tx2_i_f1.attrs["scale"].value = "0.0"
    #     tx2_q_f1.attrs["scale"].value = "0.0"

    #     # Enable I/Q channels to be associated with TX
    #     tx1_i_f1.attrs["raw"].value = str(int(1))
    #     tx1_q_f1.attrs["raw"].value = str(int(1))

    # if channel == 1:  # maybe tx
    #     print ('TX2 DDS config')
    #     tx2_i_f1.attrs["frequency"].value = str(frequency)
    #     tx2_i_f1.attrs["scale"].value = str(scale) # "0.1" = -20dBFS, "0.031616 = -30dBFS = -20dBm"
    #     tx2_i_f1.attrs["phase"].value = "90000"
    #     tx2_q_f1.attrs["frequency"].value = str(frequency)
    #     tx2_q_f1.attrs["scale"].value = str(scale)
    #     tx2_q_f1.attrs["phase"].value = "0"
    #     tx2_i_f2.attrs["frequency"].value = "2000000"
    #     tx2_i_f2.attrs["scale"].value = "0.0"
    #     tx2_q_f2.attrs["frequency"].value = "2000000"
    #     tx2_q_f2.attrs["scale"].value = "0.0"

    #     tx1_i_f1.attrs["scale"].value = "0.0"
    #     tx1_q_f1.attrs["scale"].value = "0.0"

    #     # Enable I/Q channels to be associated with TX
    #     tx2_i_f1.attrs["raw"].value = str(int(1))
    #     tx2_q_f1.attrs["raw"].value = str(int(1))

    test_sfdrl(classname, iio_uri, channel, param_set, low, high, sfdr1_min, sfdr2_min, frequency, scale, rxtx2, plot=True)

#########################################
# @pytest.mark.cmos_test
# @pytest.mark.iio_hardware(hardware)
# def test_adrv9002_stream_profile_write_both(iio_uri):
#     import adi

#     sdr = adi.adrv9002(iio_uri)
#     sdr.write_stream_profile(lte_5_cmos_stream, lte_5_cmos_profile)