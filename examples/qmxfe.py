import adi

sdr = adi.QuadMxFE(uri="ip:10.72.162.37")

sdr.rx_channel_nco_frequencies_chip_a = [10]*4
sdr.rx_channel_nco_frequencies_chip_b = [20]*4
sdr.rx_channel_nco_frequencies_chip_c = [30]*4
sdr.rx_channel_nco_frequencies_chip_d = [40]*4

sdr.tx_channel_nco_frequencies_chip_a = [40]*4
sdr.tx_channel_nco_frequencies_chip_b = [30]*4
sdr.tx_channel_nco_frequencies_chip_c = [20]*4
sdr.tx_channel_nco_frequencies_chip_d = [10]*4

print(sdr.rx_test_mode_chip_a)

# Read registers
reg = 0x01
for offset in range(10):
    print(sdr._rxadc.reg_read(reg+offset))
    print(sdr._txdac.reg_read(reg+offset))
