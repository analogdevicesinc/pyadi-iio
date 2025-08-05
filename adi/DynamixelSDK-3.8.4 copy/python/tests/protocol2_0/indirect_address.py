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


#*******************************************************************************
#***********************     Indirect Address Example      ***********************
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

from dynamixel_sdk import *                          # Uses Dynamixel SDK library

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
    ADDR_TORQUE_ENABLE                  = 64
    ADDR_LED_RED                        = 65
    LEN_LED_RED                         = 1          # Data Byte Length
    ADDR_GOAL_POSITION                  = 116
    LEN_GOAL_POSITION                   = 4          # Data Byte Length
    ADDR_MOVING                         = 122
    LEN_MOVING                          = 1          # Data Byte Length
    ADDR_PRESENT_POSITION               = 132
    LEN_PRESENT_POSITION                = 4          # Data Byte Length
    ADDR_INDIRECTADDRESS_FOR_WRITE      = 168
    LEN_INDIRECTDATA_FOR_WRITE          = 5          # Sum of Data of Length. i.e) LED (1 byte) + Goal Position data (4 bytes)
    ADDR_INDIRECTADDRESS_FOR_READ       = 178
    LEN_INDIRECTDATA_FOR_READ           = 5          # Sum of Data of Length. i.e) Moving (1 byte) + Present Position data (4 bytes)
    ADDR_INDIRECTDATA_FOR_WRITE         = 224
    ADDR_INDIRECTDATA_FOR_READ          = 229
    DXL_MINIMUM_POSITION_VALUE          = 0          # Refer to the Minimum Position Limit of product eManual
    DXL_MAXIMUM_POSITION_VALUE          = 4095       # Refer to the Maximum Position Limit of product eManual
    BAUDRATE                            = 57600
elif MY_DXL == 'PRO_SERIES':
    ADDR_INDIRECTADDRESS_FOR_WRITE      = 49
    ADDR_INDIRECTADDRESS_FOR_READ       = 59
    ADDR_TORQUE_ENABLE                  = 562        # Control table address is different in DYNAMIXEL model
    ADDR_LED_RED                        = 563        # R.G.B Address: 563 (red), 564 (green), 565 (blue)
    LEN_LED_RED                         = 1          # Data Byte Length
    ADDR_GOAL_POSITION                  = 596
    LEN_GOAL_POSITION                   = 4          # Data Byte Length
    ADDR_MOVING                         = 610
    LEN_MOVING                          = 1          # Data Byte Length
    ADDR_PRESENT_POSITION               = 611
    LEN_PRESENT_POSITION                = 4          # Data Byte Length
    ADDR_INDIRECTDATA_FOR_WRITE         = 634
    LEN_INDIRECTDATA_FOR_WRITE          = 5          # Sum of Data of Length. i.e) LED (1 byte) + Goal Position data (4 bytes)
    ADDR_INDIRECTDATA_FOR_READ          = 639
    LEN_INDIRECTDATA_FOR_READ           = 5          # Sum of Data of Length. i.e) Moving (1 byte) + Present Position data (4 bytes)
    DXL_MINIMUM_POSITION_VALUE          = -150000    # Refer to the Minimum Position Limit of product eManual
    DXL_MAXIMUM_POSITION_VALUE          = 150000     # Refer to the Maximum Position Limit of product eManual
    BAUDRATE                            = 57600
elif MY_DXL == 'P_SERIES' or MY_DXL == 'PRO_A_SERIES':
    ADDR_INDIRECTADDRESS_FOR_WRITE      = 168
    ADDR_INDIRECTADDRESS_FOR_READ       = 178
    ADDR_TORQUE_ENABLE                  = 512        # Control table address is different in DYNAMIXEL model
    ADDR_LED_RED                        = 513        # R.G.B Address: 513 (red), 544 (green), 515 (blue)
    LEN_LED_RED                         = 1          # Data Byte Length
    ADDR_GOAL_POSITION                  = 564
    LEN_GOAL_POSITION                   = 4          # Data Byte Length
    ADDR_MOVING                         = 570
    LEN_MOVING                          = 1          # Data Byte Length
    ADDR_PRESENT_POSITION               = 580
    LEN_PRESENT_POSITION                = 4          # Data Byte Length
    ADDR_INDIRECTDATA_FOR_WRITE         = 634
    LEN_INDIRECTDATA_FOR_WRITE          = 5          # Sum of Data of Length. i.e) LED (1 byte) + Goal Position data (4 bytes)
    ADDR_INDIRECTDATA_FOR_READ          = 639
    LEN_INDIRECTDATA_FOR_READ           = 5          # Sum of Data of Length. i.e) Moving (1 byte) + Present Position data (4 bytes)
    DXL_MINIMUM_POSITION_VALUE          = -150000    # Refer to the Minimum Position Limit of product eManual
    DXL_MAXIMUM_POSITION_VALUE          = 150000     # Refer to the Maximum Position Limit of product eManual
    BAUDRATE                            = 57600

# DYNAMIXEL Protocol Version (1.0 / 2.0)
# https://emanual.robotis.com/docs/en/dxl/protocol2/
PROTOCOL_VERSION            = 2.0

# Factory default ID of all DYNAMIXEL is 1
DXL_ID                      = 1

# Use the actual port assigned to the U2D2.
# ex) Windows: "COM*", Linux: "/dev/ttyUSB*", Mac: "/dev/tty.usbserial-*"
DEVICENAME                  = '/dev/ttyUSB0'

