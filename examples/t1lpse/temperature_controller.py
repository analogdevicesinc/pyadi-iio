"""
Temperature Controller Example using SWIOT1L boards.

Possible channel configuration values:
- max14906 selected as device: input, output, high_z
- ad74413r selected as device: high_z, voltage_out, current_out,
                   voltage_in, current_in_ext, current_in_loop,
                   resistance, digital_input, digital_input_loop,
                   current_in_ext_hart, current_in_loop_hart
"""

import argparse
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

AD74413R_DAC_MAX_CODE = 8192

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="SWIOT thermostat controller")

parser.add_argument(
    "--temp-ip",
    default="192.168.97.41",
    help="IP address of temperature board (default: 192.168.97.41)",
)

parser.add_argument(
    "--fan-ip",
    default="192.168.97.40",
    help="IP address of fan control board (default: 192.168.97.40)",
)

parser.add_argument(
    "--temp-on",
    type=float,
    default=50.0,
    help="Fan turns ON at/above this temperature in °C (default: 50.0)",
)

parser.add_argument(
    "--temp-off",
    type=float,
    default=40.0,
    help="Fan turns OFF at/below this temperature in °C (default: 40.0)",
)

args = parser.parse_args()

# Device URIs (fallback to defaults if args not provided)
dev_uri_temp = f"ip:{args.temp_ip}"  # Board with temperature sensor
dev_uri_fan = f"ip:{args.fan_ip}"  # Board with fan control
channel_config_temp = ["voltage_in", "voltage_in", "voltage_out", "voltage_in"]

# Possible values: 0, 1
channel_enable_temp = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device_temp = ["ad74413r", "ad74413r", "ad74413r", "ad74413r"]

board_temp = adi.swiot1l(uri=dev_uri_temp)
board_temp.mode = "config"
board_temp = adi.swiot1l(uri=dev_uri_temp)

board_temp.ch0_device = channel_device_temp[0]
board_temp.ch0_function = channel_config_temp[0]
board_temp.ch0_enable = channel_enable_temp[0]
board_temp.ch1_device = channel_device_temp[1]
board_temp.ch1_function = channel_config_temp[1]
board_temp.ch1_enable = channel_enable_temp[1]
board_temp.ch2_device = channel_device_temp[2]
board_temp.ch2_function = channel_config_temp[2]
board_temp.ch2_enable = channel_enable_temp[2]
board_temp.ch3_device = channel_device_temp[3]
board_temp.ch3_function = channel_config_temp[3]
board_temp.ch3_enable = channel_enable_temp[3]
board_temp.mode = "runtime"

# Re-connect after switching to runtime
board_temp = adi.swiot1l(uri=dev_uri_temp)

channel_config_fan = ["output", "voltage_in", "voltage_in", "high_z"]

# Possible values: 0, 1
channel_enable_fan = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device_fan = ["max14906", "ad74413r", "ad74413r", "ad74413r"]

board_fan = adi.swiot1l(uri=dev_uri_fan)
board_fan.mode = "config"
board_fan = adi.swiot1l(uri=dev_uri_fan)

board_fan.ch0_device = channel_device_fan[0]
board_fan.ch0_function = channel_config_fan[0]
board_fan.ch0_enable = channel_enable_fan[0]
board_fan.ch1_device = channel_device_fan[1]
board_fan.ch1_function = channel_config_fan[1]
board_fan.ch1_enable = channel_enable_fan[1]
board_fan.ch2_device = channel_device_fan[2]
board_fan.ch2_function = channel_config_fan[2]
board_fan.ch2_enable = channel_enable_fan[2]
board_fan.ch3_device = channel_device_fan[3]
board_fan.ch3_function = channel_config_fan[3]
board_fan.ch3_enable = channel_enable_fan[3]
board_fan.mode = "runtime"

# Re-connect after switching to runtime
board_fan = adi.swiot1l(uri=dev_uri_fan)

TEMP_ON = args.temp_on
TEMP_OFF = args.temp_off

if TEMP_OFF >= TEMP_ON:
    raise ValueError(
        f"Invalid hysteresis: TEMP_OFF ({TEMP_OFF}) must be < TEMP_ON ({TEMP_ON})."
    )

# Control variables
fan_is_on = False

# Data storage for plotting
time_data = []
temperature_data = []
tmp01_temperature_data = []
fan_state_data = []

# --- Helper Functions ---


def power_tmp01_on():
    """Power TMP01 sensor ON"""
    board_temp.ad74413r.channel["voltage2"].raw = 8000


