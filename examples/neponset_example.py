# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""
Neponset Board Device Control Example

This script provides a clean interface for accessing ADMV devices on the Neponset board.
All devices are accessible through a single 'device' dictionary using the pattern:
    device['admv1420_rx_0'].reg_read(register)
    device['admv1420_rx_0'].reg_write(register, value)

    device['hmc7003_lo_0'].reg_write(0x0, value)
    
See all the device names below, under device mapping.

Device verification is handled through the 'device_ready' dictionary which tracks
whether each device was successfully initialized AND configured by checking the product ID.

Always check device_ready['device_name'] before accessing a device to ensure it's safe to use.
"""

import iio
import time

# USER CONFIGURATION
carrier_ip = "192.168.2.1" # Kria Carrier board ip address
###########################################

carrier_uri = "ip:" + carrier_ip

neponset = iio.Context(carrier_uri)

# Access neponset_gpio device
neponset_gpio = neponset.find_device("neponset_gpio")

# Global device dictionary - will be initialized by initialize_devices()
# Example access devices as:
# device['admv1420_rx_0'].reg_read(register)
# or
# device['admv1420_rx_0'].reg_write(register, value)
# or
# device['hmc7003_lo_0'].reg_write(0x0, value)
device = {
	# RX Channel 0 devices
	'admv1420_rx_0': None, 'admv8827_rx_0': None, 'admv8809_rx_0': None,
	# RX Channel 1 devices
	'admv1420_rx_1': None, 'admv8827_rx_1': None, 'admv8809_rx_1': None,
	# RX Channel 2 devices
	'admv1420_rx_2': None, 'admv8827_rx_2': None, 'admv8809_rx_2': None,
	# RX Channel 3 devices
	'admv1420_rx_3': None, 'admv8827_rx_3': None, 'admv8809_rx_3': None,
	# TX Channel 0 devices
	'admv1320_tx_0': None, 'admv8827_tx_0': None, 'admv8909_tx_0': None,
	# TX Channel 1 devices
	'admv1320_tx_1': None, 'admv8827_tx_1': None, 'admv8909_tx_1': None,
	# TX Channel 2 devices
	'admv1320_tx_2': None, 'admv8827_tx_2': None, 'admv8909_tx_2': None,
	# TX Channel 3 devices
	'admv1320_tx_3': None, 'admv8827_tx_3': None, 'admv8909_tx_3': None,
	# LO devices
	'hmc7003_lo_0': None, 'hmc7003_lo_1': None, 'hmc7003_lo_2': None, 'hmc7003_lo_3': None
}

# GPIO mapping - maps descriptive names to voltage channel names
gpio_map = {

	# ADMV1420 RX 0 GPIOs
	"ADMV1420_RX_RST_0": "voltage4",
	"ADMV1420_RX_CEN_0": "voltage5",
	"ADMV1420_RX_LOAD_0": "voltage16",
	"ADMV1420_RX_EN_0": "voltage17",
	
	# ADMV1420 RX 1 GPIOs
	"ADMV1420_RX_CEN_1": "voltage15",
	"ADMV1420_RX_RST_1": "voltage61",
	"ADMV1420_RX_LOAD_1": "voltage64",
	"ADMV1420_RX_EN_1": "voltage65",
	
	# ADMV1420 RX 2 GPIOs
	"ADMV1420_RX_EN_2": "voltage18",
	"ADMV1420_RX_RST_2": "voltage20",
	"ADMV1420_RX_LOAD_2": "voltage49",
	"ADMV1420_RX_CEN_2": "voltage56",

	# ADMV1420 RX 3 GPIOs
	"ADMV1420_RX_CEN_3": "voltage0",
	"ADMV1420_RX_RST_3": "voltage1",
	"ADMV1420_RX_LOAD_3": "voltage2",
	"ADMV1420_RX_EN_3": "voltage3",
	
	# ADMV1420 ADDRESS/FILTER CONTROL
	"ADMV1420_ADDF_0": "voltage10",
	"ADMV1420_ADDF_1": "voltage6",
	"ADMV1420_ADDF_2": "voltage7",
	"ADMV1420_ADDF_3": "voltage8",
	"ADMV1420_ADDF_4": "voltage48",
	"ADMV1420_ADDG_0": "voltage9",
	"ADMV1420_ADDG_1": "voltage62",
	"ADMV1420_ADDG_2": "voltage46",
	"ADMV1420_ADDG_3": "voltage11",
	"ADMV1420_ADDG_4": "voltage63",
	"ADMV1420_ADDG_5": "voltage47",
	
	# ADMV1320 TX 0 GPIOs
	"ADMV1320_TX_CEN_0": "voltage13",
	"ADMV1320_TX_LOAD_0": "voltage14",
	"ADMV1320_TX_RST_0": "voltage54",
	"ADMV1320_TX_SFL_0": "voltage50",
	"ADMV1320_TX_PS_L_0": "voltage60",
	
	# ADMV1320 TX 1 GPIOs
	"ADMV1320_TX_CEN_1": "voltage51",
	"ADMV1320_TX_LOAD_1": "voltage52",
	"ADMV1320_TX_RST_1": "voltage53",
	"ADMV1320_TX_SFL_1": "voltage26",
	"ADMV1320_TX_PS_L_1": "voltage25",
	
	# ADMV1320 TX 2 GPIOs
	"ADMV1320_TX_CEN_2": "voltage59",
	"ADMV1320_TX_LOAD_2": "voltage29",
	"ADMV1320_TX_RST_2": "voltage39",
	"ADMV1320_TX_SFL_2": "voltage21",
	"ADMV1320_TX_PS_L_2": "voltage38",
	
	# ADMV1320 TX 3 GPIOs
	"ADMV1320_TX_CEN_3": "voltage12",
	"ADMV1320_TX_LOAD_3": "voltage57",
	"ADMV1320_TX_RST_3": "voltage44",
	"ADMV1320_TX_SFL_3": "voltage58",
	"ADMV1320_TX_PS_L_3": "voltage45",
	
	# ADMV1320 ADDRESS/FILTER CONTROL
	"ADMV1320_ADD_0": "voltage31",
	"ADMV1320_ADD_1": "voltage22",
	"ADMV1320_ADD_2": "voltage30",
	"ADMV1320_ADD_3": "voltage41",
	"ADMV1320_ADD_4": "voltage37",
	"ADMV1320_ADD_5": "voltage24",
	"ADMV1320_ADDF_0": "voltage35",
	"ADMV1320_ADDF_1": "voltage34",
	"ADMV1320_ADDF_2": "voltage36",
	"ADMV1320_ADDF_3": "voltage23",
	"ADMV1320_ADDF_4": "voltage40",
	
	# LO HMC7003 0 FILTER SELECT
	"LO_0_FLTR_SEL0": "voltage55",
	"LO_0_FLTR_SEL1": "voltage19",

	# LO HMC7003 1 FILTER SELECT
	"LO_1_FLTR_SEL0": "voltage33",
	"LO_1_FLTR_SEL1": "voltage32",

	# LO HMC7003 2 FILTER SELECT
	"LO_2_FLTR_SEL0": "voltage43",
	"LO_2_FLTR_SEL1": "voltage42",

	# LO HMC7003 3 FILTER SELECT
	"LO_3_FLTR_SEL0": "voltage27",
	"LO_3_FLTR_SEL1": "voltage28",
	
	# BASE POWER GOOD
	"BASE_PGOOD": "voltage66"
}

# Device configuration mapping
DEVICE_CONFIG = {
	"admv1420": {"product_id": 0x68, "description": "ADMV1420", "type": "rx"},
	"admv8827": {"product_id": 0x27, "description": "ADMV8827"},  # Both RX and TX
	"admv8809": {"product_id": 0x09, "description": "ADMV8809", "type": "rx"},
	"admv1320": {"product_id": 0x67, "description": "ADMV1320", "type": "tx"},
	"admv8909": {"product_id": 0x09, "description": "ADMV8909", "type": "tx"}
}

# Device status tracking - True if device was successfully initialized AND configured
device_ready = {
	# RX devices
	'admv1420_rx_0': False, 'admv1420_rx_1': False, 'admv1420_rx_2': False, 'admv1420_rx_3': False,
	'admv8827_rx_0': False, 'admv8827_rx_1': False, 'admv8827_rx_2': False, 'admv8827_rx_3': False,
	'admv8809_rx_0': False, 'admv8809_rx_1': False, 'admv8809_rx_2': False, 'admv8809_rx_3': False,
	# TX devices
	'admv1320_tx_0': False, 'admv1320_tx_1': False, 'admv1320_tx_2': False, 'admv1320_tx_3': False,
	'admv8827_tx_0': False, 'admv8827_tx_1': False, 'admv8827_tx_2': False, 'admv8827_tx_3': False,
	'admv8909_tx_0': False, 'admv8909_tx_1': False, 'admv8909_tx_2': False, 'admv8909_tx_3': False,
	# LO devices
	'hmc7003_lo_0': True, 'hmc7003_lo_1': True, 'hmc7003_lo_2': True, 'hmc7003_lo_3': True
}

# Helper function to set GPIO by name
def set_gpio(gpio_name, value):
	"""Set GPIO by descriptive name"""
	if gpio_name in gpio_map:
		voltage_channel = gpio_map[gpio_name]
		# Find the output channel with the given ID
		channel = None
		for ch in neponset_gpio.channels:
			if ch.id == voltage_channel and ch.output:
				channel = ch
				break

		if channel is None:
			print(f"Output channel '{voltage_channel}' not found for GPIO '{gpio_name}'")
			return False

		channel.attrs["raw"].value = str(value)
		print(f"Set {gpio_name} to {value}")
		return True
	else:
		print(f"GPIO '{gpio_name}' not found in mapping")
		return False

# Helper function to get GPIO by name
def get_gpio(gpio_name):
	"""Get GPIO value by descriptive name"""
	if gpio_name in gpio_map:
		voltage_channel = gpio_map[gpio_name]
		# Find the channel with the given ID (try output first, then input)
		channel = None
		for ch in neponset_gpio.channels:
			if ch.id == voltage_channel:
				channel = ch
				break
		if channel is None:
			print(f"Channel '{voltage_channel}' not found for GPIO '{gpio_name}'")
			return None

		value = channel.attrs["raw"].value
		print(f"{gpio_name} = {value}")
		return value
	else:
		print(f"GPIO '{gpio_name}' not found in mapping")
		return None

def disable_rx_channels():
	"""Disable all ADMV1420 RX channels and put them in reset"""
	print("Disable RX channels CEN")
	set_gpio("ADMV1420_RX_CEN_0", 0)
	set_gpio("ADMV1420_RX_CEN_1", 0)
	set_gpio("ADMV1420_RX_CEN_2", 0)
	set_gpio("ADMV1420_RX_CEN_3", 0)
	
	print("Enable RX channels Reset")
	set_gpio("ADMV1420_RX_RST_0", 0)
	set_gpio("ADMV1420_RX_RST_1", 0)
	set_gpio("ADMV1420_RX_RST_2", 0)
	set_gpio("ADMV1420_RX_RST_3", 0)

def disable_tx_channels():
	"""Disable all ADMV1320 TX channels and put them in reset"""
	print("Disable TX channels CEN")
	set_gpio("ADMV1320_TX_CEN_0", 0)
	set_gpio("ADMV1320_TX_CEN_1", 0)
	set_gpio("ADMV1320_TX_CEN_2", 0)
	set_gpio("ADMV1320_TX_CEN_3", 0)
	
	print("Enable TX channels Reset")
	set_gpio("ADMV1320_TX_RST_0", 0)
	set_gpio("ADMV1320_TX_RST_1", 0)
	set_gpio("ADMV1320_TX_RST_2", 0)
	set_gpio("ADMV1320_TX_RST_3", 0)

	print("Disable TX channels PS")
	set_gpio("ADMV1320_TX_PS_L_0", 0)
	set_gpio("ADMV1320_TX_PS_L_1", 0)
	set_gpio("ADMV1320_TX_PS_L_2", 0)
	set_gpio("ADMV1320_TX_PS_L_3", 0)

def enable_rx_channels():
	"""Enable all ADMV1420 RX channels by releasing reset and enabling CEN"""
	print("Releasing RX channels Reset")
	set_gpio("ADMV1420_RX_RST_0", 1)
	set_gpio("ADMV1420_RX_RST_1", 1)
	set_gpio("ADMV1420_RX_RST_2", 1)
	set_gpio("ADMV1420_RX_RST_3", 1)
	
	print("Enable RX channels CEN")
	set_gpio("ADMV1420_RX_CEN_0", 1)
	set_gpio("ADMV1420_RX_CEN_1", 1)
	set_gpio("ADMV1420_RX_CEN_2", 1)
	set_gpio("ADMV1420_RX_CEN_3", 1)

def enable_tx_channels():
	"""Enable all ADMV1320 TX channels by releasing reset and enabling CEN"""
	print("Releasing TX channels Reset")
	set_gpio("ADMV1320_TX_RST_0", 1)
	set_gpio("ADMV1320_TX_RST_1", 1)
	set_gpio("ADMV1320_TX_RST_2", 1)
	set_gpio("ADMV1320_TX_RST_3", 1)

	print("Enable TX channels CEN")
	set_gpio("ADMV1320_TX_CEN_0", 1)
	set_gpio("ADMV1320_TX_CEN_1", 1)
	set_gpio("ADMV1320_TX_CEN_2", 1)
	set_gpio("ADMV1320_TX_CEN_3", 1)

	print("Enable TX channels PS")
	set_gpio("ADMV1320_TX_PS_L_0", 1)
	set_gpio("ADMV1320_TX_PS_L_1", 1)
	set_gpio("ADMV1320_TX_PS_L_2", 1)
	set_gpio("ADMV1320_TX_PS_L_3", 1)

def power_up():
	"""Power up the device"""
	disable_rx_channels()
	disable_tx_channels()
	print("Power UP Neponset ...")
	set_gpio("BASE_PGOOD", 0)

def power_down():
	"""Power down the device"""
	disable_rx_channels()
	disable_tx_channels()
	print("Power DOWN Neponset ...")
	set_gpio("BASE_PGOOD", 1)

def initialize_devices():
	"""Initialize and configure all ADMV devices to 4-wire SPI"""
	print("Initializing and configuring ADMV devices...")

	# Initialize and configure RX devices
	for i in range(4):
		# ADMV1420 RX devices
		try:
			device_obj = neponset.find_device(f"admv1420_rx_{i}")
			device[f"admv1420_rx_{i}"] = device_obj
			print(f"admv1420_rx_{i} initialized")
			
			# Configure device and mark as ready if successful
			if configure_device_channel(device_obj, "ADMV1420", 0x68):
				device_ready[f"admv1420_rx_{i}"] = True
				
		except Exception as e:
			print(f"Warning: Could not find admv1420_rx_{i}: {e}")

		# ADMV8827 RX devices
		try:
			device_obj = neponset.find_device(f"admv8827_rx_{i}")
			device[f"admv8827_rx_{i}"] = device_obj
			print(f"admv8827_rx_{i} initialized")

			# Configure device and mark as ready if successful
			if configure_device_channel(device_obj, "ADMV8827 RX", 0x27):
				device_ready[f"admv8827_rx_{i}"] = True
				
		except Exception as e:
			print(f"Warning: Could not find admv8827_rx_{i}: {e}")

		# ADMV8809 RX devices
		try:
			device_obj = neponset.find_device(f"admv8809_rx_{i}")
			device[f"admv8809_rx_{i}"] = device_obj
			print(f"admv8809_rx_{i} initialized")
			
			# Configure device and mark as ready if successful
			if configure_device_channel(device_obj, "ADMV8809", 0x09):
				device_ready[f"admv8809_rx_{i}"] = True


		except Exception as e:
			print(f"Warning: Could not find admv8809_rx_{i}: {e}")
	
	# Initialize and configure TX devices
	for i in range(4):
		# ADMV1320 TX devices
		try:
			device_obj = neponset.find_device(f"admv1320_tx_{i}")
			device[f"admv1320_tx_{i}"] = device_obj
			print(f"admv1320_tx_{i} initialized")

			# Configure device and mark as ready if successful
			if configure_device_channel(device_obj, "ADMV1320", 0x67):
				device_ready[f"admv1320_tx_{i}"] = True
				
		except Exception as e:
			print(f"Warning: Could not find admv1320_tx_{i}: {e}")

		# ADMV8827 TX devices
		try:
			device_obj = neponset.find_device(f"admv8827_tx_{i}")
			device[f"admv8827_tx_{i}"] = device_obj
			print(f"admv8827_tx_{i} initialized")
			
			# Configure device and mark as ready if successful
			if configure_device_channel(device_obj, "ADMV8827 TX", 0x27):
				device_ready[f"admv8827_tx_{i}"] = True
				
		except Exception as e:
			print(f"Warning: Could not find admv8827_tx_{i}: {e}")

		# ADMV8909 TX devices
		try:
			device_obj = neponset.find_device(f"admv8909_tx_{i}")
			device[f"admv8909_tx_{i}"] = device_obj
			print(f"admv8909_tx_{i} initialized")

			# Configure device and mark as ready if successful
			if configure_device_channel(device_obj, "ADMV8909", 0x09):
				device_ready[f"admv8909_tx_{i}"] = True
				
		except Exception as e:
			print(f"Warning: Could not find admv8909_tx_{i}: {e}")

		# Lo devices
		try:
			device_obj = neponset.find_device(f"hmc7003_lo_{i}")
			device[f"hmc7003_lo_{i}"] = device_obj
			print(f"hmc7003_lo_{i} initialized")

			# LO devices are automatically marked as ready
			device_ready[f"hmc7003_lo_{i}"] = True
		except Exception as e:
			print(f"Warning: Could not find hmc7003_lo_{i}: {e}")

	# Print configuration summary
	print("\n" + "="*60)
	print("Device Status Summary")
	print("="*60)
	
	# Count ready devices by type
	device_counts = {
		'ADMV1420': sum(1 for name in device_ready if 'admv1420' in name and device_ready[name]),
		'ADMV8827_RX': sum(1 for name in device_ready if 'admv8827_rx' in name and device_ready[name]),
		'ADMV8827_TX': sum(1 for name in device_ready if 'admv8827_tx' in name and device_ready[name]),
		'ADMV8809': sum(1 for name in device_ready if 'admv8809' in name and device_ready[name]),
		'ADMV1320': sum(1 for name in device_ready if 'admv1320' in name and device_ready[name]),
		'ADMV8909': sum(1 for name in device_ready if 'admv8909' in name and device_ready[name]),
		'HMC7003_LO': sum(1 for name in device_ready if 'hmc7003' in name and device_ready[name])
	}
	
	for device_type, count in device_counts.items():
		status = "SUCCESS" if count == 4 else f"PARTIAL ({count}/4)"
		print(f"{device_type}: {status}")
	
	# Check if all devices are ready and provide appropriate completion message
	total_ready = sum(device_counts.values())
	total_expected = 28  # 7 device types × 4 channels each
	
	print("\n" + "="*60)
	if total_ready == total_expected:
		print("ALL DEVICES INITIALIZED AND CONFIGURED SUCCESSFULLY!")
	else:
		failed_count = total_expected - total_ready
		print(f"WARNING: DEVICE INITIALIZATION INCOMPLETE!")
		print(f"   Ready: {total_ready}/{total_expected} devices")
		print(f"   Failed: {failed_count} devices")
		print("   Check error messages above for details.")
	print("="*60)


def configure_device_channel(device, device_name, expected_id):
	"""Configure a single device to 4-wire SPI"""
	if device is None:
		print(f"  {device_name}: Device not available")
		return False
	
	try:
		# Write register 0x0 with value 0x81 (soft reset)
		device.reg_write(0x0, 0x81)
		
		# Write register 0x0 with value 0x18 (4-wire SPI mode setup)
		device.reg_write(0x0, 0x18)
		
		# Read Product ID register 0x4
		reg_value = device.reg_read(0x4)
		print(f"  {device_name} Product ID: 0x{reg_value:02x}")

		# Verify Product ID for successful configuration
		if reg_value == expected_id:
			print(f"  {device_name} configuration SUCCESSFUL")
			return True
		else:
			print(f"  {device_name} configuration FAILED - Expected 0x{expected_id:02x}, got 0x{reg_value:02x}")
			return False
			
	except Exception as e:
		print(f"  Error configuring {device_name}: {e}")
		return False

# Example function demonstrating direct device access (can be done the same for other devices)
def test_admv8909_tx_0_scratchpad():
	"""Example showing how to use devices directly - only if properly configured"""

	# Check if device is ready (initialized AND configured with correct product ID)
	if device_ready['admv8909_tx_0']:
		try:
			# Write scratch pad register for ADMV8909 TX Channel 0
			device['admv8909_tx_0'].reg_write(0xA, 0xEB)
			reg_value = device['admv8909_tx_0'].reg_read(0xA)
	
			print(f"ADMV8909 TX Channel 0 Scratch Pad Register 0xA: 0x{reg_value:02x}")

		except Exception as e:
			print(f"Error accessing ADMV8909 TX Channel 0: {e}")
	else:
		print("ADMV8909 TX Channel 0 is not ready - device not properly configured")

# Main execution
def main():
	"""Main function to initialize and configure all devices"""
	print("="*60)
	print("Neponset Board Initialization")
	print("="*60)
	
	# Power up Neponset and enable RX and TX channels
	power_up()
	time.sleep(1)
	enable_rx_channels()
	enable_tx_channels()
	
	print("\n" + "="*60)
	print("Device Initialization and Configuration")
	print("="*60)
	
	# Initialize and configure all ADMV devices in one step
	results = initialize_devices()
	
if __name__ == "__main__":
	main()
	
	# Uncomment below to run individual device examples functions
	test_admv8909_tx_0_scratchpad()
