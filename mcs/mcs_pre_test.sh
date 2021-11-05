#!/bin/bash
#load profile
cat /home/analog/Documents/Filters/lvds_fdd_mcs_test.json > /sys/bus/iio/devices/iio:device1/profile_config
# move all channels to calibrated
iio_attr -c adrv9002-phy -i voltage0 ensm_mode calibrated
iio_attr -c adrv9002-phy -i voltage1 ensm_mode calibrated
iio_attr -c adrv9002-phy -o voltage0 ensm_mode calibrated
iio_attr -c adrv9002-phy -o voltage1 ensm_mode calibrated

# MCS ready
iio_attr -d adrv9002-phy multi_chip_sync 1
echo "waiting for 6 pulses"