# TMP01 temperature reacting function
def read_tmp01_temperature():
    """Read temperature from TMP01 sensor on channel 3"""
    voltage_raw = (
        board_temp.ad74413r.channel["voltage3"].raw
        * board_temp.ad74413r.channel["voltage3"].scale
        + board_temp.ad74413r.channel["voltage3"].offset
    )
    temperature_c = voltage_raw / 5 - 273.15
    return temperature_c


# Function to turn fan on
def turn_fan_on():
    """Turn fan completely ON"""
    global fan_is_on
    board_fan.max14906.channel["voltage0"].raw = 1
    fan_is_on = True
    print("FAN ON")


# Function to turn fan off
def turn_fan_off():
    """Turn fan completely OFF"""
    global fan_is_on
    board_fan.max14906.channel["voltage0"].raw = 0
    fan_is_on = False
    print("FAN OFF")


# Function to simulate thermostat functionality
def simple_thermostat(temperature):
    """
    Simple thermostat logic:
    - Hot (≥27°C): Fan ON
    - Cool (≤26°C): Fan OFF
    - Between 26-27°C: Keep current state
    """
    global fan_is_on

    if not fan_is_on:
        # Fan is currently OFF
        if temperature >= TEMP_ON:
            turn_fan_on()
    else:
        # Fan is currently ON
        if temperature <= TEMP_OFF:
            turn_fan_off()

    return fan_is_on


# --- Main Execution Loop ---
try:
    # Print device information
    print(
        "Temperature Board AD74413R input channels:",
        board_temp.ad74413r._rx_channel_names,
    )
    print(
        "Fan Control Board MAX14906 channels:",
        board_fan.max14906._tx_channel_names,
        board_fan.max14906._rx_channel_names,
    )
    print(f"Initial ADT75 temperature reading: {board_temp.adt75()} °C")
    print(f"Turn ON at: {TEMP_ON}°C")
    print(f"Turn OFF at: {TEMP_OFF}°C")
    print("-" * 50)

    # Make sure fan starts OFF
    turn_fan_off()

    # Power TMP01 sensor ON
    power_tmp01_on()

    start_time = time.time()

    # Main thermostat control loop
    while True:
        # Read the current temperature using TMP01 and ADT75 sensors
        temp_tmp01 = read_tmp01_temperature()
        temp_adt75 = board_temp.adt75()

        print(f"TMP01 Temperature: {temp_tmp01:.2f}°C")
        print(f"ADT75 Temperature: {temp_adt75:.2f}°C")

        # Apply thermostat logic
        fan_state = simple_thermostat(temp_tmp01)

        # Append data for plotting
        elapsed_time = time.time() - start_time
        time_data.append(elapsed_time)
        temperature_data.append(temp_adt75)
        tmp01_temperature_data.append(temp_tmp01)
        fan_state_data.append(100 if fan_state else 0)  # 100% or 0% for plotting

        # Plot data every 10 iterations
        if len(time_data) % 10 == 0:
            plt.clf()

            # Plot Temperature vs. Time
            plt.subplot(2, 1, 1)
            plt.plot(
                time_data,
                tmp01_temperature_data,
                "b-",
                linewidth=2,
                label="TMP01 Temperature",
            )
            plt.plot(
                time_data,
                temperature_data,
                "g-",
                linewidth=1,
                label="ADT75 Temperature",
            )
            plt.axhline(
                TEMP_ON,
                color="r",
                linestyle="--",
                linewidth=2,
                label=f"ON at {TEMP_ON}°C",
            )
            plt.axhline(
                TEMP_OFF,
                color="orange",
                linestyle="--",
                linewidth=2,
                label=f"OFF at {TEMP_OFF}°C",
            )
            plt.xlabel("Time (s)")
            plt.ylabel("Temperature (°C)")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.title("Thermostat Temperature Monitoring")

            # Plot Fan State vs. Time
            plt.subplot(2, 1, 2)
            plt.plot(time_data, fan_state_data, "r-", linewidth=3, label="Fan State")
            plt.ylim(-10, 110)
            plt.ylabel("Fan State")
            plt.yticks([0, 100], ["OFF", "ON"])
            plt.xlabel("Time (s)")
            plt.title("Fan On/Off State")
            plt.legend()
            plt.grid(True, alpha=0.3)

            # Adjust layout and update the plot
            plt.tight_layout()
            plt.pause(0.01)

        print("-" * 50)
        time.sleep(2)  # Adjusted for more reasonable update rate

except KeyboardInterrupt:
    # Stop the fan when CTRL+C is pressed
    turn_fan_off()
    print("\nThermostat stopped and fan turned off.")
    print("System shutdown complete.")
    plt.show()  # Keep plots visible
