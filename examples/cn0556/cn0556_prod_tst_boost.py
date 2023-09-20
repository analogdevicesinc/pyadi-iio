import sys
import time

import adi
import numpy as np

print("-----------------------------------------------------------------------")
print("| EVAL-CN0556-EBZ: Programmable High Current Source/Sink Power Supply |")
print("-----------------------------------------------------------------------")
print("\n")
print("General Reminders:")
print(" - This test will run the board in Boost Mode.")
print(
    " - Double check that the connections of the power supply and the electronic load are for the Boost Mode Operation."
)
print(
    " - Make sure that the power supply and the electronic load are turned off and or disabled at the start of this test program."
)
print(
    "!! Warning: The following steps involve high DC voltages. \nFollow instructions carefully to prevent hot plugging which may damage the device by an overvoltage transient."
)
print(" - Double check the connections again!")

print("\n")
print("Connecting to evaluation board...")
my_cn0556 = adi.cn0556(uri="ip:analog.local")
time.sleep(1)

print("Starting Buck Mode Test...")

# Boost Mode Default Values:
V2_In = 14
UV2 = 12

V1_Out = 56

In_Current_Lim = 35
Out_Current_Lim = 10

print("\n")
my_cn0556.gpio.gpio_drxn = 0  # Set to Boost Mode = 0
print("Enable ON!")
print("Boost Mode ON!")
my_cn0556.gpio.gpio_en = 1
print("\n")

while True:
    user_input = input(
        "Test # 1: Default Configuration of CN0556. Press enter to continue."
    )
    if user_input == "":
        # Set Control Voltages from DAC:
        my_cn0556.set_boost_input_volt(14)
        my_cn0556.set_boost_input_undervolt(12)

        my_cn0556.set_boost_output_volt(56)

        my_cn0556.set_boost_input_current_lim(35)
        my_cn0556.set_boost_output_current_lim(10)
        break
    else:
        raise Exception("Press ENTER key.")


time.sleep(1)

print("Maximum Input Rating: " + str(V2_In) + "V , " + str(In_Current_Lim) + "A")
print("Maximum Output Rating: " + str(V1_Out) + "V , " + str(Out_Current_Lim) + "A")

print("\n")

print("......................................................")
print("Turn ON DC Voltage Source to V2 Boost Input Terminals...")
print("......................................................")
time.sleep(2)

while True:
    user_input = input("Press ENTER if voltage source is turned on.")

    if user_input == "":
        # Set Control Voltages from DAC:
        my_cn0556.set_boost_input_volt(14)
        my_cn0556.set_boost_input_undervolt(12)

        my_cn0556.set_boost_output_volt(56)

        my_cn0556.set_boost_input_current_lim(35)
        my_cn0556.set_boost_output_current_lim(10)
        break

print("The output voltage must still be from 54-57V.")
print("Take note: PASS or FAIL")
print("......................................................")
print("\n")
print("\n")

print("......................................................")
print("Test # 2: The output voltage will be set to 40V.")
print("\n")

while True:
    user_input = input(
        "Press ENTER to set the output voltage to 40V. Do not turn off power source.\n"
    )

    if user_input == "":
        print("The output voltage is set to 40V.\n")
        my_cn0556.set_boost_output_volt(40)
        break


print("The output voltage must still be from 54-57V.")
print("Take note: PASS or FAIL")
print("......................................................")
print("\n")
print("\n")

print("......................................................")
print("Test # 3: The output current limit will be set to 2A.")

while True:
    user_input = input(
        "Press ENTER to set the output current limit to 2A. Do not turn off power source."
    )

    if user_input == "":
        my_cn0556.set_boost_output_current_lim(2)
        break


print("------")
print("Instruction: Slowly increase the electronic load to 2A.")
print("The output voltage must drop upon nearing the 2A limit.")
print("Take note: PASS or FAIL")
print("\n")
print("......................................................")

while True:
    user_input = input("Press ENTER to end the test.")

    if user_input == "":
        break

print("\n")
print("Test Done!")

print("Turning off the device.")

my_cn0556.dac.voltage0.volt = 0
my_cn0556.dac.voltage2.volt = 0
my_cn0556.dac.voltage4.volt = 0
my_cn0556.dac.voltage6.volt = 0
my_cn0556.dac.voltage8.volt = 0
my_cn0556.dac.voltage10.volt = 0
my_cn0556.dac.voltage12.volt = 0
my_cn0556.dac.voltage14.volt = 0

my_cn0556.gpio.gpio_en = 0
my_cn0556.gpio.gpio_drxn = 0

print("OFF!\n\n")
print("Turn off power supply and electronic load!")
