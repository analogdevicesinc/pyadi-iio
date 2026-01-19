#!/bin/bash
# parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
# cd "$parent_path"

# Copyright © 2023 Analog Devices, Inc. All Rights Reserved. This software is proprietary and confidential to Analog Devices,
# Inc. and its licensors. By using this software you agree to the terms of the associated SPI Access Required to config
# interface regs
# Analog Devices Software License Agreement.

###############################################################
####      Script to:
###                 disable clocks
###                 setup correct adf4350 clock
###                 ad9508 dividers
###                 set correct ad4080 lvds clock count
###                 renable clocks
###                 re-sync the LVDS
###      This can all be configured by ACE
################################################################
stty cols 134 rows 44 # this can be modified for user preference and terminal screen resolution
clear

# Need to input a variable: Sampling Frequency
#$1 : Input Frequency in MHz
Fsamp=$1
FiltMode=$2
DecRate=$3

echo "Input Fsamp: $Fsamp"
adf4350_clk=$(awk -v x=$Fsamp 'BEGIN { print x*10000000 }' < /dev/null) # We need to be able to handle an floating point input!

echo "adf4350 Clock Freq, pre adjust: $adf4350_clk"


## Disable the AD9508 outputs
##

iio_attr -c one-bit-adc-dac voltage0 raw 1


#################################################################
## Enforce the defaults required for AD4080 Rev C. BOM board
## where CNV is configured for LVDS
## note: this is default on power up driver may be modifying
#################################################################
# This is now set in the case statements as due to AD9508 bug
# the polarity of the LVDS clock can change depending on
# the divide setting
#iio_reg ad9508 0x2B 0x16 # LVDS CLK set to LVDS Signalling



