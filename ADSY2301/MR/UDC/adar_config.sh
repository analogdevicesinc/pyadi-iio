## Register details shown for adar1000_csb_0_1_1
## The rest of the ADAR1000s are set to the same settings

echo "Configuring Manta Ray Tile 1"
# SPI interface / mode
iio_reg adar1000_csb_0_1_1 0      189   # 0x000=INTERFACE_CONFIG_A, 0xBD (SDO active & addr ascend)  [ADI datasheet/driver]

# On-chip LDO trims
iio_reg adar1000_csb_0_1_1 1025     2   # 0x401=LDO_TRIM_CTL_1,   0x02 (recommended)
iio_reg adar1000_csb_0_1_1 1024    85   # 0x400=LDO_TRIM_CTL_0,   0x55 (~1.8V trim)

# TX external PA/LNA bias OFF codes
iio_reg adar1000_csb_0_1_1 70     255   # 0x046=CH1_PA_BIAS_OFF,  0xFF
iio_reg adar1000_csb_0_1_1 71     255   # 0x047=CH2_PA_BIAS_OFF,  0xFF
iio_reg adar1000_csb_0_1_1 72     255   # 0x048=CH3_PA_BIAS_OFF,  0xFF
iio_reg adar1000_csb_0_1_1 73     255   # 0x049=CH4_PA_BIAS_OFF,  0xFF
iio_reg adar1000_csb_0_1_1 74     104   # 0x04A=LNA_BIAS_OFF,     0x68

# TX external PA/LNA bias ON codes (first write)
iio_reg adar1000_csb_0_1_1 41     255   # 0x029=CH1_PA_BIAS_ON,   0xFF
iio_reg adar1000_csb_0_1_1 42     255   # 0x02A=CH2_PA_BIAS_ON,   0xFF
iio_reg adar1000_csb_0_1_1 43     255   # 0x02B=CH3_PA_BIAS_ON,   0xFF
iio_reg adar1000_csb_0_1_1 44     255   # 0x02C=CH4_PA_BIAS_ON,   0xFF
iio_reg adar1000_csb_0_1_1 45       0   # 0x02D=LNA_BIAS_ON,      0x00

# Global enables / RAM bypass / TX enable & switch control (early)
iio_reg adar1000_csb_0_1_1 48      31   # 0x030=MISC_ENABLES,     0x1F
iio_reg adar1000_csb_0_1_1 56      96   # 0x038=MEM_CTRL,         0x60 (bypass beam & bias RAM)
iio_reg adar1000_csb_0_1_1 49      28   # 0x031=SW_CTRL,          0x1C (driver/polarity set)
iio_reg adar1000_csb_0_1_1 47     127   # 0x02F=TX_ENABLES,       0x7F (VM+VGA+DRV + Ch1–4)
iio_reg adar1000_csb_0_1_1 54      22   # 0x036=BIAS_CURRENT_TX,  0x16
iio_reg adar1000_csb_0_1_1 55       6   # 0x037=BIAS_CURRENT_TX_DRV, 0x06

# TX per‑channel gain/phase (Ch1..Ch4)
iio_reg adar1000_csb_0_1_1 28     255   # 0x01C=CH_TX_GAIN(Ch1),  0xFF
iio_reg adar1000_csb_0_1_1 32      54   # 0x020=CH_TX_PHASE_I(Ch1), 0x36
iio_reg adar1000_csb_0_1_1 33      53   # 0x021=CH_TX_PHASE_Q(Ch1), 0x35
iio_reg adar1000_csb_0_1_1 29     255   # 0x01D=CH_TX_GAIN(Ch2),  0xFF
iio_reg adar1000_csb_0_1_1 34      54   # 0x022=CH_TX_PHASE_I(Ch2), 0x36
iio_reg adar1000_csb_0_1_1 35      53   # 0x023=CH_TX_PHASE_Q(Ch2), 0x35
iio_reg adar1000_csb_0_1_1 30     255   # 0x01E=CH_TX_GAIN(Ch3),  0xFF
iio_reg adar1000_csb_0_1_1 36      54   # 0x024=CH_TX_PHASE_I(Ch3), 0x36
iio_reg adar1000_csb_0_1_1 37      53   # 0x025=CH_TX_PHASE_Q(Ch3), 0x35
iio_reg adar1000_csb_0_1_1 31     255   # 0x01F=CH_TX_GAIN(Ch4),  0xFF
iio_reg adar1000_csb_0_1_1 38      54   # 0x026=CH_TX_PHASE_I(Ch4), 0x36
iio_reg adar1000_csb_0_1_1 39      53   # 0x027=CH_TX_PHASE_Q(Ch4), 0x35