TORQUE_ENABLE               = 1                     # Value for enabling the torque
TORQUE_DISABLE              = 0                     # Value for disabling the torque
DXL_MINIMUM_LED_VALUE       = 0                     # Dynamixel LED will light between this value
DXL_MAXIMUM_LED_VALUE       = 1                     # and this value
DXL_MOVING_STATUS_THRESHOLD = 20                    # Dynamixel moving status threshold

index = 0
dxl_goal_position = [DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE]        # Goal position
dxl_led_value = [DXL_MINIMUM_LED_VALUE, DXL_MAXIMUM_LED_VALUE]                      # Dynamixel LED value

# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
# Set the protocol version
# Get methods and members of Protocol1PacketHandler or Protocol2PacketHandler
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Initialize GroupSyncWrite instance
groupSyncWrite = GroupSyncWrite(portHandler, packetHandler, ADDR_INDIRECTDATA_FOR_WRITE, LEN_INDIRECTDATA_FOR_WRITE)

# Initialize GroupSyncRead instace for Present Position
groupSyncRead = GroupSyncRead(portHandler, packetHandler, ADDR_INDIRECTDATA_FOR_READ, LEN_INDIRECTDATA_FOR_READ)

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


# Disable Dynamixel Torque :
# Indirect address would not accessible when the torque is already enabled
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
else:
    print("[ID:%03d] Dynamixel has been successfully connected" % DXL_ID)

# INDIRECTDATA parameter storages replace LED, goal position, present position and moving status storages
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_WRITE + 0, ADDR_GOAL_POSITION + 0)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_WRITE + 2, ADDR_GOAL_POSITION + 1)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_WRITE + 4, ADDR_GOAL_POSITION + 2)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_WRITE + 6, ADDR_GOAL_POSITION + 3)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_WRITE + 8, ADDR_LED_RED)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))

dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_READ + 0, ADDR_PRESENT_POSITION + 0)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_READ + 2, ADDR_PRESENT_POSITION + 1)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_READ + 4, ADDR_PRESENT_POSITION + 2)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_READ + 6, ADDR_PRESENT_POSITION + 3)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_INDIRECTADDRESS_FOR_READ + 8, ADDR_MOVING)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))

# Enable Dynamixel Torque
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))


# Add parameter storage for multiple values
dxl_addparam_result = groupSyncRead.addParam(DXL_ID)
if dxl_addparam_result != True:
    print("[ID:%03d] groupSyncRead addparam failed" % DXL_ID)
    quit()

while 1:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):
        break

    # Allocate goal position value into byte array
    param_indirect_data_for_write = [DXL_LOBYTE(DXL_LOWORD(dxl_goal_position[index])), DXL_HIBYTE(DXL_LOWORD(dxl_goal_position[index])), DXL_LOBYTE(DXL_HIWORD(dxl_goal_position[index])), DXL_HIBYTE(DXL_HIWORD(dxl_goal_position[index]))]
    param_indirect_data_for_write.append(dxl_led_value[index])

    # Add values to the Syncwrite parameter storage
    dxl_addparam_result = groupSyncWrite.addParam(DXL_ID, param_indirect_data_for_write)
    if dxl_addparam_result != True:
        print("[ID:%03d]groupSyncWrite addparam failed" % DXL_ID)
        quit()

    # Syncwrite all
    dxl_comm_result = groupSyncWrite.txPacket()
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))

    # Clear syncwrite parameter storage
    groupSyncWrite.clearParam()

    while 1:
        # Syncread present position from indirectdata2
        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(dxl_comm_result))

        # Check if groupsyncread data of Dynamixel present position value is available
        dxl_getdata_result = groupSyncRead.isAvailable(DXL_ID, ADDR_INDIRECTDATA_FOR_READ, LEN_PRESENT_POSITION)
        if dxl_getdata_result != True:
            print("[ID:%03d] groupSyncRead getdata failed" % DXL_ID)
            quit()

        # Check if groupsyncread data of Dynamixel moving status is available
        dxl_getdata_result = groupSyncRead.isAvailable(DXL_ID, ADDR_INDIRECTDATA_FOR_READ + LEN_PRESENT_POSITION, LEN_MOVING)
        if dxl_getdata_result != True:
            print("[ID:%03d] groupSyncRead getdata failed" % DXL_ID)
            quit()

        # Get Dynamixel present position value
        dxl_present_position = groupSyncRead.getData(DXL_ID, ADDR_INDIRECTDATA_FOR_READ, LEN_PRESENT_POSITION)

        # Get Dynamixel moving status value
        dxl_moving = groupSyncRead.getData(DXL_ID, ADDR_INDIRECTDATA_FOR_READ + LEN_PRESENT_POSITION, LEN_MOVING)

        print("[ID:%03d] GoalPos:%d  PresPos:%d  IsMoving:%d" % (DXL_ID, dxl_goal_position[index], dxl_present_position, dxl_moving))

        if not (abs(dxl_goal_position[index] - dxl_present_position) > DXL_MOVING_STATUS_THRESHOLD):
            break

    # Change goal position
    if index == 0:
        index = 1
    else:
        index = 0

# Clear syncread parameter storage
groupSyncRead.clearParam()

# Disable Dynamixel Torque
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))

# Close port
portHandler.closePort()
