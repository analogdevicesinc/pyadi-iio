import adi
import pytest

hardware = "adrv9009-dual"
classname = "adi.adrv9009_zu11eg"


#########################################
# @pytest.mark.obs_required
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3])
@pytest.mark.parametrize("frequency, scale, sfdr1_min, sfdr2_min", [(4001311, 0.1, 30, 60)])
@pytest.mark.parametrize(
    "low, high",
    [([-24.0, -120.0, -120.0, -120.0, -120.0], [-21.0, -20.0, -30.0, -40.0, -40.0])],
)
@pytest.mark.parametrize(
    "param_set",
    [
        dict(
            ensm_mode="radio_on",
            trx_lo=2500000000,
            trx_lo_chip_b=2500000000,
            rx_powerdown_en_chan0=1,
            rx_powerdown_en_chan1=1,
            rx_powerdown_en_chan0_chip_b=1,
            rx_powerdown_en_chan1_chip_b=1,
            obs_powerdown_en=0,
            obs_powerdown_en_chan1=0,
            obs_powerdown_en_chip_b=0,
            obs_powerdown_en_chan1_chip_b=0,
            tx_hardwaregain_chan0=-10,
            tx_hardwaregain_chan1=-10,
            tx_hardwaregain_chan0_chip_b=-10,
            tx_hardwaregain_chan1_chip_b=-10,
            aux_obs_lo=2500000000,
            obs_rf_port_select="OBS_TX_LO",
        ),
    ],
)
def test_adrv9009_zu11eg_sfdr_for_obs(
    test_sfdrl, classname, iio_uri, channel, param_set, low, high, sfdr1_min, sfdr2_min, frequency, scale
):
    print("")
    print("Configuration channel:", channel)
    print("LO chip A: ", param_set["trx_lo"], "LO chip B:", param_set["trx_lo_chip_b"])
    print("Frequency ", frequency, "and scale ", scale)
    print("")
    test_sfdrl(
        classname, iio_uri, channel, param_set, low, high, sfdr1_min, sfdr2_min, frequency, scale, plot=True, use_obs=True
    )
