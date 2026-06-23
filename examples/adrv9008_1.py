# Copyright (C) 2019-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

sdr = adi.adrv9008_1(uri="ip:localhost")

sdr.ensm_mode = "radio_on"
print("ensm_mode: " + sdr.ensm_mode)
sdr.rx_powerdown_en_chan0 = 0
print("rx_powerdown_chan0: " + str(sdr.rx_powerdown_en_chan0))
sdr.rx_powerdown_en_chan1 = 0
print("rx_powerdown_chan1: " + str(sdr.rx_powerdown_en_chan1))
sdr.gain_control_mode_chan0 = "slow_attack"
print("gain_control_mode_chan0: " + sdr.gain_control_mode_chan0)
sdr.gain_control_mode_chan0 = "manual"
print("gain_control_mode_chan0: " + sdr.gain_control_mode_chan0)
sdr.gain_control_mode_chan1 = "slow_attack"
print("gain_control_mode_chan1: " + sdr.gain_control_mode_chan1)
sdr.gain_control_mode_chan0 = "manual"
print("gain_control_mode_chan1: " + sdr.gain_control_mode_chan1)
print("rx_hardwaregain_chan0: " + str(sdr.rx_hardwaregain_chan0))
sdr.rx_hardwaregain_chan0 = -20
print("rx_hardwaregain_chan0: " + str(sdr.rx_hardwaregain_chan0))
print("rx_hardwaregain_chan1: " + str(sdr.rx_hardwaregain_chan1))
sdr.rx_hardwaregain_chan1 = -20
print("rx_hardwaregain_chan1: " + str(sdr.rx_hardwaregain_chan1))
print("rx_rf_bandwidth: " + str(sdr.rx_rf_bandwidth))
print("rx_sample_rate: " + str(sdr.rx_sample_rate))
print("trx_lo: " + str(sdr.trx_lo))
sdr.trx_lo = 6000000000
print("trx_lo: " + str(sdr.trx_lo))