# RX global enables and bias currents
iio_reg adar1000_csb_0_1_1 46     127   # 0x02E=RX_ENABLES,       0x7F (VM+VGA+LNA + Ch1–4)
iio_reg adar1000_csb_0_1_1 52       8   # 0x034=BIAS_CURRENT_RX_LNA, 0x08
iio_reg adar1000_csb_0_1_1 53      22   # 0x035=BIAS_CURRENT_RX,  0x16

# RX per‑channel gain/phase (Ch1..Ch4)
iio_reg adar1000_csb_0_1_1 16       0   # 0x010=CH_RX_GAIN(Ch1),  0x00
iio_reg adar1000_csb_0_1_1 20      54   # 0x014=CH_RX_PHASE_I(Ch1), 0x36
iio_reg adar1000_csb_0_1_1 21      53   # 0x015=CH_RX_PHASE_Q(Ch1), 0x35
iio_reg adar1000_csb_0_1_1 17       0   # 0x011=CH_RX_GAIN(Ch2),  0x00
iio_reg adar1000_csb_0_1_1 22      54   # 0x016=CH_RX_PHASE_I(Ch2), 0x36
iio_reg adar1000_csb_0_1_1 23      53   # 0x017=CH_RX_PHASE_Q(Ch2), 0x35
iio_reg adar1000_csb_0_1_1 18       0   # 0x012=CH_RX_GAIN(Ch3),  0x00
iio_reg adar1000_csb_0_1_1 24      54   # 0x018=CH_RX_PHASE_I(Ch3), 0x36
iio_reg adar1000_csb_0_1_1 25      53   # 0x019=CH_RX_PHASE_Q(Ch3), 0x35
iio_reg adar1000_csb_0_1_1 19       0   # 0x013=CH_RX_GAIN(Ch4),  0x00
iio_reg adar1000_csb_0_1_1 26      54   # 0x01A=CH_RX_PHASE_I(Ch4), 0x36
iio_reg adar1000_csb_0_1_1 27      53   # 0x01B=CH_RX_PHASE_Q(Ch4), 0x35

# Later switch control (enable TX/RX) + load working regs + LNA ON final
iio_reg adar1000_csb_0_1_1 49     176   # 0x031=SW_CTRL,          0xB0 (TX_EN+RX_EN asserted)
iio_reg adar1000_csb_0_1_1 40       1   # 0x028=LD_WRK_REGS,      0x01 (commit)
iio_reg adar1000_csb_0_1_1 45     211   # 0x02D=LNA_BIAS_ON,      0xD3 (final ON code)

iio_reg adar1000_csb_0_1_1 0      189   # 0x000=INTERFACE_CONFIG_A, 0xBD (SDO active & addr ascend)  [ADI datasheet/driver]

# On-chip LDO trims
iio_reg adar1000_csb_0_1_1 1025     2   # 0x401=LDO_TRIM_CTL_1,   0x02 (recommended)
iio_reg adar1000_csb_0_1_1 1024    85   # 0x400=LDO_TRIM_CTL_0,   0x55 (~1.8V trim)

# TX external PA/LNA bias OFF codes
iio_reg adar1000_csb_0_1_1 70     255   # 0x046=CH1_PA_BIAS_OFF,  0xFF
iio_reg adar1000_csb_0_1_1 71     255   # 0x047=CH2_PA_BIAS_OFF,  0xFF
iio_reg adar1000_csb_0_1_1 72     255   # 0x048=CH3_PA_BIAS_OFF,  0xFF
iio_reg adar1000_csb_0_1_1 73     255   # 0x049=CH4_PA_BIAS_OFF,  0xFF
iio_reg adar1000_csb_0_1_1 74     104   # 0x04A=LNA_BIAS_OFF,     0x68

# TX external PA/LNA bias ON codes (first write)
iio_reg adar1000_csb_0_1_1 41     255   # 0x029=CH1_PA_BIAS_ON,   0xFF
iio_reg adar1000_csb_0_1_1 42     255   # 0x02A=CH2_PA_BIAS_ON,   0xFF
iio_reg adar1000_csb_0_1_1 43     255   # 0x02B=CH3_PA_BIAS_ON,   0xFF
iio_reg adar1000_csb_0_1_1 44     255   # 0x02C=CH4_PA_BIAS_ON,   0xFF
iio_reg adar1000_csb_0_1_1 45       0   # 0x02D=LNA_BIAS_ON,      0x00

