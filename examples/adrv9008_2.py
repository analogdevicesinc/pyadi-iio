# Copyright (C) 2019-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

sdr = adi.adrv9008_2(uri="ip:localhost")

sdr.ensm_mode = "radio_on"
print("ensm_mode: " + sdr.ensm_mode)
print("tx_hardwaregain_chan0: " + str(sdr.tx_hardwaregain_chan0))
sdr.tx_hardwaregain_chan0 = -20
print("tx_hardwaregain_chan0: " + str(sdr.tx_hardwaregain_chan0))
print("tx_hardwaregain_chan1: " + str(sdr.tx_hardwaregain_chan1))
sdr.tx_hardwaregain_chan1 = -20
print("tx_hardwaregain_chan1: " + str(sdr.tx_hardwaregain_chan1))
print("tx_rf_bandwidth: " + str(sdr.tx_rf_bandwidth))
print("tx_sample_rate: " + str(sdr.tx_sample_rate))
print("trx_lo: " + str(sdr.trx_lo))
sdr.trx_lo = 6000000000
print("trx_lo: " + str(sdr.trx_lo))
print("aux_obs_lo: " + str(sdr.aux_obs_lo))
sdr.aux_obs_lo = 2500000000
print("aux_obs_lo: " + str(sdr.aux_obs_lo))
print("obs_powerdown_en: " + str(sdr.obs_powerdown_en))
sdr.obs_powerdown_en = 0
print("obs_powerdown_en: " + str(sdr.obs_powerdown_en))
print("obs_hardwaregain: " + str(sdr.obs_hardwaregain))
sdr.obs_hardwaregain = 3.5
print("obs_hardwaregain: " + str(sdr.obs_hardwaregain))
print("orx_sample_rate: " + str(sdr.orx_sample_rate))
