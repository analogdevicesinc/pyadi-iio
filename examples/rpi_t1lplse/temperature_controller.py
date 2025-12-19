import time
import adi
import numpy as np
import matplotlib.pyplot as plt

AD74413R_DAC_MAX_CODE = 8192

# Device URIs
dev_uri_temp = "ip:192.168.97.41"  # Board with temperature sensor
dev_uri_fan = "ip:192.168.97.40"   # Board with fan control

"""
	Possible values:
	- max14906 selected as device: input, output, high_z
	- ad74413r selected as device: high_z, voltage_out, current_out,
				       voltage_in, current_in_ext, current_in_loop,
				       resistance, digital_input, digital_input_loop,
				       current_in_ext_hart, current_in_loop_hart

"""
channel_config_temp = ["voltage_in", "voltage_in", "voltage_out", "voltage_in"]

# Possible values: 0, 1
channel_enable_temp = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device_temp = ["ad74413r", "ad74413r", "ad74413r", "ad74413r"]

swiot_temp = adi.swiot(uri=dev_uri_temp)
swiot_temp.mode = "config"
swiot_temp = adi.swiot(uri=dev_uri_temp)

swiot_temp.ch0_device = channel_device_temp[0]
swiot_temp.ch0_function = channel_config_temp[0]
swiot_temp.ch0_enable = channel_enable_temp[0]
swiot_temp.ch1_device = channel_device_temp[1]
swiot_temp.ch1_function = channel_config_temp[1]
swiot_temp.ch1_enable = channel_enable_temp[1]
swiot_temp.ch2_device = channel_device_temp[2]
swiot_temp.ch2_function = channel_config_temp[2]
swiot_temp.ch2_enable = channel_enable_temp[2]
swiot_temp.ch3_device = channel_device_temp[3]
swiot_temp.ch3_function = channel_config_temp[3]
swiot_temp.ch3_enable = channel_enable_temp[3]
swiot_temp.mode = "runtime"

# Initialize temperature sensor board devices
ad74413r_temp = adi.ad74413r(uri=dev_uri_temp)
adt75_temp = adi.lm75(uri=dev_uri_temp)
swiot_temp = adi.swiot(uri=dev_uri_temp)
swiot_temp.mode = "runtime"

channel_config_fan = ["output", "voltage_in", "voltage_in", "high_z"]

# Possible values: 0, 1
channel_enable_fan = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device_fan = ["max14906", "ad74413r", "ad74413r", "ad74413r"]

swiot_fan = adi.swiot(uri=dev_uri_fan)
swiot_fan.mode = "config"
swiot_fan = adi.swiot(uri=dev_uri_fan)

swiot_fan.ch0_device = channel_device_fan[0]
swiot_fan.ch0_function = channel_config_fan[0]
swiot_fan.ch0_enable = channel_enable_fan[0]
swiot_fan.ch1_device = channel_device_fan[1]
swiot_fan.ch1_function = channel_config_fan[1]
swiot_fan.ch1_enable = channel_enable_fan[1]
swiot_fan.ch2_device = channel_device_fan[2]
swiot_fan.ch2_function = channel_config_fan[2]
swiot_fan.ch2_enable = channel_enable_fan[2]
swiot_fan.ch3_device = channel_device_fan[3]
swiot_fan.ch3_function = channel_config_fan[3]
swiot_fan.ch3_enable = channel_enable_fan[3]
swiot_fan.mode = "runtime"

# Initialize fan control board devices
max14906_fan = adi.max14906(uri=dev_uri_fan)
swiot_fan = adi.swiot(uri=dev_uri_fan)
swiot_fan.mode = "runtime"

TEMP_ON = 27.0      # Turn fan ON when temp reaches this
TEMP_OFF = 26.0     # Turn fan OFF when temp drops to this

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
    ad74413r_temp.channel["voltage2"].raw = 8000

# TMP01 temperature reacting function
def read_tmp01_temperature():
    """Read temperature from TMP01 sensor on channel 3"""
    voltage_raw = (ad74413r_temp.channel["voltage3"].raw * 
                  ad74413r_temp.channel["voltage3"].scale + 
                  ad74413r_temp.channel["voltage3"].offset)
    temperature_c = voltage_raw / 5 - 273.15
    return temperature_c

# Function to turn fan on
def turn_fan_on():
    """Turn fan completely ON"""
    global fan_is_on
    max14906_fan.channel["voltage0"].raw = 1
    fan_is_on = True
    print("FAN ON")

# Function to turn fan off
def turn_fan_off():
    """Turn fan completely OFF"""
    global fan_is_on
    max14906_fan.channel["voltage0"].raw = 0
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
    print("Temperature Board AD74413R input channels:", ad74413r_temp._rx_channel_names)
    print("Fan Control Board MAX14906 channels:", max14906_fan._tx_channel_names, max14906_fan._rx_channel_names)
    print(f"Initial ADT75 temperature reading: {adt75_temp() * 62.5} °C")
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
        temp_adt75 = adt75_temp() * 62.5
        
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
            plt.plot(time_data, tmp01_temperature_data, 'b-', linewidth=2, label="TMP01 Temperature")
            plt.plot(time_data, temperature_data, 'g-', linewidth=1, label="ADT75 Temperature") 
            plt.axhline(TEMP_ON, color='r', linestyle='--', linewidth=2, label=f"ON at {TEMP_ON}°C")
            plt.axhline(TEMP_OFF, color='orange', linestyle='--', linewidth=2, 
                       label=f"OFF at {TEMP_OFF}°C")
            plt.xlabel("Time (s)")
            plt.ylabel("Temperature (°C)")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.title("Thermostat Temperature Monitoring")

            # Plot Fan State vs. Time
            plt.subplot(2, 1, 2)
            plt.plot(time_data, fan_state_data, 'r-', linewidth=3, label="Fan State")
            plt.ylim(-10, 110)
            plt.ylabel("Fan State")
            plt.yticks([0, 100], ['OFF', 'ON'])
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