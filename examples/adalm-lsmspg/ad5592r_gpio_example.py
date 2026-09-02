# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import sys
from time import sleep

import adi  # This is the main pyadi-iio module, contains everything

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

# Instantiate and connect to our AD5592r
# while the "my_" prefix might sound a little childish, it's a reminder that
# it represents the physical chip that is in front of you.
my_ad5592r = adi.ad5592r(uri=my_uri)

sleep(0.5)

# These are on the AD5592r, but are part of the GPIO subsystem. But the clever
# software team wrote a little driver called one-bit-adc-dac, which, does exactly
# what you would expect it to :)
my_gpios = adi.one_bit_adc_dac(uri=my_uri)

# Alternate red and green blinkenlichten!

# So - the curve tracer board has a 47-ohm resistor between CH1 and CH2. This
# means that we have to wiggle both in tandem if we want to blink the light
# since the CH1 analog output loads down the GPIO (Yeah, took a while to figure
# that one out!) CH3 doesn't have this issue, it's only tied to the LED.

print("Let's blink some blinkenlichten!")
for i in range(0, 10):
    my_gpios.gpio_ad5592r_gpio_ch_2 = 1
    my_ad5592r.voltage1_dac.raw = 4095  # set CH1 to full-scale

    my_gpios.gpio_ad5592r_gpio_ch_3 = 0

    sleep(0.5)

    my_gpios.gpio_ad5592r_gpio_ch_2 = 0  # Set CH1 to zero
    my_ad5592r.voltage1_dac.raw = 0

    my_gpios.gpio_ad5592r_gpio_ch_3 = 1
    print("Blink number ", i + 1)
    sleep(0.5)
print("Done!")

# Read out state of GPIO inputs. The names are set in the device tree - the one-bit-adc-dac
# driver prepends gpio_ and lower-cases the label.
print("\nReading state of GPIO pins: ")
print("gpio_ad5592r_gpio_ch_5: ", my_gpios.gpio_ad5592r_gpio_ch_5)
print("gpio_ad5592r_gpio_ch_6: ", my_gpios.gpio_ad5592r_gpio_ch_6)
print("gpio_ad5592r_gpio_ch_7: ", my_gpios.gpio_ad5592r_gpio_ch_7)
print("\n\n")

del my_ad5592r
del my_gpios