############################################################################
###   If/Elif Statement to set the AD9508 into the correct "Range" of Dividers
###   for the desired frequency range.
###   We also need to adjust the AD4080's LVDS clock position accordingly
###   Necessary to account to for the minimum output freq from the adf4350
############################################################################


	if ((200000000<= $(($adf4350_clk)) && $(($adf4350_clk)) <= 500000000))
	then
			adf4350_clk=$((adf4350_clk*1))
			echo  "ADF4350 PLL Frequency set to: $adf4350_clk"
			iio_attr -c /axi/spi@e0007000/adf4350@1 altvoltage0 frequency $adf4350_clk # Set back to def so that div freqs make sense
			echo
			echo "Set for: 40MSPS to 20MSPS Range"
			echo "AD4080 CNV Frequency Set to:"
			iio_attr -c ad9508 CNV frequency $((adf4350_clk/10)) # Set for ADC conversion rate
			echo
			echo "AD4080 LVDS CLK Set to:"
			iio_attr -c ad9508 MACH1_CLK frequency $((adf4350_clk/1))  # Set LVDS clock
			echo
			iio_reg ad4080 $(( 16#16 )) $(( 16#71 )) # Sets the appropriate LVDS_CNV_CLK_CNT
			iio_reg ad9508 0x2B 0x26 # 26


	elif ((100000000<= $(($adf4350_clk)) && $(($adf4350_clk)) < 200000000))
    then
			adf4350_clk=$((adf4350_clk*2))   #400MHz div by 2 + 200MHz tops it back up to 400MHz
      echo  "ADF4350 PLL Frequency set to: $adf4350_clk"
      iio_attr -c /axi/spi@e0007000/adf4350@1 altvoltage0 frequency $adf4350_clk # Set back to def so that div freqs make sense
      echo "20MSPS to 10MSPS Range"
      iio_attr -c ad9508 CNV frequency $((adf4350_clk/20))    # Set for ADC conversion rate
      echo "AD4080 LVDS CLK Set to:"
      iio_attr -c ad9508 MACH1_CLK frequency $((adf4350_clk/2))     # Set LVDS clock
      iio_reg ad4080 $(( 16#16 )) $(( 16#61 ))  # Sets the appropriate LVDS_CNV_CLK_CNT
      iio_reg ad9508 0x2B 0x26

	elif ((50000000<= $(($adf4350_clk)) && $(($adf4350_clk)) < 100000000))
    then
      adf4350_clk=$((adf4350_clk*4))  #accounts for the divider
      echo  "ADF4350 PLL Frequency set to: $adf4350_clk"
      iio_attr -c /axi/spi@e0007000/adf4350@1 altvoltage0 frequency $adf4350_clk # Set back to def so that div freqs make sense
			echo "10MSPS to 5MSPS Range"
      iio_attr -c ad9508 CNV frequency $((adf4350_clk/40))    # Set for ADC conversion rate
      echo "AD4080 LVDS CLK Set to:"
      iio_attr -c ad9508 MACH1_CLK frequency $((adf4350_clk/4))     # Set LVDS clock
      iio_reg ad4080 $(( 16#16 )) $(( 16#61 )) # Sets the appropriate LVDS_CNV_CLK_CNT
			iio_reg ad9508 0x2B 0x16

	elif ((25000000<= $(($adf4350_clk)) && $(($adf4350_clk)) < 50000000))
    then
      adf4350_clk=$((adf4350_clk*8))  #accounts for the divider
      echo  "ADF4350 PLL Frequency set to: $adf4350_clk"
      iio_attr -c /axi/spi@e0007000/adf4350@1 altvoltage0 frequency $adf4350_clk # Set back to def so that div freqs make sense
			echo "5MSPS to 2.5MSPS Range"
      iio_attr -c ad9508 CNV frequency $((adf4350_clk/80))          # Set for ADC conversion rate
      echo "AD4080 LVDS CLK Set to:"
      iio_attr -c ad9508 MACH1_CLK frequency $((adf4350_clk/8)) # Set LVDS clock
			iio_reg ad4080 $(( 16#16)) $(( 16#61 )) # Sets the appropriate LVDS_CNV_CLK_CNT
			iio_reg ad9508 0x2B 0x26

	elif ((10000000<= $(($adf4350_clk)) && $(($adf4350_clk)) < 25000000))
    then
      adf4350_clk=$((adf4350_clk*16))  #accounts for the divider
      echo  "Fsample number is: $adf4350_clk"
      iio_attr -c /axi/spi@e0007000/adf4350@1 altvoltage0 frequency $adf4350_clk # Set back to def so that div freqs make sense
			echo "2.5MSPS to 1. 25MSPS Range"
      iio_attr -c ad9508 CNV frequency $((adf4350_clk/160))          # Set for ADC conversion rate
      echo "AD4080 LVDS CLK Set to:"
			iio_attr -c ad9508 MACH1_CLK frequency $((adf4350_clk/16))  # Set LVDS clock
			iio_reg ad4080 $((16#16 )) $(( 16#61 )) # Sets the appropriate LVDS_CNV_CLK_CNT
			iio_reg ad9508 0x2B 0x16
			iio_reg ad9508 0x1F 0x16
	else
			adf4350_clk=$((400000000))
      adf4350_clk=$((adf4350_clk*1))  #accounts for the divider
      echo  "ADF4350 PLL Frequency set to: $adf4350_clk"
      iio_attr -c /axi/spi@e0007000/adf4350@1 altvoltage0 frequency $adf4350_clk # Set back to def so that div freqs make sense
      echo "5MSPS to 2.5MSPS Range"
      iio_attr -c ad9508 CNV frequency $((adf4350_clk/10))          # Set for ADC conversion rate
      echo "AD4080 LVDS CLK Set to:"
			iio_attr -c ad9508 MACH1_CLK frequency $((adf4350_clk/1)) # Set LVDS clock
			iio_reg  ad4080 $(( 16#16 )) $(( 16#71 )) # Sets the appropriate LVDS_CNV_CLK_CNT
			iio_reg ad9508 0x2B 0x26
	fi

iio_attr -c one-bit-adc-dac voltage0 raw 0

iio_attr -d ad4080 filter_sel disabled
sleep 0.25 #
# Run the LVDS Sync
iio_attr -c ad4080 voltage0 lvds_sync 1
sleep 0.25
iio_attr -d ad4080 filter_sel $FiltMode
sleep 0.25
iio_attr -d ad4080 sinc_dec_rate $DecRate
