import sys
import time

import adi
import numpy as np

print("-----------------------------------------------------------------------")
print("| EVAL-CN0556-EBZ: Programmable High Current Source/Sink Power Supply |")
print("-----------------------------------------------------------------------")
print("\n")
print("General Reminders:")
print(" - This test will run the board in Buck Mode.")
print(
    " - Double check that the connections of the power supply and the electronic load are for the Buck Mode Operation."
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

# Buck Mode Default Values:
V1_In = 56
UV1 = 54

V2_Out = 14

In_Current_Lim = 10
Out_Current_Lim = 35

print("\n")
my_cn0556.gpio.gpio_drxn = 1  # Set to Buck Mode = 1
print("Enable ON!")
print("Buck Mode ON!")
my_cn0556.gpio.gpio_en = 1
print("\n")

while True:
    user_input = input("Default Configuration of CN0556. Press enter to continue.")
    if user_input == "":
        # Set Control Voltages from DAC:
        my_cn0556.set_buck_input_volt(V1_In)
        my_cn0556.set_buck_input_undervolt(UV1)

        my_cn0556.set_buck_output_volt(V2_Out)

        my_cn0556.set_buck_input_current_lim(In_Current_Lim)
        my_cn0556.set_buck_output_current_lim(Out_Current_Lim)
        break
    else:
        raise Exception("Press ENTER key.")


time.sleep(1)

print("Maximum Input Rating: " + str(V1_In) + "V , " + str(In_Current_Lim) + "A")
print("Maximum Output Rating: " + str(V2_Out) + "V , " + str(Out_Current_Lim) + "A")

print("\n")

print("......................................................")
print("Turn ON DC Voltage Source to V1 Buck Input Terminals...")
print("......................................................")
time.sleep(2)

while True:
    user_input = input("Press ENTER if voltage source is turned on.")

    if user_input == "":
        my_cn0556.set_buck_input_volt(56)
        my_cn0556.set_buck_input_undervolt(54)

        my_cn0556.set_buck_output_volt(14)

        my_cn0556.set_buck_input_current_lim(10)
        my_cn0556.set_buck_output_current_lim(35)
        break

print("\n")
print("\n")

print("......................................................")
print("Test # 1: The input undervoltage will be set to 40V.")
print("\n")

while True:
    user_input = input(
        "Press ENTER to set the undervoltage to 40V. Do not turn off power source.\n"
    )

    if user_input == "":
        print("The input undervoltage is set to 40V.\n")
        my_cn0556.set_buck_input_undervolt(40)
        break

print("------")
print("Instruction: Slowly decrease the DC power supply to 40V.\n")
time.sleep(2)
print("The output voltage must still be from 13-15V.")
print("Take note: PASS or FAIL")
print("......................................................")
print("\n")
print("\n")

print("......................................................")
print("Test # 2: The output voltage will be set to 10V.")

while True:
    user_input = input(
        "Press ENTER to set the output voltage to 10V. Do not turn off power source."
    )

    if user_input == "":
        my_cn0556.set_buck_output_volt(10)
        break

print("The measured output voltage must be 10V.")
print("Take note: PASS or FAIL")
print("......................................................")
print("\n")


print("......................................................")
print("Test # 3: The output load current will be set to 2A limit")
print("The output voltage must drop when reaching the limit")
print("\n")

while True:
    user_input = input(
        "Press ENTER to set the output current limit to 2A. Do not turn off power source."
    )

    if user_input == "":
        my_cn0556.set_buck_output_current_lim(2)
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
