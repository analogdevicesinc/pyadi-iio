#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
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
################################################################################

# Author: Ryu Woon Jung (Leon)

#
# *********     Factory Reset Example      *********
#
#
# Available Dynamixel model on this example : All models using Protocol 1.0
# This example is tested with a Dynamixel MX-28, and an USB2DYNAMIXEL
# Be sure that Dynamixel PRO properties are already set as %% ID : 1 / Baudnum : 34 (Baudrate : 57600)
#

# Be aware that:
# This example resets all properties of Dynamixel to default values, such as %% ID : 1 / Baudnum : 34 (Baudrate : 57600)
#


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

# Control table address
ADDR_MX_BAUDRATE            = 8                 # Control table address is different in Dynamixel model

# Protocol version
PROTOCOL_VERSION            = 1.0               # See which protocol version is used in the Dynamixel

# Default setting
DXL_ID                      = 1                 # Dynamixel ID : 1
BAUDRATE                    = 57600             # Dynamixel default baudrate : 57600
DEVICENAME                  = '/dev/ttyUSB0'    # Check which port is being used on your controller
                                                # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

FACTORYRST_DEFAULTBAUDRATE  = 57600             # Dynamixel baudrate set by factoryreset
NEW_BAUDNUM                 = 1                 # New baudnum to recover Dynamixel baudrate as it was
OPERATION_MODE              = 0x00              # Mode is unavailable in Protocol 1.0 Reset

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
dxl_baudnum_read, dxl_comm_result, dxl_error = packetHandler.read1ByteTxRx(portHandler, DXL_ID, ADDR_MX_BAUDRATE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
else:
    print("[ID:%03d] DXL baudnum is now : %d" % (DXL_ID, dxl_baudnum_read))

# Write new baudnum
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_BAUDRATE, NEW_BAUDNUM)
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
dxl_baudnum_read, dxl_comm_result, dxl_error = packetHandler.read1ByteTxRx(portHandler, DXL_ID, ADDR_MX_BAUDRATE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
else:
    print("[ID:%03d] Dynamixel Baudnum is now : %d" % (DXL_ID, dxl_baudnum_read))

# Close port
portHandler.closePort()