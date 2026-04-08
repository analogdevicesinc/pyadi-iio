# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""
ADALM-LSMSPG Production Test Script.

Connections: Four jumper-shunts placed between channels 4-5 and 6-7 on both
P2 and P5

The rest of the tests are just using the onboard circuits.

ToDo: Clean up GPIO test, make that a bit more elegant.
ToDo: Set LM75 hysteresis so the LED blinks, prompt user
ToDo: Basic analog test on NPN and PNP transistor circuits, no need for a
full curve trace, rather pick a place in the middle and do a quick and dirty
beta test.

"""

import argparse
import gc
from time import sleep

import matplotlib.pyplot as plt
import numpy as np

import adi

# Optionally pass URI as command line argument, else use analog.local
# (URI stands for "Uniform Resource Identifier")
# NOTE - when running directly on the Raspberry Pi, you CAN use "local",
# but you must run as root (sudo) because we are writing as well as reading

parser = argparse.ArgumentParser(description="ADALM-LSMSPG Production Test Script")
parser.add_argument(
    "-u",
    default=["ip:analog.local"],
    help="-u (arg) URI of target device's context, eg: 'ip:analog.local',\
    'ip:192.168.2.1',\
    'serial:COM4,115200,8n1n'",
    action="store",
    nargs="*",
)
parser.add_argument(
    "-v", "--verbose", help="Enable verbose output", action="store_true", default=False,
)
args = parser.parse_args()
my_uri = args.u[0]

verbose = args.verbose
beta_min = 150.0
beta_max = 450.0

failures = []

print("uri: " + str(my_uri))


def get_closest_index_numpy(float_list, target_number):
    """
  Finds the index of the float in a list that is closest to a target number.

  Args:
    float_list: A list or array of floats.
    target_number: The number to compare against.

  Returns:
    The index of the closest float.
  """
    # Calculate the absolute difference between each element and the target
    difference_array = np.abs(np.array(float_list) - target_number)
    # Find the index of the minimum difference
    closest_index = difference_array.argmin()
    return closest_index


# Instantiate and connect to our AD5592r
# while the "my_" prefix might sound a little childish, it's a reminder that
# it represents the physical chip that is in front of you.
# my_ad5592r = adi.ad5592r(uri=my_uri)
# my_ad5593r = adi.ad5592r(uri=my_uri, device_name="ad5593r")

my_lm75 = adi.lm75(uri=my_uri)


print("\nChecking temperature channel...")
print("Temperature raw: " + str(my_lm75.input))
my_lm75_temperature = my_lm75.to_degrees(my_lm75.input)
print("Temperature in deg. Celsius: " + str(my_lm75_temperature))

print("\nUpdate interval: " + str(my_lm75.update_interval))


print("\nMax threshold: " + str(my_lm75.to_degrees(my_lm75.max)))
print("Max hysteresis: " + str(my_lm75.to_degrees(my_lm75.max_hyst)))

print("\nSetting max threshold to 10C...\n")

my_lm75.max = my_lm75.to_millidegrees(10.0)
my_lm75.max_hyst = my_lm75.to_millidegrees(5.0)  # No need to blink

print("New thresholds:")
print("Max: " + str(my_lm75.to_degrees(my_lm75.max)))
print("Max hysteresis: " + str(my_lm75.to_degrees(my_lm75.max_hyst)))


# Giving a wide range, we just want to make sure the LM75 is alive:
if 15.0 < my_lm75_temperature < 35.0:
    print("LM75 temperature passes!")

else:
    print("LM75 temperature failure!")
    failures.append("LM75: " + str(my_lm75_temperature))


del my_lm75
gc.collect()
sleep(1.0)
my_gpios = adi.one_bit_adc_dac(uri=my_uri)

# Set outputs...
print("Setting GPIO outputs to initial state...")
my_gpios.gpio_ad5592r_gpo_ch_5 = 0
my_gpios.gpio_ad5592r_gpo_ch_7 = 1

my_gpios.gpio_ad5593r_gpo_ch_5 = 0
my_gpios.gpio_ad5593r_gpo_ch_7 = 1

# Read inputs...
if my_gpios.gpio_ad5592r_gpi_ch_4 == 0:
    print("WooHoo on 5592 ch 4-5!")
else:
    print("D'oh! 5592 ch 4-5! fails :(")
    failures.append("5592 ch 4-5")

if my_gpios.gpio_ad5592r_gpi_ch_6 == 1:
    print("WooHoo on 5592 ch 6-7!")
else:
    print("D'oh! 5592 ch 6-7! fails :(")
    failures.append("5592 ch 6-7")

if my_gpios.gpio_ad5593r_gpi_ch_4 == 0:
    print("WooHoo on 5593 ch 4-5!")
else:
    print("D'oh! 5593 ch 4-5! fails :(")
    failures.append("5593 ch 4-5")

if my_gpios.gpio_ad5593r_gpi_ch_6 == 1:
    print("WooHoo on 5593 ch 6-7!")
else:
    print("D'oh! 5593 ch 6-7! fails :(")
    failures.append("5593 ch 6-7")

# Set outputs the other way...
print("Setting GPIO outputs to opposite state...")
my_gpios.gpio_ad5592r_gpo_ch_5 = 1
my_gpios.gpio_ad5592r_gpo_ch_7 = 0

my_gpios.gpio_ad5593r_gpo_ch_5 = 1
my_gpios.gpio_ad5593r_gpo_ch_7 = 0

# Read inputs...
if my_gpios.gpio_ad5592r_gpi_ch_4 == 1:
    print("WooHoo on 5592 ch 4-5!")
else:
    print("D'oh! 5592 ch 4-5! fails :(")
    failures.append("5592 ch 4-5")

if my_gpios.gpio_ad5592r_gpi_ch_6 == 0:
    print("WooHoo on 5592 ch 6-7!")
else:
    print("D'oh! 5592 ch 6-7! fails :(")
    failures.append("5592 ch 6-7")

if my_gpios.gpio_ad5593r_gpi_ch_4 == 1:
    print("WooHoo on 5593 ch 4-5!")
else:
    print("D'oh! 5593 ch 4-5! fails :(")
    failures.append("5593 ch 4-5")

if my_gpios.gpio_ad5593r_gpi_ch_6 == 0:
    print("WooHoo on 5592 ch 6-7!")
else:
    print("D'oh! 5592 ch 6-7! fails :(")
    failures.append("5593 ch 6-7")


del my_gpios
gc.collect()
sleep(1.0)

my_ad5592r = adi.ad5592r(uri=my_uri)

# Define a few constants, according to curve tracer circuit
Rsense = 47.0  # 47 Ohms
Rbase = 47.0e3  # 47 kOhms
Vbe = 0.7  # Volts (An approximation, of course...)

# Symbolically associate net names with AD5592r channels...
# NOW are things getting intuitive? :)
Vbdrive = my_ad5592r.voltage0_dac
Vcsense = my_ad5592r.voltage1_adc
Vcdrive = my_ad5592r.voltage2_dac
Vcdrive_meas = my_ad5592r.voltage2_adc

mV_per_lsb = Vcdrive.scale  # Makes things a bit more intuitive below.
# Scale is identical for all channels of the AD5592r,
# not necessarily the case for other devices.

Vbdrive.raw = 500.0 / float(mV_per_lsb)
Vcdrive.raw = 500.0 / float(mV_per_lsb)

## Curve Tracer code!!

curves_npn = []  # Empty list for curvces
vcs_index = 0  # curves_npn[x][vcs_index] Extract collector voltages
ics_index = 1  # curves_npn[x][ics_index] Extract collector currents

for vb in range(499, 2500, 500):  # Sweep base voltage from 499 mV to 2.5V in 5 steps
    Vbdrive.raw = vb / float(mV_per_lsb)  # Set base voltage
    ib = ((Vbdrive.raw * mV_per_lsb / 1000) - Vbe) / Rbase  # Calculate base current
    vcs = []  # Empty list for collector voltages
    ics = []  # Empty list for collector currents
    if verbose:
        print(
            "Base Drive: ", Vbdrive.raw * mV_per_lsb / 1000, " Volts, ", ib * 1e6, " uA"
        )
    for vcv in range(
        0, 2500, 50
    ):  # Sweep collector drive voltage from 0 to 2.5V in 50 mV steps
        Vcdrive.raw = vcv / float(mV_per_lsb)  # Set collector drive voltage
        ic = (
            (Vcdrive_meas.raw - Vcsense.raw) * mV_per_lsb / Rsense
        )  # Measure collector current
        vc = Vcsense.raw * mV_per_lsb / 1000.0  # Remember - actual collector voltage is
        vcs.append(vc)  # a bit less due to sense resistor
        ics.append(ic)  # Add measurements to lists
        if verbose:
            print("coll voltage: ", vc, "  coll curre: ", ic)  # Print for fun
    curves_npn.append([vcs, ics])  # vcs, ics, will be index 0, 1, respectively

del my_ad5592r
gc.collect()
sleep(1.0)

if verbose:
    plt.figure(1)  # Create new figure
    plt.title("Fred in the Shed NPN Curve Tracer: Prototype 0.1")
    plt.xlabel("Collector Voltage (V)")
    plt.ylabel("Collector Current (mA)")
    plt.tight_layout()  # A bit of formatting
    for curve in range(0, len(curves_npn)):  # Iterate through curves_npn
        # plot() method arguments are X values, y values, with optional parameters after.
        plt.plot(curves_npn[curve][vcs_index], curves_npn[curve][ics_index])
    plt.show()  # Self-explanatory :)


# Calculate betas...
beta_npn = 0.0
index_1p5 = get_closest_index_numpy(curves_npn[0][vcs_index], 1.50)
for i in range(1, len(curves_npn)):
    beta_npn += curves_npn[i][ics_index][index_1p5]  # Extract collector current
beta_npn = np.abs((beta_npn / (len(curves_npn) - 1)) / (500.0 / Rbase))

if beta_min < beta_npn < beta_max:
    print("NPN beta passes: ", beta_npn)

# Instantiate and connect to our ad5593r
# while the "my_" prefix might sound a little childish, it's a reminder that
# it represents the physical chip that is in front of you.
my_ad5593r = adi.ad5592r(uri=my_uri, device_name="ad5593r")


# Define a few constants, according to curve tracer circuit
Rsense = 47.0  # 47 Ohms
Rbase = 47.0e3  # 47 kOhms
Vbe = 0.7  # Volts (An approximation, of course...)

# Symbolically associate net names with ad5593r channels...
# NOW are things getting intuitive? :)
Vbdrive = my_ad5593r.voltage0_dac
Vcsense = my_ad5593r.voltage1_adc
Vcdrive = my_ad5593r.voltage2_dac
Vcdrive_meas = my_ad5593r.voltage2_adc
Vedrive = (
    my_ad5593r.voltage3_dac
)  # UNLIKE NPN whose Ve is GND, need to set this explicitly


mV_per_lsb = Vcdrive.scale  # Makes things a bit more intuitive below.
# Scale is identical for all channels of the ad5593r,
# not necessarily the case for other devices.

Vedrive.raw = 2499.0 / float(mV_per_lsb)

Vbdrive.raw = 2499.0 / float(mV_per_lsb)
Vcdrive.raw = 2499.0 / float(mV_per_lsb)

## Curve Tracer code!!

curves_pnp = []  # Empty list for curvces
vcs_index = 0  # curves_pnp[x][vcs_index] Extract collector voltages
ics_index = 1  # curves_pnp[x][ics_index] Extract collector currents

for vb in range(2499, 0, -499):  # Sweep base voltage from 499 mV to 2.5V in 5 steps
    Vbdrive.raw = int(vb / float(mV_per_lsb))  # Set base voltage
    ib = ((Vbdrive.raw * mV_per_lsb / 1000) - Vbe) / Rbase  # Calculate base current
    vcs = []  # Empty list for collector voltages
    ics = []  # Empty list for collector currents
    if verbose:
        print(
            "Base Drive: ", Vbdrive.raw * mV_per_lsb / 1000, " Volts, ", ib * 1e6, " uA"
        )
    for vcv in range(
        2499, 0, -50
    ):  # Sweep collector drive voltage from 0 to 2.5V in 50 mV steps
        Vcdrive.raw = int(vcv / float(mV_per_lsb))  # Set collector drive voltage
        ic = (
            (Vcdrive_meas.raw - Vcsense.raw) * mV_per_lsb / Rsense
        )  # Measure collector current
        vc = Vcsense.raw * mV_per_lsb / 1000.0  # Remember - actual collector voltage is
        vcs.append(vc)  # a bit less due to sense resistor
        ics.append(ic)  # Add measurements to lists

        if verbose:
            print("coll voltage: ", vc, "  coll curre: ", ic)  # Print for fun
    curves_pnp.append([vcs, ics])  # vcs, ics, will be index 0, 1, respectively

del my_ad5593r
gc.collect()

if verbose:
    plt.figure(2)  # Create new figure
    plt.title("Fred in the Shed PNP Curve Tracer: Prototype 0.1\nPNP with AD5593r")
    plt.xlabel("Collector Voltage (V)")
    plt.ylabel("Collector Current (mA)")
    plt.tight_layout()  # A bit of formatting
    for curve in range(0, len(curves_pnp)):  # Iterate through curves_pnp
        # plot() method arguments are X values, y values, with optional parameters after.
        plt.plot(curves_pnp[curve][vcs_index], curves_pnp[curve][ics_index])
    plt.show()  # Self-explanatory :)

# Calculate betas...
beta_pnp = 0.0
index_1p5 = get_closest_index_numpy(curves_pnp[0][vcs_index], 1.50)
for i in range(1, len(curves_pnp)):
    beta_pnp += curves_pnp[i][ics_index][index_1p5]  # Extract collector current
beta_pnp = np.abs((beta_pnp / (len(curves_pnp) - 1)) / (500.0 / Rbase))

if beta_min < beta_pnp < beta_max:
    print("PNP beta passes: ", beta_pnp)


resp = input(
    "Are the following true?\n * Left-hand LED (DS3) is RED\n * Right-hand LED (DS4) is GREEN\n * LM75 LED (DS2) is RED\n(y or n)"
)
if resp == "y" and len(failures) == 0:
    print("WooHoo! Whole board passes!")

else:
    print("D'oh! Board fails either LEDs or these tests:")
    print(failures)
