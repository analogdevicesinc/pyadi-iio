#!/usr/bin/env python
# -*- coding: utf-8 -*-

#*******************************************************************************
# Copyright 2017 ROBOTIS CO., LTD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#*******************************************************************************

# Author: Ryu Woon Jung (Leon)

#*******************************************************************************
#***********************     Factory Reset Example      ***********************
#  Required Environment to run this example :
#    - Protocol 2.0 supported DYNAMIXEL(X, P, PRO/PRO(A), MX 2.0 series)
#    - DYNAMIXEL Starter Set (U2D2, U2D2 PHB, 12V SMPS)
#  How to use the example :
#    - Select the DYNAMIXEL in use at the MY_DXL in the example code.
#    - Build and Run from proper architecture subdirectory.
#    - For ARM based SBCs such as Raspberry Pi, use linux_sbc subdirectory to build and run.
#    - https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/
#  Author: Ryu Woon Jung (Leon)
#  Maintainer : Zerom, Will Son
# *******************************************************************************

import os
from time import sleep

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from dynamixel_sdk import *                 # Uses Dynamixel SDK library

#********* DYNAMIXEL Model definition *********
#***** (Use only one definition at a time) *****
MY_DXL = 'X_SERIES'       # X330 (5.0 V recommended), X430, X540, 2X430
# MY_DXL = 'MX_SERIES'    # MX series with 2.0 firmware update.
# MY_DXL = 'PRO_SERIES'   # H54, H42, M54, M42, L54, L42
# MY_DXL = 'PRO_A_SERIES' # PRO series with (A) firmware update.
# MY_DXL = 'P_SERIES'     # PH54, PH42, PM54
# MY_DXL = 'XL320'        # [WARNING] Operating Voltage : 7.4V


# Control table address
if MY_DXL == 'X_SERIES' or MY_DXL == 'MX_SERIES':
# [Note] For your convenience, the factory reset example uses the DYNAMIXEL's default baudrate (depending on the DYNAMIXEL in use. See MY_DXL) in the current example, so you can simply connect your DYNAMIXEL in default setting and test.
# [Note] For further test, set the different baudrate other than the current baudrate in this example via a manage tool such as DYNAMIXEL Wizard 2.0, and change the value of BAUDRATE corresponding to the set baudrate.
    BAUDRATE                    = 57600
    ADDR_BAUDRATE               = 8         # Control table address
    FACTORYRST_DEFAULTBAUDRATE  = 57600     # Dynamixel baudrate set by factoryreset
# NEW_BAUDNUM turns the connected DYNAMIXEL to the previous baudrate setting for your convenience. Use NEW_BAUDNUM if you perform factory_reset.py if using different BAUDRATE in the code. See [Note] Line # 73 to 74.
# Go to "Control Table" in your DYNAMIXEL e-Manual, and see available NEW_BAUDNUM's valule to use.
    NEW_BAUDNUM                 = 1
elif MY_DXL == 'PRO_SERIES':
    BAUDRATE                    = 57600
    ADDR_BAUDRATE               = 8
    FACTORYRST_DEFAULTBAUDRATE  = 57600
    NEW_BAUDNUM                 = 1
elif MY_DXL == 'P_SERIES' or MY_DXL == 'PRO_A_SERIES':
    BAUDRATE                    = 57600
    ADDR_BAUDRATE               = 8
    FACTORYRST_DEFAULTBAUDRATE  = 57600
    NEW_BAUDNUM                 = 1
elif MY_DXL == 'XL320':
    BAUDRATE                    = 1000000   # Default Baudrate of XL-320 is 1Mbps
    ADDR_BAUDRATE               = 4
    FACTORYRST_DEFAULTBAUDRATE  = 1000000
    NEW_BAUDNUM                 = 3

# DYNAMIXEL Protocol Version (1.0 / 2.0)
# https://emanual.robotis.com/docs/en/dxl/protocol2/
PROTOCOL_VERSION            = 2.0

# Factory default ID of all DYNAMIXEL is 1
DXL_ID                      = 1

# Use the actual port assigned to the U2D2.
# ex) Windows: "COM*", Linux: "/dev/ttyUSB*", Mac: "/dev/tty.usbserial-*"
DEVICENAME                  = '/dev/ttyUSB0'

OPERATION_MODE              = 0x01              # 0xFF : reset all values
                                                # 0x01 : reset all values except ID
                                                # 0x02 : reset all values except ID and baudrate

# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
# Set the protocol version
# Get methods and members of Protocol1PacketHandler or Protocol2PacketHandler
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open port
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()

# Set port baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

# Read present baudrate of the controller
print("Now the controller baudrate is : %d" % portHandler.getBaudRate())

# Try factoryreset
print("[ID:%03d] Try factoryreset : " % DXL_ID)

dxl_comm_result, dxl_error = packetHandler.factoryReset(portHandler, DXL_ID, OPERATION_MODE)
if dxl_comm_result != COMM_SUCCESS:
    print("Aborted")
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    quit()
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))

# Wait for reset
print("Wait for reset...")
sleep(2.0)
print("[ID:%03d] factoryReset Success!" % DXL_ID)

# Set controller baudrate to Dynamixel default baudrate
if portHandler.setBaudRate(FACTORYRST_DEFAULTBAUDRATE):
    print("Succeeded to change the controller baudrate to : %d" % FACTORYRST_DEFAULTBAUDRATE)
else:
    print("Failed to change the controller baudrate")
    print("Press any key to terminate...")
    quit()


# Read Dynamixel baudnum
dxl_baudnum_read, dxl_comm_result, dxl_error = packetHandler.read1ByteTxRx(portHandler, DXL_ID, ADDR_BAUDRATE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
else:
    print("[ID:%03d] DXL baudnum is now : %d" % (DXL_ID, dxl_baudnum_read))

# Write new baudnum
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_BAUDRATE, NEW_BAUDNUM)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
else:
    print("[ID:%03d] Set Dynamixel baudnum to : %d" % (DXL_ID, NEW_BAUDNUM))

# Set port baudrate to BAUDRATE
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the controller baudrate to : %d" % BAUDRATE)
else:
    print("Failed to change the controller baudrate")
    print("Press any key to terminate...")
    quit()

sleep(0.2)

# Read Dynamixel baudnum
dxl_baudnum_read, dxl_comm_result, dxl_error = packetHandler.read1ByteTxRx(portHandler, DXL_ID, ADDR_BAUDRATE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
else:
    print("[ID:%03d] Dynamixel Baudnum is now : %d" % (DXL_ID, dxl_baudnum_read))

# Close port
portHandler.closePort()
