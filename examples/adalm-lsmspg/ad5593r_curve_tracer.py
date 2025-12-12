# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse

import matplotlib.pyplot as plt  # Matplotlib is a very common Python plotting routine.

import adi  # This is the main pyadi-iio module, contains everything

# Optionally pass URI as command line argument, else use analog.local
# (URI stands for "Uniform Resource Identifier")
# NOTE - when running directly on the Raspberry Pi, you CAN use "local",
# but you must run as root (sudo) because we are writing as well as reading

parser = argparse.ArgumentParser(
    description="AD5592r NPN Curve Tracer, see\
                                 docs for connections"
)
parser.add_argument(
    "-u",
    default=["ip:analog.local"],
    help="-u (arg) URI of target device's context, eg: 'ip:analog.local',\
    'ip:192.168.2.1',\
    'serial:COM4,115200,8n1n'",
    action="store",
    nargs="*",
)
args = parser.parse_args()
my_uri = args.u[0]

print("uri: " + str(my_uri))

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

Vbdrive.raw = 500.0 / float(mV_per_lsb)
Vcdrive.raw = 500.0 / float(mV_per_lsb)

## Curve Tracer code!!

curves = []  # Empty list for curvces
vcs_index = 0  # curves[x][vcs_index] Extract collector voltages
ics_index = 1  # curves[x][ics_index] Extract collector currents

for vb in range(2000, 0, -500):  # Sweep base voltage from 499 mV to 2.5V in 5 steps
    Vbdrive.raw = int(vb / float(mV_per_lsb))  # Set base voltage
    ib = ((Vbdrive.raw * mV_per_lsb / 1000) - Vbe) / Rbase  # Calculate base current
    vcs = []  # Empty list for collector voltages
    ics = []  # Empty list for collector currents
    print("Base Drive: ", Vbdrive.raw * mV_per_lsb / 1000, " Volts, ", ib * 1e6, " uA")
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
        print("coll voltage: ", vc, "  coll curre: ", ic)  # Print for fun
    curves.append([vcs, ics])  # vcs, ics, will be index 0, 1, respectively


plt.figure(1)  # Create new figure
plt.title("Fred in the Shed Curve Tracer: Prototype 0.1\nPNP with AD5593r")
plt.xlabel("Collector Voltage (V)")
plt.ylabel("Collector Current (mA)")
plt.tight_layout()  # A bit of formatting
for curve in range(0, len(curves)):  # Iterate through curves
    # plot() method arguments are X values, y values, with optional parameters after.
    plt.plot(curves[curve][vcs_index], curves[curve][ics_index])
plt.show()  # Self-explanatory :)