# Global enables / RAM bypass / TX enable & switch control (early)
iio_reg adar1000_csb_0_1_1 48      31   # 0x030=MISC_ENABLES,     0x1F
iio_reg adar1000_csb_0_1_1 56      96   # 0x038=MEM_CTRL,         0x60 (bypass beam & bias RAM)
iio_reg adar1000_csb_0_1_1 49      28   # 0x031=SW_CTRL,          0x1C (driver/polarity set)
iio_reg adar1000_csb_0_1_1 47     127   # 0x02F=TX_ENABLES,       0x7F (VM+VGA+DRV + Ch1–4)
iio_reg adar1000_csb_0_1_1 54      22   # 0x036=BIAS_CURRENT_TX,  0x16
iio_reg adar1000_csb_0_1_1 55       6   # 0x037=BIAS_CURRENT_TX_DRV, 0x06

# TX per‑channel gain/phase (Ch1..Ch4)
iio_reg adar1000_csb_0_1_1 28     255   # 0x01C=CH_TX_GAIN(Ch1),  0xFF
iio_reg adar1000_csb_0_1_1 32      54   # 0x020=CH_TX_PHASE_I(Ch1), 0x36
iio_reg adar1000_csb_0_1_1 33      53   # 0x021=CH_TX_PHASE_Q(Ch1), 0x35
iio_reg adar1000_csb_0_1_1 29     255   # 0x01D=CH_TX_GAIN(Ch2),  0xFF
iio_reg adar1000_csb_0_1_1 34      54   # 0x022=CH_TX_PHASE_I(Ch2), 0x36
iio_reg adar1000_csb_0_1_1 35      53   # 0x023=CH_TX_PHASE_Q(Ch2), 0x35
iio_reg adar1000_csb_0_1_1 30     255   # 0x01E=CH_TX_GAIN(Ch3),  0xFF
iio_reg adar1000_csb_0_1_1 36      54   # 0x024=CH_TX_PHASE_I(Ch3), 0x36
iio_reg adar1000_csb_0_1_1 37      53   # 0x025=CH_TX_PHASE_Q(Ch3), 0x35
iio_reg adar1000_csb_0_1_1 31     255   # 0x01F=CH_TX_GAIN(Ch4),  0xFF
iio_reg adar1000_csb_0_1_1 38      54   # 0x026=CH_TX_PHASE_I(Ch4), 0x36
iio_reg adar1000_csb_0_1_1 39      53   # 0x027=CH_TX_PHASE_Q(Ch4), 0x35

# RX global enables and bias currents
iio_reg adar1000_csb_0_1_1 46     127   # 0x02E=RX_ENABLES,       0x7F (VM+VGA+LNA + Ch1–4)
iio_reg adar1000_csb_0_1_1 52       8   # 0x034=BIAS_CURRENT_RX_LNA, 0x08
iio_reg adar1000_csb_0_1_1 53      22   # 0x035=BIAS_CURRENT_RX,  0x16

# RX per‑channel gain/phase (Ch1..Ch4)
iio_reg adar1000_csb_0_1_1 16       0   # 0x010=CH_RX_GAIN(Ch1),  0x00
iio_reg adar1000_csb_0_1_1 20      54   # 0x014=CH_RX_PHASE_I(Ch1), 0x36
iio_reg adar1000_csb_0_1_1 21      53   # 0x015=CH_RX_PHASE_Q(Ch1), 0x35
iio_reg adar1000_csb_0_1_1 17       0   # 0x011=CH_RX_GAIN(Ch2),  0x00
iio_reg adar1000_csb_0_1_1 22      54   # 0x016=CH_RX_PHASE_I(Ch2), 0x36
iio_reg adar1000_csb_0_1_1 23      53   # 0x017=CH_RX_PHASE_Q(Ch2), 0x35
iio_reg adar1000_csb_0_1_1 18       0   # 0x012=CH_RX_GAIN(Ch3),  0x00
iio_reg adar1000_csb_0_1_1 24      54   # 0x018=CH_RX_PHASE_I(Ch3), 0x36
iio_reg adar1000_csb_0_1_1 25      53   # 0x019=CH_RX_PHASE_Q(Ch3), 0x35
iio_reg adar1000_csb_0_1_1 19       0   # 0x013=CH_RX_GAIN(Ch4),  0x00
iio_reg adar1000_csb_0_1_1 26      54   # 0x01A=CH_RX_PHASE_I(Ch4), 0x36
iio_reg adar1000_csb_0_1_1 27      53   # 0x01B=CH_RX_PHASE_Q(Ch4), 0x35

