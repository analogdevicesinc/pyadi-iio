import adi
# mcs=$(iio_attr -d adrv9002-phy multi_chip_sync)
# ​
# [ ${mcs} != 3 ] && echo "MCS is not done after 6 pulses..."
# ​
# iio_attr -c adrv9002-phy -i voltage0 ensm_mode rf_enabled
# iio_attr -c adrv9002-phy -i voltage1 ensm_mode rf_enabled
# iio_attr -c adrv9002-phy -o voltage0 ensm_mode rf_enabled
# iio_attr -c adrv9002-phy -o voltage1 ensm_mode rf_enabled
# iio_attr -c adrv9002-phy  altvoltage2 TX1_LO_frequency 2500000000

sdr = adi.adrv9002(uri="ip:analog.local")
mcs = sdr._ctrl.attrs["multi_chip_sync"].value

if mcs != '3':
    print("MCS is not done after 6 pulses...")

sdr.rx_ensm_mode_chan0 = "rf_enabled"
sdr.rx_ensm_mode_chan1 = "rf_enabled"
sdr.tx_ensm_mode_chan0 = "rf_enabled"
sdr.tx_ensm_mode_chan1 = "rf_enabled"

sdr.tx0_lo = int(2.5e9)