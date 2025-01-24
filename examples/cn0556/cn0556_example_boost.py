import sys
import time

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_cn0556 = adi.cn0556(uri=my_uri)


my_cn0556.drxn = 0  # Set to Boost Mode = 0
drxn_status = my_cn0556.drxn
if drxn_status == 1:
    print("Buck Mode")
elif drxn_status == 0:
    print("Boost Mode")
else:
    print("Unknown Mode")

# Boost Mode Example:
UV2 = 12.0
V1_Out = 56.0
In_Current_Lim = 35.0
Out_Current_Lim = 10.0

# Set Control Voltages from DAC:
my_cn0556.boost_input_undervoltage = UV2
# my_cn0556.boost_input_undervoltage[0] - Gets the set Boost Input Undervoltage by the user
# my_cn0556.boost_input_undervoltage[1] - Gets the equivalent DAC Output Voltage to set the Boost Input Undervoltage
print(
    "Boost Input Undervoltage set to: "
    + str(my_cn0556.boost_input_undervoltage[0])
    + "V || UV2_CTL DAC Volt: "
    + str(my_cn0556.boost_input_undervoltage[1])
)

my_cn0556.boost_target_output_voltage = V1_Out
# my_cn0556.boost_target_output_voltage[0] - Gets the set Boost Output Voltage by the user
# my_cn0556.boost_target_output_voltage[1] - Gets the equivalent DAC Output Voltage to set the Boost Output Voltage
print(
    "Boost Output set to: "
    + str(my_cn0556.boost_target_output_voltage[0])
    + "V || FB1_CTL DAC Volt: "
    + str(my_cn0556.boost_target_output_voltage[1])
)

my_cn0556.boost_input_current_limit = In_Current_Lim
# my_cn0556.boost_input_current_limit[0] - Gets the set Boost Input Current Limit by the user
# my_cn0556.boost_input_current_limit[1] - Gets the equivalent DAC Output Voltage to set the Boost Input Current Limit
print(
    "Boost Input Current Limit set to: "
    + str(my_cn0556.boost_input_current_limit[0])
    + "V || ISET2N_CTL DAC Volt: "
    + str(my_cn0556.boost_input_current_limit[1])
)

my_cn0556.boost_output_current_limit = Out_Current_Lim
# my_cn0556.boost_output_current_limit[0] - Gets the set Boost Output Current Limit by the user
# my_cn0556.boost_output_current_limit[1] - Gets the equivalent DAC Output Voltage to set the Boost Output Current Limit
print(
    "Boost Output Current Limit set to: "
    + str(my_cn0556.boost_output_current_limit[0])
    + "V || ISET1N_CTL DAC Volt: "
    + str(my_cn0556.boost_output_current_limit[1])
)

print("\n...................................................")
print("Enable DC Voltage Source to V2 Boost In Terminals...")
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
        print("Input Voltage: " + str(my_cn0556.boost_input_voltage) + "V")
        print("Input Current: " + str(my_cn0556.boost_input_current) + "A")
        print("Output Voltage: " + str(my_cn0556.boost_output_voltage) + "V")
        print("Output Current: " + str(my_cn0556.boost_output_current) + "A")

        while True:
            user_input = input(
                "\nDo you want to continue? Enter 'N' to turn off CN0556. Enter 'Y' to leave the supply enabled. "
            )
            if user_input == "Y":
                break
            elif user_input == "N":
                # Disable CN0556:
                my_cn0556.enable = False
                print("=== End of Boost Mode Example ===")
                break
            else:
                my_cn0556.enable = False
                raise Exception("Enter the correct input.")

    else:
        my_cn0556.enable = False
        print("=== End of Boost Mode Example ===")
        break
    break
