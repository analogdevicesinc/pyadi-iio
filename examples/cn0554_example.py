# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import adi
import numpy as np

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

# Instantiate CN0554 object
my_cn0554 = adi.cn0554(uri=my_uri)

# Notify user of scaling factor based on default resistor values
print("Scale factor from onboard resistors: " + str(my_cn0554.in_scale))

# voltages to set for each DAC output pair. Always make sure that even
# numbered indices are greater than their odd counterparts (V_even > V_odd)
vset = [1500, 1200, 1300, 900, 2000, 1000, 1350, 560]

for a in range(0, 4):
    # Track the voltage set at the DAC outputs
    print(
        "-------Vset values: "
        + str(vset[2 * a])
        + "mV   "
        + str(vset[2 * a + 1])
        + "mV -------"
    )
    print("")

    # Print expected values measured based on DAC inputs
    expected_diff = (vset[2 * a] - vset[2 * a + 1]) / 1000

    # Set the DAC outputs
    for out_ch in my_cn0554.dac_out_channels:
        cn_obj = eval("my_cn0554.dac." + str(out_ch))
        id_num = int(out_ch[7:])

        if id_num % 2 == 0:
            cn_obj.volt = vset[2 * a]
        else:
            cn_obj.volt = vset[2 * a + 1]

    # Request data from onboard ADC
    print("Capturing data....")
    dat = my_cn0554.rx()
    print("")
    print("")

    # Print out average of measured values
    for ind, sigs in enumerate(dat):
        ch_in_range = str(my_cn0554.adc_in_channels[ind])
        sigs = my_cn0554.convert_to_volts(sigs, ch_in_range)
        print("Expected difference measurements: " + str(expected_diff))
        print("Average Values of " + ch_in_range + ": " + str(np.mean(sigs)))
        print("")
        print(
            "#######################################################################################"
        )

    # Small delay between iterations
    time.sleep(1)