# Later switch control (enable TX/RX) + load working regs + LNA ON final
iio_reg adar1000_csb_0_1_1 49     176   # 0x031=SW_CTRL,          0xB0 (TX_EN+RX_EN asserted)
iio_reg adar1000_csb_0_1_1 40       1   # 0x028=LD_WRK_REGS,      0x01 (commit)
iio_reg adar1000_csb_0_1_1 45     211   # 0x02D=LNA_BIAS_ON,      0xD3 (final ON code)

iio_reg adar1000_csb_0_1_2 0 189
iio_reg adar1000_csb_0_1_2 1025 2
iio_reg adar1000_csb_0_1_2 1024 85
iio_reg adar1000_csb_0_1_2 70 255
iio_reg adar1000_csb_0_1_2 71 255
iio_reg adar1000_csb_0_1_2 72 255
iio_reg adar1000_csb_0_1_2 73 255
iio_reg adar1000_csb_0_1_2 74 104
iio_reg adar1000_csb_0_1_2 41 255
iio_reg adar1000_csb_0_1_2 42 255
iio_reg adar1000_csb_0_1_2 43 255
iio_reg adar1000_csb_0_1_2 44 255
iio_reg adar1000_csb_0_1_2 45 0
iio_reg adar1000_csb_0_1_2 48 31
iio_reg adar1000_csb_0_1_2 56 96
iio_reg adar1000_csb_0_1_2 49 28
iio_reg adar1000_csb_0_1_2 47 127
iio_reg adar1000_csb_0_1_2 54 22
iio_reg adar1000_csb_0_1_2 55 6
iio_reg adar1000_csb_0_1_2 28 255
iio_reg adar1000_csb_0_1_2 32 54
iio_reg adar1000_csb_0_1_2 33 53
iio_reg adar1000_csb_0_1_2 29 255
iio_reg adar1000_csb_0_1_2 34 54
iio_reg adar1000_csb_0_1_2 35 53
iio_reg adar1000_csb_0_1_2 30 255
iio_reg adar1000_csb_0_1_2 36 54
iio_reg adar1000_csb_0_1_2 37 53
iio_reg adar1000_csb_0_1_2 31 255
iio_reg adar1000_csb_0_1_2 38 54
iio_reg adar1000_csb_0_1_2 39 53
iio_reg adar1000_csb_0_1_2 46 127
iio_reg adar1000_csb_0_1_2 52 8
iio_reg adar1000_csb_0_1_2 53 22
iio_reg adar1000_csb_0_1_2 16 0
iio_reg adar1000_csb_0_1_2 20 54
iio_reg adar1000_csb_0_1_2 21 53
iio_reg adar1000_csb_0_1_2 17 0
iio_reg adar1000_csb_0_1_2 22 54
iio_reg adar1000_csb_0_1_2 23 53
iio_reg adar1000_csb_0_1_2 18 0
iio_reg adar1000_csb_0_1_2 24 54
iio_reg adar1000_csb_0_1_2 25 53
iio_reg adar1000_csb_0_1_2 19 0
iio_reg adar1000_csb_0_1_2 26 54
iio_reg adar1000_csb_0_1_2 27 53
iio_reg adar1000_csb_0_1_2 49 176
iio_reg adar1000_csb_0_1_2 40 1
iio_reg adar1000_csb_0_1_2 45 211
iio_reg adar1000_csb_0_1_3 0 189
iio_reg adar1000_csb_0_1_3 1025 2
iio_reg adar1000_csb_0_1_3 1024 85
iio_reg adar1000_csb_0_1_3 70 255
iio_reg adar1000_csb_0_1_3 71 255
iio_reg adar1000_csb_0_1_3 72 255
iio_reg adar1000_csb_0_1_3 73 255
iio_reg adar1000_csb_0_1_3 74 104
iio_reg adar1000_csb_0_1_3 41 255
iio_reg adar1000_csb_0_1_3 42 255
iio_reg adar1000_csb_0_1_3 43 255
iio_reg adar1000_csb_0_1_3 44 255
iio_reg adar1000_csb_0_1_3 45 0
iio_reg adar1000_csb_0_1_3 48 31
iio_reg adar1000_csb_0_1_3 56 96
iio_reg adar1000_csb_0_1_3 49 28
iio_reg adar1000_csb_0_1_3 47 127
iio_reg adar1000_csb_0_1_3 54 22
iio_reg adar1000_csb_0_1_3 55 6
iio_reg adar1000_csb_0_1_3 28 255
iio_reg adar1000_csb_0_1_3 32 54
iio_reg adar1000_csb_0_1_3 33 53
iio_reg adar1000_csb_0_1_3 29 255
iio_reg adar1000_csb_0_1_3 34 54
iio_reg adar1000_csb_0_1_3 35 53
iio_reg adar1000_csb_0_1_3 30 255
iio_reg adar1000_csb_0_1_3 36 54
iio_reg adar1000_csb_0_1_3 37 53
iio_reg adar1000_csb_0_1_3 31 255
iio_reg adar1000_csb_0_1_3 38 54
iio_reg adar1000_csb_0_1_3 39 53
iio_reg adar1000_csb_0_1_3 46 127
iio_reg adar1000_csb_0_1_3 52 8
iio_reg adar1000_csb_0_1_3 53 22
iio_reg adar1000_csb_0_1_3 16 0
iio_reg adar1000_csb_0_1_3 20 54
iio_reg adar1000_csb_0_1_3 21 53
iio_reg adar1000_csb_0_1_3 17 0
iio_reg adar1000_csb_0_1_3 22 54
iio_reg adar1000_csb_0_1_3 23 53
iio_reg adar1000_csb_0_1_3 18 0
iio_reg adar1000_csb_0_1_3 24 54
iio_reg adar1000_csb_0_1_3 25 53
iio_reg adar1000_csb_0_1_3 19 0
iio_reg adar1000_csb_0_1_3 26 54
iio_reg adar1000_csb_0_1_3 27 53
iio_reg adar1000_csb_0_1_3 49 176
iio_reg adar1000_csb_0_1_3 40 1
iio_reg adar1000_csb_0_1_3 45 211
iio_reg adar1000_csb_0_1_4 0 189
iio_reg adar1000_csb_0_1_4 1025 2
iio_reg adar1000_csb_0_1_4 1024 85
iio_reg adar1000_csb_0_1_4 70 255
iio_reg adar1000_csb_0_1_4 71 255
iio_reg adar1000_csb_0_1_4 72 255
iio_reg adar1000_csb_0_1_4 73 255
iio_reg adar1000_csb_0_1_4 74 104
iio_reg adar1000_csb_0_1_4 41 255
iio_reg adar1000_csb_0_1_4 42 255
iio_reg adar1000_csb_0_1_4 43 255
iio_reg adar1000_csb_0_1_4 44 255
iio_reg adar1000_csb_0_1_4 45 0
iio_reg adar1000_csb_0_1_4 48 31
iio_reg adar1000_csb_0_1_4 56 96
iio_reg adar1000_csb_0_1_4 49 28
iio_reg adar1000_csb_0_1_4 47 127
iio_reg adar1000_csb_0_1_4 54 22
iio_reg adar1000_csb_0_1_4 55 6
iio_reg adar1000_csb_0_1_4 28 255
iio_reg adar1000_csb_0_1_4 32 54
iio_reg adar1000_csb_0_1_4 33 53
iio_reg adar1000_csb_0_1_4 29 255
iio_reg adar1000_csb_0_1_4 34 54
iio_reg adar1000_csb_0_1_4 35 53
iio_reg adar1000_csb_0_1_4 30 255
iio_reg adar1000_csb_0_1_4 36 54
iio_reg adar1000_csb_0_1_4 37 53
iio_reg adar1000_csb_0_1_4 31 255
iio_reg adar1000_csb_0_1_4 38 54
iio_reg adar1000_csb_0_1_4 39 53
iio_reg adar1000_csb_0_1_4 46 127
iio_reg adar1000_csb_0_1_4 52 8
iio_reg adar1000_csb_0_1_4 53 22
iio_reg adar1000_csb_0_1_4 16 0
iio_reg adar1000_csb_0_1_4 20 54
iio_reg adar1000_csb_0_1_4 21 53
iio_reg adar1000_csb_0_1_4 17 0
iio_reg adar1000_csb_0_1_4 22 54
iio_reg adar1000_csb_0_1_4 23 53
iio_reg adar1000_csb_0_1_4 18 0
iio_reg adar1000_csb_0_1_4 24 54
iio_reg adar1000_csb_0_1_4 25 53
iio_reg adar1000_csb_0_1_4 19 0
iio_reg adar1000_csb_0_1_4 26 54
iio_reg adar1000_csb_0_1_4 27 53
iio_reg adar1000_csb_0_1_4 49 176
iio_reg adar1000_csb_0_1_4 40 1
iio_reg adar1000_csb_0_1_4 45 211


