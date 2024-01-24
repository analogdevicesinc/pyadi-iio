import sys
import time

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_cn0556 = adi.cn0556(uri=my_uri)

my_cn0556.drxn = 1  # Set to Buck Mode = 1
drxn_status = my_cn0556.drxn
if drxn_status == 1:
    print("Buck Mode")
elif drxn_status == 0:
    print("Boost Mode")
else:
    print("Unknown Mode")

# Buck Mode Example:

UV1 = 54.0
V2_Out = 14.0
In_Current_Lim = 10.0
Out_Current_Lim = 35.0

# Set Control Voltages from DAC:

my_cn0556.buck_input_undervoltage = UV1
# my_cn0556.buck_input_undervoltage[0] - Gets the set Buck Input Undervoltage by the user
# my_cn0556.buck_input_undervoltage[1] - Gets the equivalent DAC Output Voltage to set the Buck Input Undervoltage

print(
    "Buck Input Undervoltage set to: "
    + str(my_cn0556.buck_input_undervoltage[0])
    + "V || UV1_CTL DAC Volt: "
    + str(my_cn0556.buck_input_undervoltage[1])
)

my_cn0556.buck_target_output_voltage = V2_Out
# my_cn0556.buck_target_output_voltage[0] - Gets the set Buck Output Voltage by the user
# my_cn0556.buck_target_output_voltage[1] - Gets the equivalent DAC Output Voltage to set the Buck Output Voltage

print(
    "Buck Output set to: "
    + str(my_cn0556.buck_target_output_voltage[0])
    + "V || FB2_CTL DAC Volt: "
    + str(my_cn0556.buck_target_output_voltage[1])
)

my_cn0556.buck_input_current_limit = In_Current_Lim
# my_cn0556.buck_input_current_limit[0] - Gets the set Buck Input Current Limit by the user
# my_cn0556.buck_input_current_limit[1] - Gets the equivalent DAC Output Voltage to set the Buck Input Current Limit

print(
    "Buck Input Current Limit set to: "
    + str(my_cn0556.buck_input_current_limit[0])
    + "V || ISET1P_CTL DAC Volt: "
    + str(my_cn0556.buck_input_current_limit[1])
)

my_cn0556.buck_output_current_limit = Out_Current_Lim
# my_cn0556.buck_output_current_limit[0] - Gets the set Buck Output Current Limit by the user
# my_cn0556.buck_output_current_limit[1] - Gets the equivalent DAC Output Voltage to set the Buck Output Current Limit

print(
    "Buck Output Current Limit set to: "
    + str(my_cn0556.buck_output_current_limit[0])
    + "V || ISET2P_CTL DAC Volt: "
    + str(my_cn0556.buck_output_current_limit[1])
)

print("\n..........................................................")
print(
    "Input Rating: Buck Input Undervoltage is set to "
    + str(UV1)
    + "V , "
    + str(In_Current_Lim)
    + "A"
)
print("Maximum Output Rating: " + str(V2_Out) + "V , " + str(Out_Current_Lim) + "A")
print("..........................................................")

print("\n...................................................")
print("Enable DC Voltage Source to V1 Buck In Terminals...")
print("...................................................")

while True:
    user_input = input(
        "\nPress ENTER to ENABLE CN0556. To exit the program, input any key and then PRESS ENTER. "
    )
    if user_input == "":
        # Enable CN0556:
        my_cn0556.enable = True

        time.sleep(1)

        print("ADC Readings: ")
        print("Input Voltage: " + str(my_cn0556.buck_input_voltage) + "V")
        print("Input Current: " + str(my_cn0556.buck_input_current) + "A")
        print("Output Voltage: " + str(my_cn0556.buck_output_voltage) + "V")
        print("Output Current: " + str(my_cn0556.buck_output_current) + "A")

        while True:
            user_input = input(
                "\nDo you want to continue? Enter 'N' to turn off CN0556. Enter 'Y' to leave the supply enabled. "
            )
            if user_input == "Y":
                break
            elif user_input == "N":
                # Disable CN0556:
                my_cn0556.enable = False
                print("=== End of Buck Mode Example ===")
                break
            else:
                my_cn0556.enable = False
                raise Exception("Enter the correct input.")

    else:
        my_cn0556.enable = False
        print("=== End of Buck Mode Example ===")
        break
    break
