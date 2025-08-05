from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Set these parameters:
DEVICENAME = '/dev/ttyUSB2'
BAUDRATE = 57600  # Try 57600, 115200, 1_000_000, etc.
PROTOCOL_VERSION = 2.0  # Try 2.0 if unsure
SCAN_RANGE = range(0, 253)

# Initialize PortHandler and PacketHandler
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if portHandler.openPort():
    print(f"Opened port {DEVICENAME}")
else:
    print(f"Failed to open port {DEVICENAME}")
    quit()

if portHandler.setBaudRate(BAUDRATE):
    print(f"Set baudrate to {BAUDRATE}")
else:
    print(f"Failed to set baudrate")
    quit()

print("Scanning for Dynamixel IDs...")
found = []
for dxl_id in SCAN_RANGE:
    dxl_model_number, dxl_comm_result, dxl_error = packetHandler.ping(portHandler, dxl_id)
    if dxl_comm_result == COMM_SUCCESS and dxl_error == 0:
        print(f"[SUCCESS] Found Dynamixel ID: {dxl_id}  (Model: {dxl_model_number})")
        found.append(dxl_id)
    elif dxl_comm_result != COMM_TX_FAIL:
        print(f"[FAIL] ID {dxl_id}: {packetHandler.getTxRxResult(dxl_comm_result)}")

portHandler.closePort()

if not found:
    print("⚠️ No Dynamixel devices found.")
