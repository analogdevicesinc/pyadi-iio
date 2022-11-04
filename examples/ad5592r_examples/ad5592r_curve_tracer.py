# Copyright (C) 2021 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
# ``
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys  # Only needed to read in command line arguments, if any

import adi  # This is the main pyadi-iio module, contains everything
import matplotlib.pyplot as plt  # Matplotlib is a very common Python plotting routine.

# Optionally pass URI as command line argument, else use analog.local
# (URI stands for "Uniform Resource Identifier")
# NOTE - when running directly on the Raspberry Pi, you CAN use "local",
# but you must run as root (sudo) because we are writing as well as reading
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

# Instantiate and connect to our AD5592r
# while the "my_" prefix might sound a little childish, it's a reminder that
# it represents the physical chip that is in front of you.
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

curves = []  # Empty list for curvces
vcs_index = 0  # curves[x][vcs_index] Extract collector voltages
ics_index = 1  # curves[x][ics_index] Extract collector currents

for vb in range(499, 2500, 500):  # Sweep base voltage from 499 mV to 2.5V in 5 steps
    Vbdrive.raw = vb / float(mV_per_lsb)  # Set base voltage
    ib = ((Vbdrive.raw * mV_per_lsb / 1000) - Vbe) / Rbase  # Calculate base current
    vcs = []  # Empty list for collector voltages
    ics = []  # Empty list for collector currents
    print("Base Drive: ", Vbdrive.raw * mV_per_lsb / 1000, " Volts, ", ib * 1e6, " uA")
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
        print("coll voltage: ", vc, "  coll curre: ", ic)  # Print for fun
    curves.append([vcs, ics])  # vcs, ics, will be index 0, 1, respectively

plt.figure(1)  # Create new figure
plt.title("Fred in the Shed Curve Tracer: Prototype 0.1")
plt.xlabel("Collector Voltage (V)")
plt.ylabel("Collector Current (mA)")
plt.tight_layout()  # A bit of formatting
for curve in range(0, len(curves)):  # Iterate through curves
    # plot() method arguments are X values, y values, with optional parameters after.
    plt.plot(curves[curve][vcs_index], curves[curve][ics_index])
plt.show()  # Self-explanatory :)
