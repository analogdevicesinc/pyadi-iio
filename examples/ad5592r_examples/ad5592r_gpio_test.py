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
#
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


import sys
from time import sleep

import adi  # This is the main pyadi-iio module, contains everything

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

# Instantiate and connect to our AD5592r
# while the "my_" prefix might sound a little childish, it's a reminder that
# it represents the physical chip that is in front of you.
my_ad5592r = adi.ad5592r(uri=my_uri)

# Create iterable list of channels
channels = []
for attr in dir(my_ad5592r):
    if type(getattr(my_ad5592r, attr)) is adi.ad5592r._channel:
        channels.append(getattr(my_ad5592r, attr))

sleep(0.5)

# These are on the AD5592r, but are part of the GPIO subsystem. But the clever
# software team wrote a little driver called one-bit-adc-dac, which, does exactly
# what you would expect it to :)
my_gpios = adi.one_bit_adc_dac(uri=my_uri)


# Alternate red and green blinkenlichten!

# So - the curve tracer board has a 47-ohm resistor between CH1 and CH2. This
# means that we sorta have to wiggle both in tandem if we want to blink the light
# since the CH1 analog output loads down the GPIO (Yeah, took a while to figure
# that one out!) CH3 doesn't have this issue, it's only tied to the LED.

for i in range(0, 10):
    my_gpios.gpio_ad5592r_gpio_ch_2 = 1
    my_ad5592r.voltage1_dac.raw = 4095  # Gotta clean up that indexing business...

    my_gpios.gpio_ad5592r_gpio_ch_3 = 0

    sleep(0.5)

    my_gpios.gpio_ad5592r_gpio_ch_2 = 0
    my_ad5592r.voltage1_dac.raw = 0

    my_gpios.gpio_ad5592r_gpio_ch_3 = 1

    sleep(0.5)

# Read out state of GPIO inputs. The names are set in the device tree - the one-bit-adc-dac
# driver prepends gpio_ and lower-cases the label.
print("\nReading state of GPIO pins: ")
print("gpio_ad5592r_gpio_ch_5: ", my_gpios.gpio_ad5592r_gpio_ch_5)
print("gpio_ad5592r_gpio_ch_6: ", my_gpios.gpio_ad5592r_gpio_ch_6)
print("gpio_ad5592r_gpio_ch_7: ", my_gpios.gpio_ad5592r_gpio_ch_7)
print("\n\n")


# And for the sake of completeness... print out analog channel information.

for ch in channels:
    print("***********************")  # Just a separator for easier serial read
    print("Channel Name: ", ch.name)  # Channel Name
    print("is Output? ", ch._output)  # True = Output/Write/DAC, False = Input/Read/ADC
    print(
        "Channel Scale: ", ch.scale
    )  # Channel Scale can be 0.610351562 or 0.610351562*2

    # Print Temperature in Celsius
    if ch.name == "temp":
        T = ((ch.raw + ch.offset) * ch.scale) / 1000
        print("Channel Temperature (C): ", float(T))
    # Print Real Voltage in mV
    else:
        print(
            "Channel Real Value (mV): ", float(ch.raw * ch.scale)
        )  # Channel Raw Value
# del my_ad5592r
# del my_gpios
