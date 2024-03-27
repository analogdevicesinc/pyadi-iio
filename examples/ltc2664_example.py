# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import adi

# Device initialization
try:
    myDAC = adi.ltc2664(uri="ip:analog.local")

    for ch in myDAC.channel_names:
        ch_object = eval("myDAC." + str(ch))
        voltage_range = ch_object.volt_available
        raw_value_range = ch_object.raw_available
        print(
            "LTC2644 channel "
            + ch
            + " configured output range "
            + str(voltage_range)
            + " mV: RAW value range "
            + str(raw_value_range)
        )

except Exception as e:
    print(str(e))
    print("Failed to open LTC2664 device")
    sys.exit(0)

# sweep entire output range in 100mV steps
voltage_range = myDAC.voltage0.volt_available

for v in range(int(voltage_range[0]), int(voltage_range[1]), 100):
    print("setting voltage0 = " + str(v / 1000) + " Volt")
    myDAC.voltage0.volt = v
    time.sleep(0.05)

myDAC.voltage0.powerdown = 1
