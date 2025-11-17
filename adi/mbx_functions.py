#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Copyright 2017 ROBOTIS CO., LTD.
#
# Copyright 2018-2022 MILLIWAVE SILICON SOLUTIONS, inc.

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

# Author: Ryu Woon Jung (Leon) ROBOTIS
# Author: Jeanmarc Laurent, Chinh Doan - Milliwave Silicon Solutions
#
# *********     MILLIBOX FUNCTIONS      *********
#   Gimbal registers
#   Gimbal movement control
#   Equipment selection and measurement
#   Sweep functions
#

# IMPORTS
from __future__ import division                             # division compatibility Python 2.7 and Python 3.6+
import os
import sys
import csv
import datetime
import time
import six

from mbx_realtimeplot import *
import numpy as np
import matplotlib.pyplot as plt
import mbx_instrument as equip
import dynamixel_functions as dynamixel                     # Uses Dynamixel SDK library

if sys.platform == "win32":                                 # if we run windows, we can use getch from OS
    from msvcrt import getch, kbhit
else:                                                       # but if we use MACos or Linux we need to create getch()
    def getch():
        x = six.moves.input()
        if len(x) > 1:
            x = chr(0)
            print("too long")
        elif len(x) == 0:
            x = chr(13)  # enter
            print("enter")
        return x

    def kbhit():
        return False


# Register set for MX64AT
# EEPROM SPACE               ADDRESS                       SIZE     R/W    DEFAULT    DESCRIPTION
ADD_MODEL_NUMBER                 = 0                           # 	2   R      311        Model Number for MX64AT(2.0)
ADD_MODEL                        = 2                           #    4   R      -          Model Information
ADD_FW_VER                       = 6                           #    1   R      -          Firmware Version  should stay 41
ADD_MOTOR_ID                     = 7                           #    1 	RW     1          ID 	DYNAMIXEL ID set H to 1 V to 2
ADD_BAUD_RATE                    = 8                           #    1   RW     1          Communication Baud Rate 	 SET to 3 -> 1Mbps
ADD_RETURN_TIME                  = 9                           #    1   RW     250        Return Delay Time
ADD_DRIVE_MODE                   = 10                          #    1   RW     0          Drive Mode
ADD_OPERATING_MODE               = 11                          #    1   RW     3          Operating Mode
ADD_SEC_ID                       = 12                          #    1   RW     255        Secondary(Shadow) ID
ADD_PROTOCOL                     = 13                          #    1   RW     2          Protocol Version
ADD_HOME_OFFSET                  = 20                          #    4   RW     0          Homing Offset
ADD_MOVE_THRESHOLD               = 24                          #    4   RW     10         Velocity Threshold for Movement Detection
ADD_TEMP_LIMIT                   = 31                          #    1   RW     80         Temperature Limit in degree C
ADD_VOLT_MAX_LIMIT               = 32                          #    2 	RW     160        Maximum Input Voltage Limit
ADD_VOLT_MIN_LIMIT               = 34                          #    2 	RW     95         Minimum Input Voltage Limit
ADD_PWM_LIMIT                    = 36                          #    2 	RW     885        Maximum PWM Limit
ADD_MAX_CURRENT                  = 38                          #    2 	RW     1941       Maximum Current Limit
ADD_MAX_ACCEL                    = 40                          #    4 	RW     32767      Maximum Acceleration Limit
ADD_MAX_VELOCITY                 = 44                          #    4 	RW     435        Maximum Velocity Limit
ADD_MAX_POS                      = 48                          #    4 	RW     4095       Maximum Position Limit
ADD_MIN_POS                      = 52                          #    4 	RW     0          Minimum Position Limit
ADD_ERROR_INFO                   = 63                          #    1 	RW     52         Shutdown Error Information

# RAM  SPACE                 ADDRESS                       SIZE     R/W    DEFAULT    DESCRIPTION
ADD_TORQUE_ENABLE                = 64                          #    1 	RW     0          Motor Torque On/Off
ADD_LED                          = 65                          #    1 	RW     0          Status LED On/Off
ADD_STATUS                       = 68                          #    1 	RW     2          Select Types of Status Return
ADD_REG_WRITE_FLAG               = 69                          #    1 	R      0          REG_WRITE Instruction Flag
ADD_HW_ERROR                     = 70                          #    1 	R      0          Hardware Error Status
ADD_VEL_I_GAIN                   = 76                          #    2 	RW     1920       I Gain of Velocity
ADD_VEL_P_GAIN                   = 78                          #    2 	RW     100        P Gain of Velocity
ADD_POS_D_GAIN                   = 80                          #    2 	RW     0          D Gain of Position
ADD_POS_I_GAIN                   = 82                          #    2 	RW     0          I Gain of Position
ADD_POS_P_GAIN                   = 84                          #    2 	RW     850        P Gain of Position
ADD_FF_2ND_GAIN                  = 88                          #    2 	RW     0          2nd Gain of Feed-Forward
ADD_FF_1ST_GAIN                  = 90                          #    2 	RW     0          1st Gain of Feed-Forward
ADD_WATCHDOG                     = 98                          #    1 	RW     0          Dynamixel BUS Watchdog
ADD_GOAL_PWM                     = 100                         #    2 	RW     -          Target PWM Value
ADD_GOAL_CURRENT                 = 102                         #    2 	RW     -          Target Current Value
ADD_GOAL_VELOC                   = 104                         #    4 	RW     -          Target Velocity Value
ADD_ACCEL_PROFILE                = 108                         #    4 	RW     0          Acceleration Value of Profile
ADD_VELOC_PROFILE                = 112                         #    4   RW     0          Velocity Value of Profile
ADD_GOAL_POSITION                = 116                         #    4 	RW     0          Target Position
ADD_TIME_TICK                    = 120 	                       #    2 	R      -          Count Time in Millisecond
ADD_MOVING                       = 122                         #    1 	R      0          Moving 	Movement Flag
ADD_MOVING_STATUS                = 123 	                       #    1 	R      0          Detailed Information of Movement Status
ADD_PRESENT_PWM                  = 124                         #    2 	R      -          Present PWM Value
ADD_PRESENT_CURR                 = 126                         #    2 	R      -          Present Current Value
ADD_PRESENT_VELOC                = 128                         #    4 	R      -          Present Velocity Value
ADD_PRESENT_POS                  = 132 	                       #    4 	R      -          Present Position Value
ADD_VELOC_TRAJ                   = 136                         #    4 	R      -          Target Velocity Trajectory from Profile
ADD_POS_TRAJ                     = 140                         #    4 	R      -          Target Position Trajectory from Profile
ADD_PRESENT_VOLT                 = 144                         #    2 	R      -          Present Input Voltage
ADD_PRESENT_TEMP                 = 146 	                       #    1   R      -          Present Internal Temperature


# SET GLOBALS
PROTOCOL_VERSION            = 2                         # See which protocol version is used in the Dynamixel
H                           = 1                         # Horizontal Motor is ID: 1
V                           = 2                         # Vertical Motor  is ID: 2
R                           = 3                         # Reverse Vertical motor is ID: 3 in case of GIM03 gimbal
P                           = 4                         # Polarization motor is ID: 4
T                           = 5                         # GIM05 Theta Rotation on Gimbal side
Z                           = 6                         # GIM05 Horn Polarization on Horn post side
TH                          = 101                       # "Virtual" theta motor - mapped to H motor
PH                          = 105                       # "Virtual" phi motor - mapped to T/Z motors
DPH                         = 106                       # "Virtual" dphi motor - mapped to T/Z motor
GIM03_MOTOR_TYPE            = 1100                      # X series motors
GIM04_MOTOR_TYPE            = 2000                      # P motor series
OPER_MODE                   = 4                         # Operating mode set to multiturn
TORQUE_ENABLE               = 1                         # Value for enabling the torque
TORQUE_DISABLE              = 0                         # Value for disabling the torque
ESC_ASCII_VALUE             = 0x1b
COMM_SUCCESS                = 0                         # Communication Success result value
COMM_TX_FAIL                = -1001                     # Communication Tx Failed
H_MOVING_THRESHOLD          = 0                         # resolution for movement detection
HP_MOVING_THRESHOLD         = 5                         # resolution for movement detection: P motor series
V_MOVING_THRESHOLD          = 0                         # resolution for movement detection
P_MOVING_THRESHOLD          = 0                         # resolution for movement detection
T_MOVING_THRESHOLD          = 0                         # resolution for movement detection
Z_MOVING_THRESHOLD          = 0                         # resolution for movement detection
GIM04_RAM_ADD_OFFSET        = 448                       # RAM address offset for P motor series

H_POSITION_D_G              = 50                         # Horizontal D gain
H_POSITION_I_G              = 1000                      # Horizontal I gain
H_POSITION_P_G              = 600                     # Horizontal P gain
H_FF1_G                     = 0                         # Horizontal feed forward gain
HP_POSITION_D_G             = 0                         # base_type 4 Horizontal D gain
HP_POSITION_I_G             = 3000                      # base_type 4 Horizontal I gain
HP_POSITION_P_G             = 3000                      # base_type 4 Horizontal P gain
HP_FF1_G                    = 0                         # base_type 4 Horizontal feed forward gain
V_POSITION_D_G              = 50                         # Vertical D gain
V_POSITION_I_G              = 1000                      # Vertical I gain
V_POSITION_P_G              = 600                      # Vertical P gain
V_FF1_G                     = 0                         # Vertical feed forward gain
P_POSITION_D_G              = 0                         # Polarization D gain
P_POSITION_I_G              = 3000                      # Polarization I gain
P_POSITION_P_G              = 1000                      # Polarization P gain
P_FF1_G                     = 0                         # Polarization feed forward gain

MIN_VERSION                 = 41                        # Minimum version supported
MAX_VELOCITY                = 1023                      # Maximum velocity
MIN_P_VERSION               = 11                        # Minimum version supported for P Motors (GIM04)
MAX_P_VELOCITY              = 2920                      # GMI04 Base velocity
H_PROFILE_VELOCITY          = 1023                      # rotation speed 1023
HP_PROFILE_VELOCITY         = 2920                      # rotation speed
V_PROFILE_VELOCITY          = 200                      # rotation speed
P_PROFILE_VELOCITY          = 200                      # rotation speed
H0                          = 2048                      # center H position relative to H Offset defined
HP0                         = 0                         # center H position relative to H Offset defined (P motor)
V0                          = 2048                      # center V position relative to V Offset defined
P0                          = 2048                      # center P position relative to P Offset defined
T0                          = 2048
Z0                          = 2048
DRIVE_MODE                  = 3                         # slave reverse mode for GIM03 reserse vertical motor
DRIVE_MODE_Z                = 1                         # reverse mode for GIM05 horn post motor
MAX_OFFSET                  = 1044479                   # +/- 255 revolutions is the max supported offset
MAX_OFFSET_P                = 2147483647
H_RATIO                     = 5
G4_H_RATIO                  = 2
V_RATIO                     = 1
P_RATIO                     = 120/50
T_RATIO                     = 120/50
Z_RATIO                     = 2
H_GOAL_VELOCITY             = 1023
HP_GOAL_VELOCITY            = 2920
V_GOAL_VELOCITY             = 1023
P_GOAL_VELOCITY             = 1023
T_GOAL_VELOCITY             = 1023
Z_GOAL_VELOCITY             = 1023
X_RES                       = 4096.0                    # X series resolution
P_RES                       = 607500.0                  # P series resolution for GIM04 base
X_VELOCITY_UNIT             = 0.229                     # X series velocity unit (0.229 rev/min)
P_VELOCITY_UNIT             = 0.01                      # P series velocity unit (0.01 rev/min)
MIN_VERSION_P               = 10
V_ACCELERATION_LIMIT        = 5
HP_ACCELERATION_LIMIT       = 2500
HV                          = 1                         # gim_type 1 is HV coordinate
SPHERICAL                   = 5                         # gim_type 5 is spherical coordinate

POS_ACC_THRESH_H_G1         = 1                         # positional accuracy threshold for HIGH or VERY HIGH accuracy (1/4096)*360/5 = 0.018
POS_ACC_THRESH_H_G4         = 40                        # positional accuracy threshold for HIGH or VERY HIGH accuracy (40/607500)*360/2 = 0.012
POS_ACC_THRESH_V            = 1                         # positional accuracy threshold for HIGH or VERY HIGH accuracy
POS_ACC_THRESH_P            = 1                         # positional accuracy threshold for HIGH or VERY HIGH accuracy
POS_ACC_THRESH_T            = 1                         # positional accuracy threshold for HIGH or VERY HIGH accuracy
POS_ACC_THRESH_Z            = 1                         # positional accuracy threshold for HIGH or VERY HIGH accuracy
OVERSHOOT_H_ANG             = 0                         # in VERY HIGH accuracy mode, overshoot in H direction by 2deg
OVERSHOOT_V_ANG             = 0                         # in VERY HIGH accuracy mode, overshoot in V direction by 2deg
OVERSHOOT_P_ANG             = 2                         # in VERY HIGH accuracy mode, overshoot in P direction by 2deg
OVERSHOOT_T_ANG             = 2                         # in VERY HIGH accuracy mode, overshoot in T direction by 2deg
OVERSHOOT_Z_ANG             = 2                         # in VERY HIGH accuracy mode, overshoot in Z direction by 2deg
OVERSHOOT_TH_ANG            = 2
OVERSHOOT_PH_ANG            = 2
# DEBUG_MOVING                = 1					        # flag to debug movement with extra print statements
DEBUG_MOVING                = 0					        # flag to debug movement with extra print statements

num_motors                  = 2                         # number of gimbal motors (defaults to GIM01 = 2 motors (H&V))
port_num                    = None

# placeholder values (GIM01 base) - these globals will be overwritten during initialiation if GIM04 base is found
base_type                   = 1                         # base_type = 1 for GIM01 and GIM03 and base type is 4 for GIM04 and GIM04_P
base_ratio                  = H_RATIO
base_res                    = X_RES
ram_offset                  = 0
h_zero                      = H0
base_pos_acc_thresh         = POS_ACC_THRESH_H_G1
base_vel_unit               = X_VELOCITY_UNIT
max_H_velocity              = H_PROFILE_VELOCITY
h_P                         = H_POSITION_P_G
h_I                         = H_POSITION_I_G
h_D                         = H_POSITION_D_G
h_FF1                       = H_FF1_G
base_moving_threshold       = H_MOVING_THRESHOLD
gim_type                    = 0


# Initialize PacketHandler Structs
dxl_comm_result = COMM_TX_FAIL                          # Communication result
dxl_error = 0                                           # Dynamixel error


# ============================================
# ============= GIMBAL FUNCTIONS =============
# ============================================

def write1(motor, address, value):
    """ generic function to write 1 Byte to motor register """
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, motor, address, value)
    dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)
    dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)
    if dxl_comm_result != COMM_SUCCESS:
        print(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result))
    elif dxl_error != 0:
        print(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error))
    # else:                                                                      # debug
    #     print("Motor " + str(motor) + " write sucessful")
    return


def write2(motor, address, value):
    """ generic function to write 2 Byte to motor register """
    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, motor, address, value)
    dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)
    dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)
    if dxl_comm_result != COMM_SUCCESS:
        print(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result))
    elif dxl_error != 0:
        print(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error))
    # else:                                                                      # debug
    #     print("Motor " + str(motor) + " write sucessful")
    return


def write4(motor, address, value):
    """ generic function to write 4 Byte to motor register """
    dynamixel.write4ByteTxRx(port_num, PROTOCOL_VERSION, motor, address, value)
    dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)
    dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)
    if dxl_comm_result != COMM_SUCCESS:
        print(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result))
    elif dxl_error != 0:
        print(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error))
    # else:                                                                      # debug
    #     print("Motor " + str(motor) + " write sucessful")
    return


def read1(motor, address):
    """ generic function to read 1 Byte from motor register """
    read = dynamixel.read1ByteTxRx(port_num, PROTOCOL_VERSION, motor, address)
    dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)
    dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)
    if dxl_comm_result != COMM_SUCCESS:
        print(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result))
    elif dxl_error != 0:
        print(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error))
    # else:
    #     print("Motor " + str(motor) + " read sucessful")
    return read


def read2(motor, address):
    """ generic function to read 2 Byte from motor register """
    read = dynamixel.read2ByteTxRx(port_num, PROTOCOL_VERSION, motor, address)
    dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)
    dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)
    if dxl_comm_result != COMM_SUCCESS:
        print(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result))
    elif dxl_error != 0:
        print(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error))
    # else:
    #     print("Motor " + str(motor) + " read sucessfull")
    return read


def read4(motor, address):
    """ generic function to read 4 Byte from motor register """
    read = dynamixel.read4ByteTxRx(port_num, PROTOCOL_VERSION, motor, address)
    dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)
    dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)
    if dxl_comm_result != COMM_SUCCESS:
        print(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result))
    elif dxl_error != 0:
        print(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error))
    # else:
    #     print("Motor " + str(motor) + " read sucessful")
    return read


def close():
    """ close com port and menu """
    dynamixel.closePort(port_num)
    return


def connect(DEVICENAME, BAUDRATE):
    """ initiate communication with motors, check communication """

    port_num = dynamixel.portHandler(DEVICENAME.encode('utf-8'))                # open port
    print ("device = " + str(DEVICENAME) + "   port = " + str(port_num))

    dynamixel.packetHandler()
    if dynamixel.openPort(port_num):
        print("Succeeded to open the port (%s)!" % DEVICENAME)
    else:
        print("Failed to open the port (%s)!" % DEVICENAME)
        status_ok = False
        return status_ok

    if dynamixel.setBaudRate(port_num, BAUDRATE):                               # Set port baudrate
        print("Succeeded to set the baudrate!")
    else:
        print("Failed to change the baudrate!")
        status_ok = False
        return status_ok

    status_ok = test()                                                           # test register configuration

    return status_ok


def test():
    """ test register setting and restore to MilliBox settings """

    global num_motors
    global base_type
    global base_ratio
    global base_res
    global ram_offset
    global h_zero
    global base_pos_acc_thresh
    global base_vel_unit
    global max_H_velocity
    global h_P
    global h_I
    global h_D
    global h_FF1
    global base_moving_threshold
    global gim_type

    status_ok = True

    print("===== Gimbal type CHECK =====")
    if read2(Z, ADD_MODEL_NUMBER) >= GIM03_MOTOR_TYPE:                          # check if Z motor is found (GIM05)
        num_motors = 6
        gim_type = SPHERICAL
        print("====> GIM05_Z identified")
    elif read2(T, ADD_MODEL_NUMBER) >= GIM03_MOTOR_TYPE:                        # check if T motor is found (GIM05)
        num_motors = 5
        gim_type = SPHERICAL
        print("====> GIM05_T identified")
    elif read2(P, ADD_MODEL_NUMBER) >= GIM03_MOTOR_TYPE:                        # check if P motor is found (GIM04x)
        num_motors = 4
        gim_type = HV
        print("====> GIM04_P identified")
    elif read2(R, ADD_MODEL_NUMBER) >= GIM03_MOTOR_TYPE:                        # check if slave motor is found (GIM03)
        num_motors = 3
        gim_type = HV
        print("====> GIM03/04 identified")
    elif read2(V, ADD_MODEL_NUMBER) > 0:                                        # check if V motor is found (GIM01)
        num_motors = 2
        gim_type = HV
        print("====> GIM01 identified")
    elif read2(H, ADD_MODEL_NUMBER) > 0:                                        # check if H motor is found (GIM1D)
        num_motors = 1
        gim_type = HV
        print("====> GIM1D identified")
    else:
        print("Failed MOTOR READBACK!!")                                        # no motors found, report error and quit
        status_ok = False
        return status_ok

    if read2(H, ADD_MODEL_NUMBER) == GIM04_MOTOR_TYPE:
        base_type = 4
        base_ratio = G4_H_RATIO
        base_res = P_RES
        ram_offset = GIM04_RAM_ADD_OFFSET
        h_zero = 0
        base_pos_acc_thresh = POS_ACC_THRESH_H_G4
        base_vel_unit = P_VELOCITY_UNIT
        max_H_velocity = HP_PROFILE_VELOCITY
        h_P = HP_POSITION_P_G
        h_I = HP_POSITION_I_G
        h_D = HP_POSITION_D_G
        h_FF1 = HP_FF1_G
        base_moving_threshold = HP_MOVING_THRESHOLD
        print("====> GIM04 Base identified")
    else:
        base_type = 1
        base_ratio = H_RATIO
        base_res = X_RES
        ram_offset = 0
        h_zero = H0
        base_pos_acc_thresh = POS_ACC_THRESH_H_G1
        base_vel_unit = X_VELOCITY_UNIT
        max_H_velocity = H_PROFILE_VELOCITY
        h_P = H_POSITION_P_G
        h_I = H_POSITION_I_G
        h_D = H_POSITION_D_G
        h_FF1 = H_FF1_G
        base_moving_threshold = H_MOVING_THRESHOLD
        print("====> GIM01 GIM03 Base identified")

    print("===== motor configuration CHECK =====")
    disable_torque(H)
    if gim_type == SPHERICAL:                                                   # access flash
        if num_motors >= 5:
            disable_torque(T)
            if num_motors >= 6:
                disable_torque(Z)
    elif gim_type == HV:
        if num_motors >= 2:
            disable_torque(V)
        if num_motors >= 3:
            disable_torque(R)
        if num_motors >= 4:
            disable_torque(P)
    print("flash access set ")

    # print("======  re-instate Offsets debug only==========")
    # Hoffset = read4(H, ADD_HOME_OFFSET)
    # Voffset = read4(V, ADD_HOME_OFFSET)
    # write4(H, ADD_HOME_OFFSET, Hoffset)
    # write4(V, ADD_HOME_OFFSET, Voffset)
    # print ("H Offset is:  " +str(Hoffset)+"   V Offset is:  " +str(Voffset))

    if read4(H, ADD_MOVE_THRESHOLD) == base_moving_threshold:                   # test H moving Threshold
        print("H moving threshold OK")
    else:
        print("resetting H moving threshold")

        write4(H, ADD_MOVE_THRESHOLD, base_moving_threshold)
        print("H moving threshold set to : " + str(base_moving_threshold))
    if gim_type == HV:
        if num_motors >= 2:
            if read4(V, ADD_MOVE_THRESHOLD) == V_MOVING_THRESHOLD:              # test V moving Threshold
                print("V moving threshold OK")
            else:
                print("resetting V moving threshold")
                write4(V, ADD_MOVE_THRESHOLD, V_MOVING_THRESHOLD)
                print("V moving threshold set to : " + str(V_MOVING_THRESHOLD))
            if num_motors >= 4:
                if read4(P, ADD_MOVE_THRESHOLD) == P_MOVING_THRESHOLD:          # test P moving Threshold
                    print("P moving threshold OK")
                else:
                    print("resetting P moving threshold")
                    write4(P, ADD_MOVE_THRESHOLD, P_MOVING_THRESHOLD)
                    print("P moving threshold set to : " + str(P_MOVING_THRESHOLD))
    elif gim_type == SPHERICAL:
        if num_motors >= 5:
            if read4(T, ADD_MOVE_THRESHOLD) == T_MOVING_THRESHOLD:              # test T moving Threshold
                print("T moving threshold OK")
            else:
                print("resetting T moving threshold")
                write4(T, ADD_MOVE_THRESHOLD, T_MOVING_THRESHOLD)
                print("T moving threshold set to : " + str(T_MOVING_THRESHOLD))
            if num_motors >= 6:
                if read4(Z, ADD_MOVE_THRESHOLD) == Z_MOVING_THRESHOLD:          # test Z moving Threshold
                    print("Z moving threshold OK")
                else:
                    print("resetting Z moving threshold")
                    write4(Z, ADD_MOVE_THRESHOLD, Z_MOVING_THRESHOLD)
                    print("Z moving threshold set to : " + str(Z_MOVING_THRESHOLD))

    if gim_type == HV:                                                          # test max velocity settings
        maxvelH = read4(H, ADD_MAX_VELOCITY)
        if num_motors >= 2:
            maxvelV = read4(V, ADD_MAX_VELOCITY)
            if num_motors >= 4:
                maxvelP = read4(P, ADD_MAX_VELOCITY)
            else:
                maxvelP = MAX_VELOCITY
        else:
            maxvelV = MAX_VELOCITY

        # print("max velocity H = " +str(maxvelH)+ " and V = " +str(maxvelV)+ "  and P = " +str(maxvelP))

        if maxvelH == max_H_velocity:
            print("****  Max H velocity is OK : " + str(maxvelH) + "  ****")
        else:
            print(" resetting H max velocity to :  " + str(max_H_velocity))
            write4(H, ADD_MAX_VELOCITY, max_H_velocity)
        if num_motors >= 2:
            if maxvelV == MAX_VELOCITY:
                print("****  Max V velocity is OK : " + str(maxvelV) + "  ****")
            else:
                print( " resetting V max velocity to :  " + str(MAX_VELOCITY))
                write4(V, ADD_MAX_VELOCITY, MAX_VELOCITY)
            if num_motors >= 4:
                if maxvelP == MAX_VELOCITY:
                    print("****  Max P velocity is OK : " + str(maxvelP) + "  ****")
                else:
                    print( " resetting P max velocity to :  " + str(MAX_VELOCITY))
                    write4(P, ADD_MAX_VELOCITY, MAX_VELOCITY)

    if gim_type == SPHERICAL:                                                   # test max velocity settings
        maxvelH = read4(H, ADD_MAX_VELOCITY)
        if num_motors >= 5:
            maxvelT = read4(T, ADD_MAX_VELOCITY)
            if num_motors >= 6:
                maxvelZ = read4(Z, ADD_MAX_VELOCITY)
            else:
                maxvelZ = MAX_VELOCITY
        else:
            maxvelT = MAX_VELOCITY

        # print("max velocity H = " +str(maxvelH)+ " and T = " +str(maxvelT)+ "  and Z = " +str(maxvelZ))

        if maxvelH == max_H_velocity:
            print("****  Max H velocity is OK : " + str(maxvelH) + "  ****")
        else:
            print(" resetting H max velocity to :  " + str(max_H_velocity))
            write4(H, ADD_MAX_VELOCITY, max_H_velocity)
        if num_motors >= 5:
            if maxvelT == MAX_VELOCITY:
                print("****  Max T velocity is OK : " + str(maxvelT) + "  ****")
            else:
                print( " resetting T max velocity to :  " + str(MAX_VELOCITY))
                write4(T, ADD_MAX_VELOCITY, MAX_VELOCITY)
            if num_motors >= 6:
                if maxvelZ == MAX_VELOCITY:
                    print("****  Max Z velocity is OK : " + str(maxvelZ) + "  ****")
                else:
                    print( " resetting Z max velocity to :  " + str(MAX_VELOCITY))
                    write4(Z, ADD_MAX_VELOCITY, MAX_VELOCITY)

    if gim_type == HV:
        opmodeH = read1(H, ADD_OPERATING_MODE)                                  # test operating mode
        if num_motors >= 2:
            opmodeV = read1(V, ADD_OPERATING_MODE)
        else:
            opmodeV = OPER_MODE

        print("operating mode H = " + str(opmodeH) + " and V = " + str(opmodeV))
        if opmodeH == OPER_MODE and opmodeV == OPER_MODE:
            print("**** Operating mode is OK ****")
        else:
            print(" resetting operating mode ")
            write1(H, ADD_OPERATING_MODE, OPER_MODE)
            if num_motors >= 2:
                write1(V, ADD_OPERATING_MODE, OPER_MODE)
            print("operating mode reset to : " + str(OPER_MODE))

        if num_motors >= 4:
            if read1(P, ADD_OPERATING_MODE) == OPER_MODE:
                print("**** Operating mode is OK ****")
            else:
                print(" resetting operating mode ")
                write1(P, ADD_OPERATING_MODE, OPER_MODE)

        if num_motors >= 3:                                                     # This part is to make sure that if Motors are upgraded
            opmodeR = read1(R, ADD_OPERATING_MODE)                              # GIM03 reverse slave motors (ID:3) does not lose its slave mode
            print("operating mode R = " + str(opmodeR))                         # otherwsie it could damage the gimbal
            if opmodeR == OPER_MODE:
                print("gim03 reverse motor operating mode is OK")
            else:
                write1(R, ADD_OPERATING_MODE, OPER_MODE)
                print(" reseting reverse motor operating mode")
            drmodeR = read1(R, ADD_DRIVE_MODE)
            print("drive mode R = " + str(drmodeR))
            if drmodeR == DRIVE_MODE:
                print("gim03 reverse motor drive mode is OK")
            else:
                write1(R, ADD_DRIVE_MODE, DRIVE_MODE)
                print(" resetting reverse motor drive mode")

    if gim_type == SPHERICAL:
        opmodeH = read1(H, ADD_OPERATING_MODE)                                  # test operating mode
        if num_motors >= 5:
            opmodeT = read1(T, ADD_OPERATING_MODE)
        else:
            opmodeT = OPER_MODE

        print("operating mode H = " + str(opmodeH) + " and T = " + str(opmodeT))
        if opmodeH == OPER_MODE and opmodeT == OPER_MODE:
            print("**** Operating mode is OK ****")
        else:
            print(" resetting operating mode ")
            write1(H, ADD_OPERATING_MODE, OPER_MODE)
            if num_motors >= 5:
                write1(T, ADD_OPERATING_MODE, OPER_MODE)
            print("operating mode reset to : " + str(OPER_MODE))

        if num_motors >= 6:                                                     # This part is to make sure that if Motors are upgraded
            opmodeZ = read1(Z, ADD_OPERATING_MODE)                              # GIM05 stays in reverse mode (to match polarity of T)
            print("operating mode Z = " + str(opmodeZ))
            if opmodeZ == OPER_MODE:
                print("gim05 reverse motor operating mode is OK")
            else:
                write1(Z, ADD_OPERATING_MODE, OPER_MODE)
                print(" reseting reverse motor operating mode")
            drmodeZ = read1(Z, ADD_DRIVE_MODE)
            print("drive mode Z = " + str(drmodeZ))
            if drmodeZ == DRIVE_MODE_Z:
                print("gim05 reverse motor drive mode is OK")
            else:
                write1(Z, ADD_DRIVE_MODE, DRIVE_MODE_Z)
                print(" resetting reverse motor drive mode")

    print("=== setting motors dynamic parameters ===")                          # those setting should be done at every power on
    enable_torque(H)
    if gim_type == HV:
        if num_motors >= 2:
            enable_torque(V)
        if num_motors >= 3:
            enable_torque(R)
        if num_motors >= 4:
            enable_torque(P)
    elif gim_type == SPHERICAL:
        if num_motors >= 5:
            enable_torque(T)
        if num_motors >= 6:
            enable_torque(Z)

    print("ram access enabled")                                                 # close access to flash and enable acces to RAM area

    print("BOOT UP MOTOR POSITION CHECK before re-alignement")                  # print motor absolute position at boot up
    getposition(0)

    write4(H, (ADD_GOAL_VELOC + ram_offset), max_H_velocity)                    # set H PID values
    # write4(H, (ADD_VELOC_PROFILE + ram_offset), H_PROFILE_VELOCITY)
    # print("H goal velocity set to :" +str(GOAL_VELOCITY))
    write2(H, (ADD_POS_D_GAIN + ram_offset), h_D)
    write2(H, (ADD_POS_P_GAIN + ram_offset), h_P)
    write2(H, (ADD_POS_I_GAIN + ram_offset), h_I)
    write2(H, (ADD_FF_1ST_GAIN+ ram_offset), h_FF1)
    print("H PID configuration set")

    if gim_type == HV:
        if num_motors >= 2:
            write4(V, ADD_GOAL_VELOC, V_GOAL_VELOCITY)                                # set V PID values
            # write4(V, ADD_VELOC_PROFILE, V_PROFILE_VELOCITY)
            # print("V goal velocity set to :" +str(V_GOAL_VELOCITY))
            write2(V, ADD_POS_D_GAIN, V_POSITION_D_G)
            write2(V, ADD_POS_P_GAIN, V_POSITION_P_G)
            write2(V, ADD_POS_I_GAIN, V_POSITION_I_G)
            write2(V, ADD_FF_1ST_GAIN, V_FF1_G)
            print("V PID configuration set")

        if num_motors >= 4:
            write4(P, ADD_GOAL_VELOC, P_GOAL_VELOCITY)                                # set P PID values
            # write4(P, ADD_VELOC_PROFILE, P_PROFILE_VELOCITY)
            # print("P goal velocity set to :" +str(P_GOAL_VELOCITY))
            write2(P, ADD_POS_D_GAIN, P_POSITION_D_G)
            write2(P, ADD_POS_P_GAIN, P_POSITION_P_G)
            write2(P, ADD_POS_I_GAIN, P_POSITION_I_G)
            write2(P, ADD_FF_1ST_GAIN, P_FF1_G)
            print("P PID configuration set")

    if gim_type == SPHERICAL:
        if num_motors >= 5:
            write4(T, ADD_GOAL_VELOC, P_GOAL_VELOCITY)                                # set T PID values
            # write4(T, ADD_VELOC_PROFILE, P_PROFILE_VELOCITY)                          # fixme: do we need specific PID for GIM05
            # print("T goal velocity set to :" +str(P_GOAL_VELOCITY))
            write2(T, ADD_POS_D_GAIN, P_POSITION_D_G)
            write2(T, ADD_POS_P_GAIN, P_POSITION_P_G)
            write2(T, ADD_POS_I_GAIN, P_POSITION_I_G)
            write2(T, ADD_FF_1ST_GAIN, P_FF1_G)
            print("T PID configuration set")

        if num_motors >= 6:
            write4(Z, ADD_GOAL_VELOC, P_GOAL_VELOCITY)                                # set Z PID values
            # write4(P, ADD_VELOC_PROFILE, P_PROFILE_VELOCITY)
            # print("P goal velocity set to :" +str(P_GOAL_VELOCITY))
            write2(Z, ADD_POS_D_GAIN, P_POSITION_D_G)
            write2(Z, ADD_POS_P_GAIN, P_POSITION_P_G)
            write2(Z, ADD_POS_I_GAIN, P_POSITION_I_G)
            write2(Z, ADD_FF_1ST_GAIN, P_FF1_G)
            print("Z PID configuration set")

    print("verifying all settings")                                             # check all actual values in RAM

    print("H goal Velocity : " + str(read4(H, ADD_GOAL_VELOC + ram_offset)) + " = " + str(max_H_velocity))
    print("H position D gain : " + str(read2(H, ADD_POS_D_GAIN + ram_offset)) + " = " + str(h_D))
    print("H position P gain : " + str(read2(H, ADD_POS_P_GAIN + ram_offset)) + " = " + str(h_P))
    print("H position I gain : " + str(read2(H, ADD_POS_I_GAIN + ram_offset)) + " = " + str(h_I))
    print("H FF1 gain : " + str(read2(H, ADD_FF_1ST_GAIN + ram_offset)) + " = " + str(h_FF1))

    if gim_type == HV:
        if num_motors >= 2:
            print("V goal Velocity : " + str(read4(V, ADD_GOAL_VELOC)) + " = " + str(V_GOAL_VELOCITY))
            print("V position D gain : " + str(read2(V, ADD_POS_D_GAIN)) + " = " + str(V_POSITION_D_G))
            print("V position P gain : " + str(read2(V, ADD_POS_P_GAIN)) + " = " + str(V_POSITION_P_G))
            print("V position I gain : " + str(read2(V, ADD_POS_I_GAIN)) + " = " + str(V_POSITION_I_G))
            print("V FF1 gain : " + str(read2(V, ADD_FF_1ST_GAIN)) + " = " + str(V_FF1_G))

        if num_motors >= 4:                                                         # fixme: set P actual PID values
            print("P goal Velocity : " + str(read4(P, ADD_GOAL_VELOC)) + " = " + str(P_GOAL_VELOCITY))
            print("P position D gain : " + str(read2(P, ADD_POS_D_GAIN)) + " = " + str(P_POSITION_D_G))
            print("P position P gain : " + str(read2(P, ADD_POS_P_GAIN)) + " = " + str(P_POSITION_P_G))
            print("P position I gain : " + str(read2(P, ADD_POS_I_GAIN)) + " = " + str(P_POSITION_I_G))
            print("P FF1 gain : " + str(read2(P, ADD_FF_1ST_GAIN)) + " = " + str(P_FF1_G))

        if gim_type == SPHERICAL:
            if num_motors >= 5:
                print("T goal Velocity : " + str(read4(T, ADD_GOAL_VELOC)) + " = " + str(P_GOAL_VELOCITY))
                print("T position D gain : " + str(read2(T, ADD_POS_D_GAIN)) + " = " + str(P_POSITION_D_G))
                print("T position P gain : " + str(read2(T, ADD_POS_P_GAIN)) + " = " + str(P_POSITION_P_G))
                print("T position I gain : " + str(read2(T, ADD_POS_I_GAIN)) + " = " + str(P_POSITION_I_G))
                print("T FF1 gain : " + str(read2(T, ADD_FF_1ST_GAIN)) + " = " + str(P_FF1_G))

            if num_motors >= 6:                                                         # fixme: set P actual PID values
                print("Z goal Velocity : " + str(read4(Z, ADD_GOAL_VELOC)) + " = " + str(P_GOAL_VELOCITY))
                print("Z position D gain : " + str(read2(Z, ADD_POS_D_GAIN)) + " = " + str(P_POSITION_D_G))
                print("Z position P gain : " + str(read2(Z, ADD_POS_P_GAIN)) + " = " + str(P_POSITION_P_G))
                print("Z position I gain : " + str(read2(Z, ADD_POS_I_GAIN)) + " = " + str(P_POSITION_I_G))
                print("Z FF1 gain : " + str(read2(Z, ADD_FF_1ST_GAIN)) + " = " + str(P_FF1_G))

    # reset offset and pos at startup

    versionH = read1(H, ADD_FW_VER)
    if base_type == 4:
        if versionH < MIN_VERSION_P:                                            # make sure Firmware is up to date
            print("firmware version not supported:" + str(versionH))
        else:
            print("firmware version of motor H is OKAY ")

    if base_type == 1:
        if versionH < MIN_VERSION:                                              # make sure Firmware is up to date
            print("firmware version not supported:" + str(versionH))
        else:
            print("firmware version of motor H is OKAY ")
            if versionH > 42:                                                   # offset handling after FW 42 has changed
                realign(H)

    if gim_type == HV:
        if num_motors >= 2:
            versionV = read1(V, ADD_FW_VER)
            if versionV < MIN_VERSION:                                          # make sure Firmware is up to date
                print("firmware version not supported")
            else:
                print("firmware version of motor V is OKAY ")
                if versionV > 42:                                               # offset handling after FW 42 has changed
                    realign(V)                                                  # we may need to re-align current position
            if num_motors >= 4:
                versionP = read1(P, ADD_FW_VER)
                if versionP < MIN_VERSION:                                      # make sure Firmware is up to date
                    print("firmware version not supported")
                else:
                    print("firmware version of motor P is OKAY ")
                    if versionP > 42:                                           # offset handling after FW 42 has changed
                        realign(P)                                              # we may need to re-align current position

        if num_motors >= 3:                                                     # setting an acceleration limiter on GIM03 and GIM04 Vertical motor for smoother motion
            acc_profile = read4 (V, ADD_ACCEL_PROFILE)
            if acc_profile == V_ACCELERATION_LIMIT:
                print(" Vertical acceleration profile check pass")
            else:
                write4(V, ADD_ACCEL_PROFILE, V_ACCELERATION_LIMIT)
                print(" Vertical acceleration profile set to : " + str(V_ACCELERATION_LIMIT))

    if gim_type == SPHERICAL:
        if num_motors >= 5:
            versionT = read1(T, ADD_FW_VER)
            if versionT < MIN_VERSION:                                          # make sure Firmware is up to date
                print("firmware version not supported")
            else:
                print("firmware version of motor T is OKAY ")
                if versionT > 42:                                               # offset handling after FW 42 has changed
                    realign(T)                                                  # we may need to re-align current position
            if num_motors >= 6:
                versionZ = read1(Z, ADD_FW_VER)
                if versionZ < MIN_VERSION:                                      # make sure Firmware is up to date
                    print("firmware version not supported")
                else:
                    print("firmware version of motor Z is OKAY ")
                    if versionZ > 42:                                           # offset handling after FW 42 has changed
                        realign(Z)                                              # we may need to re-align current position

    if base_type == 4:                                                          # setting an acceleration limiter on GIM04 Base for smoother motion
        H_acc_profile = read4 (H, ADD_ACCEL_PROFILE + ram_offset)
        if H_acc_profile == HP_ACCELERATION_LIMIT:
            print(" GIM04 base acceleration profile check pass")
        else:
            write4(H, ADD_ACCEL_PROFILE + ram_offset, HP_ACCELERATION_LIMIT)
            print(" GIM04 base acceleration profile set to : " + str(HP_ACCELERATION_LIMIT))

    gotoZERO("HIGH")
    return status_ok


def get_gimtype():
    """ return the gimbal type (HV or SPHERICAL) """
    global gim_type
    return gim_type


def get_nummotors():
    """ return the number of detected motors """
    global num_motors
    return num_motors


def realign(motor):
    """ re-aligns the motor at boot-up, if needed """
    if motor == H and base_type == 4:
        resolution = P_RES
        max_off = MAX_OFFSET_P
        ram = ram_offset
    else:
        resolution = X_RES
        max_off = MAX_OFFSET
        ram = 0

    print("checking motor : " +str(motor)+ " position at init")                 # debug
    homeoffset = read4(motor, ADD_HOME_OFFSET)                                  # read current offset from flash
    print("motor : "+str(motor)+" offset at init is: " +str(homeoffset))        # debug
    goalpos = read4(motor, ADD_GOAL_POSITION + ram)                             # read current motor position
    print("motor : "+str(motor)+" pos at init is: "  +str(goalpos))             # debug
    drmode = read1(motor, ADD_DRIVE_MODE)                                       # read current drive mode (direction)
    print("motor : "+str(motor)+" drive mode at init is: "  +str(drmode))       # debug

    # normal mode:  pos_actual = goalpos - homeoffset
    # reverse mode: pos_actual = goalpos + homeoffset
    pos_valid = goalpos % resolution                                            # ensure 0 <= pos_valid < resolution
    pos_delta = pos_valid - goalpos                                             # determine change needed to goalpos to make valid
    if (drmode & 1) == 1:                                                       # check bit0 of drive mode
        homeoffset_delta = -1 * pos_delta                                       # reverse drive
    else:
        homeoffset_delta = pos_delta                                            # normal drive

    new_homeoffset = int(homeoffset + homeoffset_delta)                         # compute change needed to offset

    if new_homeoffset > max_off or new_homeoffset < -1*max_off:                 # let's check that our offset is not maxed out
        print ("WARNING ------ offset overun need to reset offset using menu-------")
    elif homeoffset_delta == 0:                                                 # no change is needed
        print("-> no compensation needed for motor : " +str(motor))
    else:                                                                       # offset is not maxed out and we need to make a change
        disable_torque(motor)                                                   # disable torque opens the motor flash memory for update
        write4(motor, ADD_HOME_OFFSET, new_homeoffset)                          # change offset accordingly
        enable_torque(motor)                                                    # close the flash write access
        print(" motor : " + str(motor) + " offset adjusted to : " + str(new_homeoffset))    # debug
        offset = read4(motor, ADD_HOME_OFFSET)                                  # read back to make sure the change happened
        print(" readback motor : " + str(motor) + " offset is: " + str(offset)) # record the change in log
        pos = read4(motor, ADD_GOAL_POSITION + ram)                             # read back the the current position is within valid range
        if 0 <= pos < resolution:
            print(" updated motor : " + str(motor) + " pos is: " + str(pos))
        else:
            print(" ERROR : the motor position is wrong ")

    return


def setoffset(motor):
    """ write the current position to motor eeprom """
    if motor is H:
        offset = read4(H, ADD_HOME_OFFSET)
        print("current offset= " + str(offset))
        offset = offset - current_pos(H, 1) + h_zero                            # we want Horizontal center at 2048 or 0 (depending on motor type)
        if abs(offset) <= MAX_OFFSET:
            disable_torque(H)
            write4(H, ADD_HOME_OFFSET, offset)
            print("new offset= " + str(offset))
            offset = read4(H, ADD_HOME_OFFSET)
            print("check new offset= " + str(offset))
        else:
            print("offset out of range, reset the offset")
        enable_torque(H)                                                        # allow motors to move
    else:
        offset = read4(motor, ADD_HOME_OFFSET)
        print("current offset= " + str(offset))
        drmode = read1(motor, ADD_DRIVE_MODE)                                   # read drive mode (direction)

        # normal mode:  pos_actual = goalpos - homeoffset
        # reverse mode: pos_actual = goalpos + homeoffset
        if (drmode & 1) == 1:
            offset = offset - (V0 - current_pos(motor, 1))                      # reverse drive
        else:
            offset = offset - (current_pos(motor, 1) - V0)                      # normal drive

        if abs(offset) <= MAX_OFFSET:
            disable_torque(motor)
            write4(motor, ADD_HOME_OFFSET, offset)
            print("new offset= " + str(offset))
            offset = read4(motor, ADD_HOME_OFFSET)
            print("check new offset= " + str(offset))
        else:
            print("offset out of range, reset the offset")
        enable_torque(motor)
    return


def setoffset_all():
    """ write the current position for all motors to motor eeprom """
    if gim_type == HV:
        setoffset(H)
        if num_motors >= 2:
            setoffset(V)
            if num_motors >= 4:
                setoffset(P)
    elif gim_type == SPHERICAL:
        setoffset(H)
        if num_motors >= 5:
            setoffset(T)
            if num_motors >= 6:
                setoffset(Z)
    return


def resetoffset():
    """ reset the offset position in case it reach the maximum number of turns 255 """
    disable_torque(H)
    offseth = read4(H, ADD_HOME_OFFSET)
    print("current H offset= " + str(offseth))
    write4(H, ADD_HOME_OFFSET, 0)
    enable_torque(H)
    print("*** offset reset done on H")
    if gim_type == HV:
        if num_motors >= 2:
            disable_torque(V)
            offsetv = read4(V, ADD_HOME_OFFSET)
            print("current V offset= " + str(offsetv))
            write4(V, ADD_HOME_OFFSET, 0)
            enable_torque(V)
            print("*** offset reset done on V")
            if num_motors >= 4:
                disable_torque(P)
                offsetp = read4(P, ADD_HOME_OFFSET)
                print("current P offset= " + str(offsetp))
                write4(P, ADD_HOME_OFFSET, 0)
                enable_torque(P)
                print("*** offset reset done on P")
    if gim_type == SPHERICAL:
        if num_motors >= 5:
            disable_torque(T)
            offsetv = read4(T, ADD_HOME_OFFSET)
            print("current T offset= " + str(offsetv))
            write4(T, ADD_HOME_OFFSET, 0)
            enable_torque(T)
            print("*** offset reset done on T")
            if num_motors >= 6:
                disable_torque(Z)
                offsetp = read4(Z, ADD_HOME_OFFSET)
                print("current Z offset= " + str(offsetp))
                write4(Z, ADD_HOME_OFFSET, 0)
                enable_torque(Z)
                print("*** offset reset done on Z")
    return


def changerate(rate):
    """ change all motors communication baud rate, this is used for MACos which does not support 1Mbps """
    disable_torque(H)
    write1(H, ADD_BAUD_RATE, rate)
    enable_torque(H)
    if gim_type == HV:
        if num_motors >= 2:
            disable_torque(V)
            write1(V, ADD_BAUD_RATE, rate)
            enable_torque(V)
            if num_motors >= 3:
                disable_torque(R)
                write1(R, ADD_BAUD_RATE, rate)
                enable_torque(R)
                if num_motors >= 4:
                    disable_torque(P)
                    write1(P, ADD_BAUD_RATE, rate)
                    enable_torque(P)
    elif gim_type == SPHERICAL:
        if num_motors >= 5:
            disable_torque(T)
            write1(T, ADD_BAUD_RATE, rate)
            enable_torque(T)
            if num_motors >= 6:
                disable_torque(Z)
                write1(Z, ADD_BAUD_RATE, rate)
                enable_torque(Z)

    print("*** rate changed, port is closed, set BAUDRATE global in mbx.py accordingly")
    print("*** restart mbx.py with correct baud rate")
    sys.exit()
    return


def enable_torque(motor):
    """ allow motor to move and block eeprom register access """
    if motor <= num_motors:
        if motor == H:
            if read1(motor, (ADD_TORQUE_ENABLE + ram_offset)) == TORQUE_ENABLE:
                print("torque for motor : " + str(motor) + " is already enabled")
            else:
                write1(motor, (ADD_TORQUE_ENABLE + ram_offset), TORQUE_ENABLE)
                print("torque now enabled for motor" + str(motor))
        elif motor > H:
            if read1(motor, ADD_TORQUE_ENABLE) == TORQUE_ENABLE:
                print("torque for motor : " + str(motor) + " is already enabled")
            else:
                write1(motor, ADD_TORQUE_ENABLE, TORQUE_ENABLE)
                print("torque now enabled for motor" + str(motor))
    else:
        print("WARNING: Attempting to enable torque on Motor %d that does not exist" % motor)
    return


def disable_torque(motor):
    """ stop motor from being moved and allow eeprom register access """
    if motor <= num_motors:
        if motor == H:
            if read1(motor, (ADD_TORQUE_ENABLE + ram_offset)) == TORQUE_DISABLE:
                print("torque for motor : " + str(motor) + " is already disabled")
            else:
                write1(motor, (ADD_TORQUE_ENABLE + ram_offset), TORQUE_DISABLE)
                print("torque now disabled for motor" + str(motor))
        elif motor > H:
            if read1(motor, ADD_TORQUE_ENABLE) == TORQUE_DISABLE:
                print("torque for motor : " + str(motor) + " is already disabled")
            else:
                write1(motor, ADD_TORQUE_ENABLE, TORQUE_DISABLE)
                print("torque now disabled for motor" + str(motor))
    else:
        print("WARNING: Attempting to disable torque on Motor %d that does not exist" % motor)
    return


def get_velocity():
    """ print motor RPM value """
    global base_ratio
    global ram_offset
    global base_vel_unit
    global V_GOAL_VELOCITY
    global P_GOAL_VELOCITY
    global X_VELOCITY_UNIT

    # print("base_type = %g" % base_type)
    # print("base_ratio = %g" % base_ratio)
    # print("ram_offset = %g" % ram_offset)
    # print("base_vel_unit = %g" % base_vel_unit)

    if gim_type == HV:
        H_velocity = base_vel_unit * read4(H, (ADD_VELOC_PROFILE + ram_offset)) / base_ratio    # read the current motor H velocity setting and convert to rpm
        print("H velocity is set to = " + str(H_velocity) + " rpm")
        if num_motors >= 2:
            V_velocity = X_VELOCITY_UNIT * read4(V, ADD_VELOC_PROFILE)/V_RATIO                  # read the current motor V velocity setting and convert to rpm
            print("V velocity is set to = " + str(V_velocity) + " rpm")
        else:
            V_velocity = V_GOAL_VELOCITY

        if num_motors >= 4:
            P_velocity = X_VELOCITY_UNIT * read4(P, ADD_VELOC_PROFILE)/P_RATIO                  # read the current motor P velocity setting and convert to rpm
            print("P velocity is set to = " + str(P_velocity) + " rpm")
        else:
            P_velocity = P_GOAL_VELOCITY
        vel1 = H_velocity
        vel2 = V_velocity
        vel3 = P_velocity

    if gim_type == SPHERICAL:
        H_velocity = base_vel_unit * read4(H, (ADD_VELOC_PROFILE + ram_offset)) / base_ratio    # read the current motor H velocity setting and convert to rpm
        print("H velocity is set to = " + str(H_velocity) + " rpm")
        if num_motors >= 5:
            T_velocity = X_VELOCITY_UNIT * read4(T, ADD_VELOC_PROFILE)/T_RATIO                  # read the current motor T velocity setting and convert to rpm
            print("T velocity is set to = " + str(T_velocity) + " rpm")
        else:
            T_velocity = T_GOAL_VELOCITY

        if num_motors >= 6:
            Z_velocity = X_VELOCITY_UNIT * read4(Z, ADD_VELOC_PROFILE)/Z_RATIO                  # read the current motor Z velocity setting and convert to rpm
            print("Z velocity is set to = " + str(Z_velocity) + " rpm")
        else:
            Z_velocity = Z_GOAL_VELOCITY
        vel1 = H_velocity
        vel2 = T_velocity
        vel3 = Z_velocity

    return vel1, vel2, vel3


def set_velocity(vel1=0, vel2=0, vel3=0):
    """ change rotation speed of the motors """
    global base_ratio
    global ram_offset
    global base_vel_unit
    global max_H_velocity
    global V_GOAL_VELOCITY
    global P_GOAL_VELOCITY
    global X_VELOCITY_UNIT

    # print("base_ratio = %g" % base_ratio)
    # print("ram_offset = %g" % ram_offset)
    # print("base_vel_unit = %g" % base_vel_unit)
    # print("max_H_velocity = %g" % max_H_velocity)

    if gim_type == HV:                                                          # set velocities for HV gimbal
        h_vel = vel1
        v_vel = vel2
        p_vel = vel3

        if h_vel == 0:                                                          # if user set 0 then default max speed is used
            H_vel = max_H_velocity
        else:
            H_vel = int(round(h_vel * base_ratio / base_vel_unit))              # convert horizontal velocity to actual register value
            if H_vel > max_H_velocity:                                          # can't exceed max speed
                H_vel = max_H_velocity
                print("clamping to maximum possible velocity for H motor")
            if H_vel < 1:                                                       # can't be less than min speed
                H_vel = 1
                print("clamping to minimum possible velocity for H motor")
        write4(H, ADD_VELOC_PROFILE + ram_offset, H_vel)                        # program register value in RAM

        if num_motors >= 2:
            if v_vel == 0:                                                      # if user set 0 then default max speed is used
                V_vel = V_GOAL_VELOCITY
            else:
                V_vel = int(round(v_vel*V_RATIO/X_VELOCITY_UNIT))               # convert vertical velocity to actual register value
                if V_vel > V_GOAL_VELOCITY:                                     # can't exceed max speed
                    V_vel = V_GOAL_VELOCITY
                    print("clamping to maximum possible velocity for V motor")
                if V_vel < 1:                                                   # can't be less than min speed
                    V_vel = 1
                    print("clamping to minimum possible velocity for V motor")
            write4(V, ADD_VELOC_PROFILE, V_vel)                                 # program register value in RAM

        if num_motors >= 4:
            if p_vel == 0:                                                      # if user set 0 then default max speed is used
                P_vel = P_GOAL_VELOCITY
            else:
                P_vel = int(round(p_vel*P_RATIO/X_VELOCITY_UNIT))               # convert vertical velocity to actual register value
                if P_vel > P_GOAL_VELOCITY:                                     # can't exceed max speed
                    P_vel = P_GOAL_VELOCITY
                    print("clamping to maximum possible velocity for P motor")
                if P_vel < 1:                                                   # can't be less than min speed
                    P_vel = 1
                    print("clamping to minimum possible velocity for P motor")
            write4(P, ADD_VELOC_PROFILE, P_vel)

    if gim_type == SPHERICAL:                                                   # set velocities for SPHERICAL gimbal
        h_vel = vel1
        t_vel = vel2
        z_vel = vel3

        if h_vel == 0:                                                          # if user set 0 then default max speed is used
            H_vel = max_H_velocity
        else:
            H_vel = int(
                round(h_vel * base_ratio / base_vel_unit))                      # convert horizontal velocity to actual register value
            if H_vel > max_H_velocity:                                          # can't exceed max speed
                H_vel = max_H_velocity
                print("clamping to maximum possible velocity for H motor")
            if H_vel < 1:                                                       # can't be less than min speed
                H_vel = 1
                print("clamping to minimum possible velocity for H motor")
        write4(H, ADD_VELOC_PROFILE + ram_offset, H_vel)                        # program register value in RAM

        if num_motors >= 5:
            if t_vel == 0:                                                      # if user set 0 then default max speed is used
                T_vel = T_GOAL_VELOCITY
            else:
                T_vel = int(round(t_vel*T_RATIO/X_VELOCITY_UNIT))               # convert vertical velocity to actual register value
                if T_vel > T_GOAL_VELOCITY:                                     # can't exceed max speed
                    T_vel = T_GOAL_VELOCITY
                    print("clamping to maximum possible velocity for T motor")
                if T_vel < 1:                                                   # can't be less than min speed
                    T_vel = 1
                    print("clamping to minimum possible velocity for T motor")
            write4(T, ADD_VELOC_PROFILE, T_vel)                                 # program register value in RAM

        if num_motors >= 6:
            if z_vel == 0:                                                      # if user set 0 then default max speed is used
                Z_vel = Z_GOAL_VELOCITY
            else:
                Z_vel = int(round(z_vel*Z_RATIO/X_VELOCITY_UNIT))               # convert vertical velocity to actual register value
                if Z_vel > Z_GOAL_VELOCITY:                                     # can't exceed max speed
                    Z_vel = Z_GOAL_VELOCITY
                    print("clamping to maximum possible velocity for Z motor")
                if Z_vel < 1:                                                   # can't be less than min speed
                    Z_vel = 1
                    print("clamping to minimum possible velocity for Z motor")
            write4(Z, ADD_VELOC_PROFILE, Z_vel)

    get_velocity()                                                              # check the values by reading back the registers

    return


# ===========================================
# ============= GIMBAL MOVEMENT =============
# ===========================================

def convertangletopos(motor, angle):
    """ convert angle in degree to motor position """
    if motor is V:
        pos = int(round((angle*X_RES*V_RATIO)/360.0))+V0                        # Vertical motor is in direct drive
    elif motor is H:
        pos = int(round((angle*base_res*base_ratio)/360.0))+h_zero              # Horizontal motor has an additional 5x gear ratio in gimbal
    elif motor is P:
        pos = int(round(angle*X_RES*P_RATIO)/360.0)+P0                          # Pol motor has an additional 2.4x (120/50) gear ratio in gimbal
    elif motor is T:
        pos = int(round(angle*X_RES*T_RATIO)/360.0)+T0                          # Pol motor has an additional 2.4x (120/50) gear ratio in gimbal
    elif motor is Z:
        pos = int(round(angle*X_RES*Z_RATIO)/360.0)+Z0                          # Pol motor has an additional 2x gear ratio in gimbal
    elif motor is TH:
        pos = convertangletopos(H, angle)
    elif motor is PH:                                                           # angle = [PHI, DEL_PHI] when specifying PH angle
        pos = [convertangletopos(T, angle[0]), convertangletopos(Z, angle[0]-angle[1])]     # pos = [posT, posZ]
    else:
        print("position error")
    return pos


def convertpostoangle(motor, pos):
    """ convert reported motor position to absolute angle """
    if motor is V:
        angle = ((pos-V0)*360.0/(X_RES*V_RATIO))                                # Vertical motor is in direct drive
    elif motor is H:
        angle = ((pos-h_zero)*360.0/(base_res*base_ratio))                      # Horizontal motor has an additional 5x gear ratio in gimbal
    elif motor is P:
        angle = ((pos-P0)*360.0/(X_RES*P_RATIO))                                # Pol motor has an additional 2.4x (120/50) gear ratio in gimbal
    elif motor is T:
        angle = ((pos-T0)*360.0/(X_RES*T_RATIO))                                # T motor has an additional 2.4x (120/50) gear ratio in gimbal
    elif motor is Z:
        angle = ((pos-Z0)*360.0/(X_RES*Z_RATIO))                                # Z motor has an additional 2x gear ratio in gimbal
    elif motor is TH:
        angle = convertpostoangle(H, pos)
    elif motor is PH:
        Tangle = convertpostoangle(T, pos[0])                                   # pos = [posT, posZ]
        Zangle = convertpostoangle(Z, pos[1])
        angle = [Tangle, Tangle - Zangle]                                       # angle = [PHI, DEL_PHI] when specifying PH angle
    else:
        print("position error")
    return angle


def current_pos(motor, log):
    """ read the absolute current position of the motor """
    # this function can be called while the motor is moving
    # if a settled position is desired, use wait_stop_moving() before calling this function
    if motor % 100 <= num_motors:
        if motor == H:
            curpos = read4(motor, ADD_PRESENT_POS + ram_offset)
            offset = read4(motor, ADD_HOME_OFFSET)
        elif motor == TH:
            curpos = read4(H, ADD_PRESENT_POS + ram_offset)
            offset = read4(H, ADD_HOME_OFFSET)
        elif motor == PH:
            curposT = read4(T, ADD_PRESENT_POS)
            offsetT = read4(T, ADD_HOME_OFFSET)
            curposZ = read4(Z, ADD_PRESENT_POS)
            offsetZ = read4(Z, ADD_HOME_OFFSET)
            curpos = [curposT, curposZ]
            offset = [offsetT, offsetZ]
        else:
            curpos = read4(motor, ADD_PRESENT_POS)
            offset = read4(motor, ADD_HOME_OFFSET)
        if log == 0:
            cur_angle = convertpostoangle(motor, curpos)
            print("Current position for motor " + str(motor) + "  is =  " + str(cur_angle) + " degree, Position is : " + str(curpos) + " steps,  Offset is : " + str(offset))
    else:
        if motor == TH:
            curpos = convertangletopos(H, 0)
        elif motor == PH:
            curpos = [convertangletopos(T, 0), convertangletopos(Z, 0)]
        else:
            curpos = convertangletopos(motor, 0)
    return curpos


def goal_pos(motor, log):
    """ read the absolute goal position of the motor """
    if motor % 100 <= num_motors:
        if motor == H:
            cur_goal_pos = read4(motor, ADD_GOAL_POSITION + ram_offset)
            offset = read4(motor, ADD_HOME_OFFSET)
        elif motor == TH:
            cur_goal_pos = read4(H, ADD_GOAL_POSITION + ram_offset)
            offset = read4(H, ADD_HOME_OFFSET)
        elif motor == PH:
            cur_goal_posT = read4(T, ADD_GOAL_POSITION)
            offsetT = read4(T, ADD_HOME_OFFSET)
            cur_goal_posZ = read4(Z, ADD_GOAL_POSITION)
            offsetZ = read4(Z, ADD_HOME_OFFSET)

            cur_goal_pos = [cur_goal_posT, cur_goal_posZ]
            offset = [offsetT, offsetZ]
        else:
            cur_goal_pos = read4(motor, ADD_GOAL_POSITION)
            offset = read4(motor, ADD_HOME_OFFSET)
    else:
        if motor == TH:
            cur_goal_pos = convertangletopos(H, 0)
            offset = 0
        elif motor == PH:
            cur_goal_posT = convertangletopos(T, 0)
            cur_goal_posZ = convertangletopos(Z, 0)
            cur_goal_pos = [cur_goal_posT, cur_goal_posZ]
            offset = [0, 0]
        else:
            cur_goal_pos = convertangletopos(motor, 0)
            offset = 0

    goal_angle = convertpostoangle(motor, cur_goal_pos)
    if log == 0:
        print("Current goal position for motor " + str(motor) + "  is =  " + str(goal_angle) + " degree, Position is : " + str(cur_goal_pos) + "steps,  Offset is : " + str(offset))
    return cur_goal_pos


def getposition(log=0):
    """ get absolute position of all motors """
    if gim_type == HV:
        pos1 = current_pos(H, log)
        pos2 = current_pos(V, log)
        pos3 = current_pos(P, log)
    if gim_type == SPHERICAL:
        pos1 = current_pos(TH, log)
        pos2 = current_pos(PH, log)
        pos3 = None

    return pos1, pos2, pos3


def wait_stop_moving(accuracy="HIGH", debug=DEBUG_MOVING):
    """ wait until all motors are not moving """
    global ram_offset
    global base_pos_acc_thresh
    global POS_ACC_THRESH_V
    global POS_ACC_THRESH_P
    global POS_ACC_THRESH_T
    global POS_ACC_THRESH_Z

    INIT_DELAY = 0.15                                                           # delay before any register is read (to avoid ismoving reporting incorrectly)
    LOOP_DELAY = 0.05                                                           # delay in while loop polling status

    if debug:
        print("wait_stop_moving() called...")

    time.sleep(INIT_DELAY)

    if accuracy == "HIGH" or accuracy == "VERY HIGH":
        goalH = read4(H,ADD_GOAL_POSITION + ram_offset)                         # read H goal position
        if gim_type == HV:
            if num_motors >= 2:
                goalV = read4(V,ADD_GOAL_POSITION)                              # read V goal position
                if num_motors >= 4:
                    goalP = read4(P,ADD_GOAL_POSITION)                          # read P goal position
        if gim_type == SPHERICAL:
            if num_motors >= 5:
                goalT = read4(T,ADD_GOAL_POSITION)                              # read T goal position
                if num_motors >= 6:
                    goalZ = read4(Z,ADD_GOAL_POSITION)                          # read Z goal position

    # wait until motor H reports not MOVING (based on velocity)
    ismovingH = True
    while ismovingH:
        ismovingH = (read1(H, ADD_MOVING + ram_offset) > 0)                     # check H MOVING register
        if debug:
            print("H is moving = %d" % ismovingH)
        if ismovingH:
            time.sleep(LOOP_DELAY)                                              # delay before polling again

    # wait until motor H reaches goal position (based on target and current position)
    if accuracy == "HIGH" or accuracy == "VERY HIGH":
        not_reachedH = True
        while not_reachedH:                                                     # for higher accuracy, loop until (pres_pos - goal) <= threshold
            pres_posH = read4(H, ADD_PRESENT_POS + ram_offset)
            if debug:
                print("H goal position / present / error = %d / %d / %d" % (goalH, pres_posH, goalH - pres_posH))
            not_reachedH = (abs(pres_posH - goalH) > base_pos_acc_thresh)
            if not_reachedH:
                time.sleep(LOOP_DELAY)                                          # delay before polling again

    if gim_type == HV:
        if num_motors >= 2:                                                     # if we are not GIM1D
            # wait until motor V reports not MOVING (based on velocity)
            ismovingV = True
            while ismovingV:
                ismovingV = (read1(V, ADD_MOVING) > 0)                          # check V MOVING register
                if debug:
                    print("V is moving = %d" % ismovingV)
                if ismovingV:
                    time.sleep(LOOP_DELAY)                                      # delay before polling again

            # wait until motor V reaches goal position (based on target and current position)
            if accuracy == "HIGH" or accuracy == "VERY HIGH":
                not_reachedV = True
                while not_reachedV:                                             # for higher accuracy, loop until (pres_pos - goal) <= threshold
                    pres_posV = read4(V, ADD_PRESENT_POS)
                    if debug:
                        print("V goal position / present / error = %d / %d / %d" % (goalV, pres_posV, goalV - pres_posV))
                    not_reachedV = (abs(pres_posV - goalV) > POS_ACC_THRESH_V)
                    if not_reachedV:
                        time.sleep(LOOP_DELAY)                                  # delay before polling again

        if num_motors >= 4:                                                     # if we are a GIM04
            # wait until motor P reports not MOVING (based on velocity)
            ismovingP = 1
            while ismovingP:
                ismovingP = (read1(P, ADD_MOVING) > 0)                          # check P MOVING register
                if debug:
                    print("P is moving = %d" % ismovingP)
                if ismovingP:
                    time.sleep(LOOP_DELAY)                                      # delay before polling again

            # wait until motor P reaches goal position (based on target and current position)
            if accuracy == "HIGH" or accuracy == "VERY HIGH":
                not_reachedP = True
                while not_reachedP:                                             # for higher accuracy, loop until (pres_pos - goal) <= threshold
                    pres_posP = read4(P, ADD_PRESENT_POS)
                    if debug:
                        print("P goal position / present / error = %d / %d / %d" % (goalP, pres_posP, goalP - pres_posP))
                    not_reachedP = (abs(pres_posP - goalP) > POS_ACC_THRESH_P)
                    if not_reachedP:
                        time.sleep(LOOP_DELAY)                                  # delay before polling again

    if gim_type == SPHERICAL:
        if num_motors >= 5:                                                     # if we are not GIM1D
            # wait until motor T reports not MOVING (based on velocity)
            ismovingT = True
            while ismovingT:
                ismovingT = (read1(T, ADD_MOVING) > 0)                          # check T MOVING register
                if debug:
                    print("T is moving = %d" % ismovingT)
                if ismovingT:
                    time.sleep(LOOP_DELAY)                                      # delay before polling again

            # wait until motor T reaches goal position (based on target and current position)
            if accuracy == "HIGH" or accuracy == "VERY HIGH":
                not_reachedT = True
                while not_reachedT:                                             # for higher accuracy, loop until (pres_pos - goal) <= threshold
                    pres_posT = read4(T, ADD_PRESENT_POS)
                    if debug:
                        print("T goal position / present / error = %d / %d / %d" % (goalT, pres_posT, goalT - pres_posT))
                    not_reachedT = (abs(pres_posT - goalT) > POS_ACC_THRESH_T)
                    if not_reachedT:
                        time.sleep(LOOP_DELAY)                                  # delay before polling again

        if num_motors >= 6:                                                     # if we are a GIM05
            # wait until motor Z reports not MOVING (based on velocity)
            ismovingZ = 1
            while ismovingZ:
                ismovingZ = (read1(Z, ADD_MOVING) > 0)                          # check Z MOVING register
                if debug:
                    print("Z is moving = %d" % ismovingZ)
                if ismovingZ:
                    time.sleep(LOOP_DELAY)                                      # delay before polling again

            # wait until motor Z reaches goal position (based on target and current position)
            if accuracy == "HIGH" or accuracy == "VERY HIGH":
                not_reachedZ = True
                while not_reachedZ:                                             # for higher accuracy, loop until (pres_pos - goal) <= threshold
                    pres_posZ = read4(Z, ADD_PRESENT_POS)
                    if debug:
                        print("Z goal position / present / error = %d / %d / %d" % (goalZ, pres_posZ, goalZ - pres_posZ))
                    not_reachedZ = (abs(pres_posZ - goalZ) > POS_ACC_THRESH_Z)
                    if not_reachedZ:
                        time.sleep(LOOP_DELAY)                                  # delay before polling again

    return


def move(motor, step, accuracy="HIGH"):
    """ Move motor position to a new position relative to current one (and check for boundary limits) - HV gimbal """
    global OVERSHOOT_H_ANG, OVERSHOOT_V_ANG, OVERSHOOT_P_ANG

    overshoot_H = convertangletopos(H, OVERSHOOT_H_ANG) - convertangletopos(H, 0)     # convert step angle to motor position step
    overshoot_V = convertangletopos(V, OVERSHOOT_V_ANG) - convertangletopos(V, 0)     # convert step angle to motor position step
    overshoot_P = convertangletopos(P, OVERSHOOT_P_ANG) - convertangletopos(P, 0)     # convert step angle to motor position step

    step_pos = convertangletopos(motor, step) - convertangletopos(motor, 0)     # convert step angle to motor position step

    cur_goal_pos = goal_pos(motor, 1)                                           # read the current goal position
    if motor is V:
        if num_motors >= 2:
            if abs(step_pos) < 1:                                               # check step size is not lower than resolution
                print("step is too small for this motor, increase step size, to move")
            else:                                                               # prevent loop around on V
                if (step_pos + cur_goal_pos)> X_RES/2+V0 or (step_pos + cur_goal_pos) < -1*X_RES/2+V0:
                    print ("limit up   " +str(X_RES/2+V0))
                    print ("limit down " +str(-1*X_RES/2+V0))
                    print ("target     "  +str(step_pos + cur_goal_pos))
                    print("please go back on V out of range")
                else:
                    pos=(step_pos + cur_goal_pos)
                    print("motor vertical target position =  " + str(pos))
                    angle=convertpostoangle(V, pos)
                    print("target vertical angle =  " + str(angle))
                    if accuracy == "VERY HIGH":
                        write4(motor, ADD_GOAL_POSITION, pos - overshoot_V)     # overshoot goal V position first
                        wait_stop_moving(accuracy)
                    write4(motor, ADD_GOAL_POSITION, pos)                       # go to final goal V position
                    wait_stop_moving(accuracy)                                  # wait for motor to stop moving
        else:
            if step != 0:
                print("WARNING: Trying to move V motor, but motor not detected")

    elif motor is H:
        if abs(step_pos) < 1:                                                   # check step size is not lower than resolution
            print("step is too small for this motor, increase step size, to move")
        else:                                                                   # prevent loop around on H
            if (step_pos + cur_goal_pos) > (base_res*base_ratio)/2+h_zero or (step_pos + cur_goal_pos) < (-1*base_res*base_ratio)/2+h_zero:
                print("please go back on H out of range")
            else:
                pos = (step_pos + cur_goal_pos)
                print("Motor horizontal target position =  " + str(pos))
                angle = convertpostoangle(H, pos)
                print("Target horizontal angle =  " + str(angle))
                if accuracy == "VERY HIGH":
                    write4(motor, ADD_GOAL_POSITION + ram_offset, pos - overshoot_H)    # overshoot goal H position first
                    wait_stop_moving(accuracy)                                  # wait for motor to stop moving
                write4(motor, ADD_GOAL_POSITION + ram_offset, pos)              # go to final goal H position
                wait_stop_moving(accuracy)                                      # wait for motor to stop moving

    elif motor is P:
        if num_motors >= 4:
            if abs(step_pos) < 1:                                               # check step size is not lower than resolution
                print("step is too small for this motor, increase step size, to move")
            else:                                                               # prevent loop around on P
                if (step_pos + cur_goal_pos)> X_RES*P_RATIO/2+P0 or (step_pos + cur_goal_pos) < -1*X_RES*P_RATIO/2+P0:
                    print("please go back on P out of range")
                else:
                    pos=(step_pos + cur_goal_pos)
                    print("motor Polarization target position =  " + str(pos))
                    angle=convertpostoangle(P, pos)
                    print("target vertical angle =  " + str(angle))
                    if accuracy == "VERY HIGH":
                        write4(motor, ADD_GOAL_POSITION, pos - overshoot_P)     # overshoot goal P position first
                        wait_stop_moving(accuracy)
                    write4(motor, ADD_GOAL_POSITION, pos)                       # go to final goal P position
                    wait_stop_moving(accuracy)                                  # wait for motor to stop moving
        else:
            if step != 0:
                print("WARNING: Trying to move P motor, but motor not detected")

    else:
        print(" Warning motor selection is wrong")

    return


def move_sph(motor, step, accuracy="HIGH"):
    """ Move motor position to a new position relative to current one (and check for boundary limits) - SPHERICAL gimbal """
    global OVERSHOOT_TH_ANG, OVERSHOOT_PH_ANG

    overshoot_H = convertangletopos(H, OVERSHOOT_TH_ANG) - convertangletopos(H, 0)  # convert step angle to motor position step
    overshoot_T = convertangletopos(T, OVERSHOOT_PH_ANG) - convertangletopos(T, 0)  # convert step angle to motor position step
    overshoot_Z = convertangletopos(Z, OVERSHOOT_PH_ANG) - convertangletopos(Z, 0)  # convert step angle to motor position step

    if motor is TH:
        step_pos_H = convertangletopos(H, step) - convertangletopos(H, 0)       # convert step angle to motor position step
        cur_goal_pos_H = goal_pos(H, 1)                                         # read the current goal position
    elif motor is PH:
        step_pos_T = convertangletopos(T, step) - convertangletopos(T, 0)       # positive PHI step is positive T and Z steps
        cur_goal_pos_T = goal_pos(T, 1)

        step_pos_Z = convertangletopos(Z, step) - convertangletopos(Z, 0)
        cur_goal_pos_Z = goal_pos(Z, 1)
    elif motor is DPH:
        step_pos_Z = convertangletopos(Z, -step) - convertangletopos(Z, 0)      # positive DPHI step is negative Z step
        cur_goal_pos_Z = goal_pos(Z, 1)
    elif motor is T:
        step_pos_T = convertangletopos(T, step) - convertangletopos(T, 0)       # positive T steps
        cur_goal_pos_T = goal_pos(T, 1)

    if motor is TH:
        if abs(step_pos_H) < 1:                                                   # check step size is not lower than resolution
            print("step is too small for this motor, increase step size, to move")
        else:                                                                   # prevent loop around on H
            if (step_pos_H + cur_goal_pos_H) > (base_res*base_ratio)/2+h_zero or (step_pos_H + cur_goal_pos_H) < (-1*base_res*base_ratio)/2+h_zero:
                print("please go back on H out of range")
            else:
                pos = (step_pos_H + cur_goal_pos_H)
                print("Motor horizontal target position =  " + str(pos))
                angle = convertpostoangle(H, pos)
                print("Target horizontal angle =  " + str(angle))
                if accuracy == "VERY HIGH":
                    write4(H, ADD_GOAL_POSITION + ram_offset, pos - overshoot_H)         # overshoot goal H position first
                    wait_stop_moving(accuracy)                                  # wait for motor to stop moving
                write4(H, ADD_GOAL_POSITION + ram_offset, pos)                  # go to final goal H position
                wait_stop_moving(accuracy)                                      # wait for motor to stop moving

    elif motor is PH:
        if num_motors >= 6:
            if abs(step_pos_T) < 1 or abs(step_pos_Z) < 1:                      # check step size is not lower than resolution
                print("step is too small for this motor, increase step size, to move")
            else:                                                               # prevent loop around on T
                if (step_pos_T + cur_goal_pos_T)> X_RES*T_RATIO/2+T0 or (step_pos_T + cur_goal_pos_T) < -1*X_RES*T_RATIO/2+T0:
                    print ("limit up   " +str(X_RES*T_RATIO/2+T0))
                    print ("limit down " +str(-1*X_RES*T_RATIO/2+T0))
                    print ("target     "  +str(step_pos_T + cur_goal_pos_T))
                    print("please go back on T out of range")
                else:                                                           # prevent loop around on Z
                    if (step_pos_Z + cur_goal_pos_Z) > X_RES*Z_RATIO/2+Z0 or (step_pos_Z + cur_goal_pos_Z) < -1*X_RES*Z_RATIO/2+Z0:
                        print ("limit up   " + str(X_RES*Z_RATIO / 2 + Z0))
                        print ("limit down " + str(-1 * X_RES*Z_RATIO / 2 + Z0))
                        print ("target     " + str(step_pos_Z + cur_goal_pos_Z))
                        print("please go back on Z out of range")
                    else:
                        pos_T=(step_pos_T + cur_goal_pos_T)
                        print("motor T target position =  " + str(pos_T))
                        angle=convertpostoangle(T, pos_T)
                        print("target T angle =  " + str(angle))
                        pos_Z=(step_pos_Z + cur_goal_pos_Z)
                        print("motor Z target position =  " + str(pos_Z))
                        angle=convertpostoangle(Z, pos_Z)
                        print("target Z angle =  " + str(angle))

                        if accuracy == "VERY HIGH":
                            write4(T, ADD_GOAL_POSITION, pos_T - overshoot_T)   # overshoot goal T position first
                            write4(Z, ADD_GOAL_POSITION, pos_Z - overshoot_Z)   # overshoot goal Z position first
                            wait_stop_moving(accuracy)
                        write4(T, ADD_GOAL_POSITION, pos_T)                     # go to final goal T position
                        write4(Z, ADD_GOAL_POSITION, pos_Z)                     # go to final goal Z position
                        wait_stop_moving(accuracy)                              # wait for motor to stop moving
        else:
            if step != 0:
                print("WARNING: Trying to move PHI motor, but motor T and Z not detected")

    elif motor is DPH:
        if num_motors >= 6:
            if abs(step_pos_Z) < 1:                                             # check step size is not lower than resolution
                print("step is too small for this motor, increase step size, to move")
            else:                                                               # prevent loop around on Z
                if (step_pos_Z + cur_goal_pos_Z)> X_RES*Z_RATIO/2+Z0 or (step_pos_Z + cur_goal_pos_Z) < -1*X_RES*Z_RATIO/2+Z0:
                    print ("limit up   " +str(X_RES/2+Z0))
                    print ("limit down " +str(-1*X_RES/2+Z0))
                    print ("target     "  +str(step_pos_Z + cur_goal_pos_Z))
                    print("please go back on Z out of range")
                else:
                    pos_Z=(step_pos_Z + cur_goal_pos_Z)
                    print("motor Z target position =  " + str(pos_Z))
                    angle=convertpostoangle(Z, pos_Z)
                    print("target vertical angle =  " + str(angle))
                    if accuracy == "VERY HIGH":
                        write4(Z, ADD_GOAL_POSITION, pos_Z - overshoot_Z)       # overshoot goal V position first
                        wait_stop_moving(accuracy)
                    write4(Z, ADD_GOAL_POSITION, pos_Z)                         # go to final goal V position
                    wait_stop_moving(accuracy)                                  # wait for motor to stop moving
        else:
            if step != 0:
                print("WARNING: Trying to move DPHI motor, but Z motor not detected")

    elif motor is T:
        if num_motors >= 6:
            if abs(step_pos_T) < 1:                                             # check step size is not lower than resolution
                print("step is too small for this motor, increase step size, to move")
            else:                                                               # prevent loop around on T
                if (step_pos_T + cur_goal_pos_T)> X_RES*T_RATIO/2+T0 or (step_pos_T + cur_goal_pos_T) < -1*X_RES*T_RATIO/2+T0:
                    print ("limit up   " +str(X_RES*T_RATIO/2+T0))
                    print ("limit down " +str(-1*X_RES*T_RATIO/2+T0))
                    print ("target     "  +str(step_pos_T + cur_goal_pos_T))
                    print("please go back on T out of range")
                else:
                    pos_T=(step_pos_T + cur_goal_pos_T)
                    print("motor T target position =  " + str(pos_T))
                    angle=convertpostoangle(T, pos_T)
                    print("target T angle =  " + str(angle))

                    if accuracy == "VERY HIGH":
                        write4(T, ADD_GOAL_POSITION, pos_T - overshoot_T)   # overshoot goal T position first
                        wait_stop_moving(accuracy)
                    write4(T, ADD_GOAL_POSITION, pos_T)                     # go to final goal T position
                    wait_stop_moving(accuracy)                              # wait for motor to stop moving
        else:
            if step != 0:
                print("WARNING: Trying to move T motor, but motor T not detected")

    else:
        print(" Warning motor (%d) selection is wrong" % motor)

    return


def jump_H(hpos):
    """ makes H motor move to a given absolute position
    does not wait for motor to stop moving before returning """
    write4(H, ADD_GOAL_POSITION + ram_offset, int(hpos))                        # move to H goal position
    return


def jump_V(vpos):
    """ makes V motor move to a given absolute position
    does not wait for motor to stop moving before returning """
    if num_motors >= 2:
        write4(V, ADD_GOAL_POSITION, int(vpos))                                 # move to V goal position if motor exists
    else:
        if convertpostoangle(V, vpos) != 0:                                     # if V motor does not exist, and try to move to non-zero angle, print WARNING
            print("WARNING: Trying to move Motor V that does not exist")
    return


def jump_P(ppos):
    """ makes P motor move to a given absolute position
    does not wait for motor to stop moving before returning """
    if num_motors >= 4:
        write4(P, ADD_GOAL_POSITION, int(ppos))                                 # move to P goal position if motor exists
    else:
        if convertpostoangle(P, ppos) != 0:                                     # if P motor does not exist, and try to move to non-zero angle, print WARNING
            print("WARNING: Trying to move Motor P that does not exist")
    return


def jump_T(tpos):
    """ makes T motor move to a given absolute position
    does not wait for motor to stop moving before returning """
    if num_motors >= 5:
        write4(T, ADD_GOAL_POSITION, int(tpos))                                 # move to T goal position if motor exists
    else:
        if convertpostoangle(T, tpos) != 0:                                     # if T motor does not exist, and try to move to non-zero angle, print WARNING
            print("WARNING: Trying to move Motor T that does not exist")
    return


def jump_Z(zpos):
    """ makes Z motor move to a given absolute position
    does not wait for motor to stop moving before returning """
    if num_motors >= 6:
        write4(Z, ADD_GOAL_POSITION, int(zpos))                                 # move to Z goal position if motor exists
    else:
        if convertpostoangle(Z, zpos) != 0:                                     # if Z motor does not exist, and try to move to non-zero angle, print WARNING
            print("WARNING: Trying to move Motor Z that does not exist")
    return


def jump_TH(thpos):
    """ makes TH motor move to a given absolute position
    does not wait for motor to stop moving before returning """
    jump_H(thpos)
    return


def jump_PH(pos):
    """ makes PH motor move to a given absolute position
    does not wait for motor to stop moving before returning """
    tpos = pos[0]
    zpos = pos[1]
    jump_T(tpos)
    jump_Z(zpos)
    return


def jump_angle_H(hang, accuracy="HIGH"):
    """ makes H motor move to a given absolute angle """
    global OVERSHOOT_H_ANG
    h_pos = convertangletopos(H, hang)                                          # calculate H goal position

    if accuracy == "VERY HIGH":
        overshoot_H = convertangletopos(H, OVERSHOOT_H_ANG) - convertangletopos(H, 0)  # convert overshoot angle to motor position step
        jump_H(h_pos - overshoot_H)                                             # for very high accuracy, overshoot H goal position first
        wait_stop_moving(accuracy)                                              # wait for motor to stop moving

    jump_H(h_pos)                                                               # move to H goal position
    wait_stop_moving(accuracy)                                                  # wait for motor to stop moving
    return


def jump_angle_V(vang, accuracy="HIGH"):
    """ makes V motor move to a given absolute angle """
    global OVERSHOOT_V_ANG
    v_pos = convertangletopos(V, vang)                                          # calculate V goal position

    if num_motors >= 2:
        if accuracy == "VERY HIGH":
            overshoot_V = convertangletopos(V, OVERSHOOT_V_ANG) - convertangletopos(V, 0)  # convert overshoot angle to motor position step
            jump_V(v_pos - overshoot_V)                                         # for very high accuracy, overshoot V goal position first
            wait_stop_moving(accuracy)                                          # wait for motor to stop moving

        jump_V(v_pos)                                                           # move to V goal position if motor exists
        wait_stop_moving(accuracy)                                              # wait for motor to stop moving
    else:
        if vang != 0:                                                           # if V motor does not exist, and try to move to non-zero angle, print WARNING
            print("WARNING: Trying to move Motor V that does not exist")

    return


def jump_angle_P(pang, accuracy="HIGH"):
    """ makes P motor move to a given absolute angle """
    global OVERSHOOT_P_ANG
    p_pos = convertangletopos(P, pang)                                          # calculate P goal position

    if num_motors >= 4:
        if accuracy == "VERY HIGH":
            overshoot_P = convertangletopos(P, OVERSHOOT_P_ANG) - convertangletopos(P, 0)  # convert overshoot angle to motor position step
            jump_P(p_pos - overshoot_P)                                         # for very high accuracy, overshoot P goal position first
            wait_stop_moving(accuracy)                                          # wait for motor to stop moving

        jump_P(p_pos)                                                           # move to P goal position if motor exists
        wait_stop_moving(accuracy)                                              # wait for motor to stop moving
    else:
        if pang != 0:                                                           # if P motor does not exist, and try to move to non-zero angle, print WARNING
            print("WARNING: Trying to move Motor P that does not exist")

    return


def jump_angle_TH(thang, accuracy="HIGH"):
    """ makes TH motor move to a given absolute angle """
    global OVERSHOOT_TH_ANG
    th_pos = convertangletopos(TH, thang)                                       # calculate TH goal position

    if accuracy == "VERY HIGH":
        overshoot_TH = convertangletopos(TH, OVERSHOOT_TH_ANG) - convertangletopos(TH, 0)  # convert overshoot angle to motor position step
        jump_TH(th_pos - overshoot_TH)                                          # for very high accuracy, overshoot TH goal position first
        wait_stop_moving(accuracy)                                              # wait for motor to stop moving

    jump_TH(th_pos)                                                             # move to TH goal position if motor exists
    wait_stop_moving(accuracy)                                                  # wait for motor to stop moving

    return


def jump_angle_PH(phang, accuracy="HIGH"):
    """ makes PH motor move to a given absolute angle """
    global OVERSHOOT_PH_ANG
    ph_pos = convertangletopos(PH, phang)                                       # calculate PH goal position

    if accuracy == "VERY HIGH":
        ph_cur_goal_pos = goal_pos(PH, 1)
        overshoot_T = convertangletopos(T, OVERSHOOT_PH_ANG) - convertangletopos(T, 0)  # convert overshoot angle to motor position step
        overshoot_Z = convertangletopos(Z, OVERSHOOT_PH_ANG) - convertangletopos(Z, 0)  # convert overshoot angle to motor position step

        if ph_pos[0] != ph_cur_goal_pos[0]:                                     # if need to move
            jump_T(ph_pos[0] - overshoot_T)                                     # for very high accuracy, overshoot T goal position first
        if ph_pos[1] != ph_cur_goal_pos[1]:                                     # if need to move
            jump_Z(ph_pos[1] - overshoot_Z)                                     # for very high accuracy, overshoot Z goal position first
        wait_stop_moving(accuracy)                                              # wait for motor to stop moving

    jump_PH(ph_pos)                                                             # move to PH goal position if motor exists
    wait_stop_moving(accuracy)                                                  # wait for motor to stop moving

    return


def jump_angle(hang, vang, pang, accuracy="HIGH"):
    """ makes all motors move to a given absolute angle for HV gimbal """
    global OVERSHOOT_H_ANG, OVERSHOOT_V_ANG, OVERSHOOT_P_ANG

    if gim_type == HV:
        h_pos = convertangletopos(H, hang)                                                      # calculate H goal position
        overshoot_H = convertangletopos(H, OVERSHOOT_H_ANG) - convertangletopos(H, 0)           # convert overshoot angle to motor position step
        if num_motors >= 2:
            v_pos = convertangletopos(V, vang)                                                  # calculate V goal position
            overshoot_V = convertangletopos(V, OVERSHOOT_V_ANG) - convertangletopos(V, 0)       # convert overshoot angle to motor position step

            if num_motors >= 4:
                p_pos = convertangletopos(P, pang)                                              # calculate P goal position
                overshoot_P = convertangletopos(P, OVERSHOOT_P_ANG) - convertangletopos(P, 0)   # convert overshoot angle to motor position step

        if accuracy == "VERY HIGH":
            h_cur_goal_pos = goal_pos(H, 1)
            if h_pos != h_cur_goal_pos:                                         # if need to move
                jump_H(h_pos - overshoot_H)                                     # for very high accuracy, overshoot H goal position first
            if num_motors >= 2:
                v_cur_goal_pos = goal_pos(V, 1)
                if v_pos != v_cur_goal_pos:                                     # if need to move
                    jump_V(v_pos - overshoot_V)                                 # for very high accuracy, overshoot V goal position first
                if num_motors >= 4:
                    p_cur_goal_pos = goal_pos(P, 1)
                    if p_pos != p_cur_goal_pos:                                 # if need to move
                        jump_P(p_pos - overshoot_P)                             # for very high accuracy, overshoot P goal position first
            wait_stop_moving(accuracy)                                          # wait for all motors to stop moving

        jump_H(h_pos)                                                           # go to final H position
        if num_motors >= 2:
            jump_V(v_pos)                                                       # go to final V position
            if num_motors >= 4:
                jump_P(p_pos)                                                   # go to final P position
        wait_stop_moving(accuracy)                                              # wait for all motors to stop moving
    else:
        print("Incorrect gimbal type. jump_angle() used for HV gimbal")

    return


def jump_angle_sph(thang, phang, accuracy="HIGH"):
    """ makes all motors move to a given absolute angle for SPHERICAL gimbal """
    global OVERSHOOT_TH_ANG, OVERSHOOT_PH_ANG

    th_pos = convertangletopos(TH, thang)                                               # calculate TH goal position
    overshoot_TH = convertangletopos(TH, OVERSHOOT_TH_ANG) - convertangletopos(TH, 0)   # convert overshoot angle to motor position step
    if num_motors >= 6:
        ph_pos = convertangletopos(PH, phang)                                           # calculate PH goal position
        overshoot_T = convertangletopos(T, OVERSHOOT_PH_ANG) - convertangletopos(T, 0)  # convert overshoot angle to motor position step
        overshoot_Z = convertangletopos(Z, OVERSHOOT_PH_ANG) - convertangletopos(Z, 0)  # convert overshoot angle to motor position step

    if accuracy == "VERY HIGH":
        th_cur_goal_pos = goal_pos(TH, 1)
        if th_pos != th_cur_goal_pos:                                           # if need to move
            jump_TH(th_pos - overshoot_TH)                                      # for very high accuracy, overshoot TH goal position first
        if num_motors >= 6:
            t_cur_goal_pos = goal_pos(T, 1)
            if ph_pos[0] != t_cur_goal_pos:                                     # if need to move
                jump_T(ph_pos[0] - overshoot_T)                                 # for very high accuracy, overshoot T goal position first

            z_cur_goal_pos = goal_pos(Z, 1)
            if ph_pos[1] != z_cur_goal_pos:                                     # if need to move
                jump_Z(ph_pos[1] - overshoot_Z)                                 # for very high accuracy, overshoot Z position first
        wait_stop_moving(accuracy)                                              # wait for all motors to stop moving

    jump_TH(th_pos)                                                             # move to final TH position
    if num_motors >= 6:
        jump_PH([ph_pos[0], ph_pos[1]])                                         # move to final [PH, DPH] position
    wait_stop_moving(accuracy)                                                  # wait for all motors to stop moving

    return


def check_move(h_target, v_target, p_target):                                   # check that the move values are in range
    """ check the move is doable """
    ok = 1
    if (abs(h_target) > 180) or \
            ((v_target is not None) and (abs(v_target) > 180)) or \
            ((p_target is not None) and (abs(p_target) > 180)):
        ok = 0
    # else:
    #     print("---->  target values okay")
    return ok


def check_move_sph(theta_target, phi_target):                                   # check that the move values are in range
    """ check the move is doable """
    ok = 1
    if (abs(theta_target) > 180) or \
            ((phi_target[0] is not None) and (abs(phi_target[0]) > 180)) or \
            ((phi_target[1] is not None) and (abs(phi_target[0]-phi_target[1]) > 180)):
        ok = 0
    # else:
    #     print("---->  target values okay")
    return ok


def gim_move(h_target, v_target, p_target, accuracy="HIGH"):                    # move H and V motors to any H,V position in space
    """ make a direct move and measure the move time """
    t0 = time.time()                                                            # record start time
    if check_move(h_target, v_target, p_target) == 1:
        jump_angle(h_target, v_target, p_target, accuracy)                      # do the move
    else:
        print(" ERROR: move location out of valid range")
    t1 = time.time()                                                            # record stop time
    travel_time = (t1 - t0)                                                     # measure travel time
    print(" travel time was : %0.3f seconds" % travel_time)                     # print travel time


def gim_move_sph(theta_target, phi_target, accuracy="HIGH"):                    # move GIM05 motors to any theta/phi position in space
    """ make a direct move and measure the move time """
    t0 = time.time()                                                            # record start time
    if check_move_sph(theta_target, phi_target) == 1:
        jump_angle_sph(theta_target, phi_target, accuracy)
    else:
        print(" ERROR: move location out of valid range")
    t1 = time.time()                                                            # record stop time
    travel_time = (t1 - t0)                                                     # measure travel time
    print(" travel time was : %0.3f seconds" % travel_time)                     # print travel time


def gotoZERO(accuracy="HIGH"):
    """ makes all motors go home """
    print("going to zero position")
    if gim_type == HV:
        # jump_angle(7.51, -6.33, 0, accuracy)
        # jump_angle(0.21, -34.98, 0, accuracy)
        jump_angle(-0.15, 0.44, 0, accuracy)
        
        
    elif gim_type == SPHERICAL:
        jump_angle_sph(0, [0, 0], accuracy)
    return


# ===========================================================
# ============= MEASUREMENT EQUIPMENT FUNCTIONS =============
# ===========================================================

def select_meas_mode(cur_mode="UNDEFINED"):
    """ select if using SA, SG+SA, or VNA """
    print("\nCurrent measurement mode = %s\n" % cur_mode)
    print("************* MEASUREMENT SETUP *************")
    print("* press <0> for No Instrument")
    print("* press <1> for Spectrum Analyzer only")
    print("* press <2> for SigGen + Spectrum Analyzer")
    print("* press <3> for VNA")
    print("* press <ESC> for no change")
    print("*********************************************")
    valid = False
    while not valid:
        pressedkey = ord(getch())
        if pressedkey == ord('0'):
            meas_mode = "NONE"
            print("NO EQUIPMENT mode selected")
            valid = True
        elif pressedkey == ord('1'):
            meas_mode = 'SA'
            print("Spectrum Analyzer mode selected")
            valid = True
        elif pressedkey == ord('2'):
            meas_mode = 'SG+SA'
            print("Sig Gen + Spectrum Analyzer mode selected")
            valid = True
        elif pressedkey == ord('3'):
            meas_mode = 'VNA'
            print("VNA mode selected")
            valid = True
        elif pressedkey == 27:
            meas_mode = cur_mode
            if meas_mode != "UNDEFINED":
                valid = True
            else:
                print("Must select a valid measurement mode")
    return meas_mode


def select_visa_addr(orig_addr="SIMULATION"):
    """ displays list of connected VISA instruments and selects one """
    print("")
    print("************** INSTRUMENT LIST **************")
    resources = equip.list_resources()                                          # find list of potential instruments
    resources = [x for x in resources if str(x).find('ASRL') == -1]             # only keep resources without "ASRL" in name
    resources.insert(0, 'MANUAL ENTRY (%s)' % orig_addr)                        # pre-pend "MANUAL ENTRY" to the list - used to type in a socket address
    resources.insert(0, 'SIMULATION')                                           # pre-pend "SIMULATION" to the list - used if no instrument connected

    for x in range(0, len(resources), 1):                                       # list all the resources
        if orig_addr == resources[x]:
            print("  >>> %3d) %s" % (x+1, resources[x]))                        # show which equipment is currently selected
        else:
            print("      %3d) %s" % (x+1, resources[x]))
    print("*********************************************")
    print("")

    done = False
    while not done:
        selection = int(input_num("Select instrument or enter <0> for no change: "))
        if selection in range(len(resources)+1):
            if selection == 0:
                new_addr = orig_addr
                done = True
            elif selection == 2:                                                # manual entry
                new_addr = str(six.moves.input("Enter equipment VISA address: "))
                done = True
            else:
                new_addr = str(resources[selection-1])                          # set the name of the GPIB resource, convert from unicode to string
                done = True
        else:
            print("Invalid selection. Please try again")

    print ("")
    print("Measurement instrument selected (addr): %s" % (new_addr))

    return new_addr


def visa(orig_meas_mode, inst):
    """ list all potential VISA instruments connected, select and initialize for measurement """

    orig_addr = inst.addr
    inst.close_instrument()

    meas_mode = select_meas_mode(orig_meas_mode)

    # Spectrum Analyzer mode
    if meas_mode == "SA":
        if orig_meas_mode != meas_mode:
            orig_addr = ["SIMULATION"]                                          # if previous was not SA, set default to SIMULATION

        print("Select Spectrum Analyzer VISA address")
        new_addr = [select_visa_addr(orig_addr[0])]                             # select Spectrum Analyzer

        inst = equip.inst_setup(meas_mode, new_addr)                            # initialize equipment

    # SigGen + SpecAnalyzer mode
    elif meas_mode == "SG+SA":
        if orig_meas_mode != meas_mode:
            orig_addr = ["SIMULATION", "SIMULATION"]                            # if previous was not SG+SA, set default to SIMULATION

        print("\n\nSelect SIG GEN VISA address")
        sg_addr = select_visa_addr(orig_addr[0])                                # select Sig Gen
        print("\n\nSelect SPECTRUM ANALYZER VISA address")
        sa_addr = select_visa_addr(orig_addr[1])                                # select Spectrum Analyzer
        new_addr = [sg_addr, sa_addr]

        inst = equip.inst_setup(meas_mode, new_addr)                            # initialize equipment

    # VNA mode
    elif meas_mode == "VNA":
        if orig_meas_mode != meas_mode:
            orig_addr = ["SIMULATION"]                                          # if previous was not VNA, set default to SIMULATION

        print("Select VNA VISA address")
        new_addr = [select_visa_addr(orig_addr[0])]                             # select VNA

        inst = equip.inst_setup(meas_mode, new_addr)                            # initialize equipment

    # NONE or undefined mode
    else:
        inst = equip.inst_setup(meas_mode, ["SIMULATION"])                      # initialize SIMULATION mode

    if inst.port_open:                                                          # if instrument is open
        print("initializing equipment")
        inst.init_meas()                                                        # initialize instrument for measurement

    return meas_mode, inst


def get_power(inst):
    """ return measured power at a given gimbal (H,V) position or compute value if no instrument connected """

    # readback power from instrument
    if inst.port_open:
        if inst.inst_type.find("SA") > -1:
            try:
                inst.single_trigger()                                           # single trigger and hold if it has been implemented
            except:
                pass
            val = [round(float(inst.get_marker(1)),2)]                          # readback marker 1 if connected to an instrument
            freq = [float(inst.get_marker_freq(1))]                             # readback marker 1 freq
        elif inst.inst_type.find("VNA") > -1:
            try:
                inst.single_trigger()                                           # single trigger and hold if it has been implemented
            except:
                pass
            val, phase = inst.get_s_dbphase()                                   # readback S21
            val = [round(x,2) for x in val]                                     # round values to 2 digits
            freq = inst.get_freq_list()                                         # readback frequency list
            # inst.cont_trigger()

    # compute simulated power level based on (H,V) position
    else:                                                                       # compute DUMMY value based on gimbal position if not connected to instrument
        if gim_type == HV:
            hori_ang = convertpostoangle(H,current_pos(H,1))
            vert_ang = convertpostoangle(V,current_pos(V,1))
            val = [round(((vert_ang ** 2 + 0.6 * hori_ang ** 2) * (-1 / 300.0)),2)] # DUMMY val, when instrument is not connected
        elif gim_type == SPHERICAL:
            theta_ang = convertpostoangle(TH,current_pos(TH,1))
            phi_ang, dphi_ang = convertpostoangle(PH,current_pos(PH,1))
            val = [round(((theta_ang ** 2 * (2.0 - np.sin(phi_ang*np.pi/180)**2)) * (-1 / 300.0)),2)] # DUMMY val, when instrument is not connected

        freq = [28.0e9]

    return val, freq


# =================================================
# ============= SWEEP CHECK FUNCTIONS =============
# =================================================

def input_num(prompt, default=None):
    """ prompt for a number and wait until a valid number is returned """
    ok = False
    while not ok:
        s = six.moves.input(prompt)                                                       # display prompt and wait for input, does not crash on empty string six make it 2.x and 3.x compatible
        if len(s) == 0:
            s = str(default)
        try:
            x = float(s)
            ok = True
        except ValueError:
            print ("\n*** ERROR: Please enter a valid number ***\n")
    return x


def check_plot_1d(dir, minh, maxh, minv, maxv, step, pola=None):
    """ check that user plot values are valid for 1D sweep """
    ok = 1
    if (minh < -180) or (minv < -180):
        ok = 0
    if (maxh > 180) or (maxv > 180):
        ok = 0
    if (maxh-minh) < 0:
        ok = 0
    if (maxv-minv) < 0:
        ok = 0
    if dir == "H" and step > (maxh-minh):
        ok = 0
    if dir == "V" and step > (maxv-minv):
        ok = 0
    if step <= 0:
        ok = 0
    if pola is not None:
        if (pola > 180) or (pola < -180):
            ok = 0
    return ok


def check_plot_1d_sph(dir, minth, maxth, minph, maxph, step, dphi=None):
    """ check that user plot values are valid for 1D sweep """
    ok = 1
    if (minth < -180) or (minph < -180):
        ok = 0
    if (maxth > 180) or (maxph > 180):
        ok = 0
    if (maxth-minth) < 0:
        ok = 0
    if (maxph-minph) < 0:
        ok = 0
    if dir == "T" and step > (maxth-minth):
        ok = 0
    if dir == "P" and step > (maxph-minph):
        ok = 0
    if step <= 0:
        ok = 0
    if dphi is not None:
        if (maxph - dphi > 180) or (minph - dphi < -180):
            ok = 0
    return ok


def check_plot(minh, maxh, minv, maxv, step, pola=None):
    """ check that user plot values are valid """
    ok = 1
    if (minh < -180) or (minv < -180):
        ok = 0
    if (maxh > 180) or (maxv > 180):
        ok = 0
    if (maxh-minh) < 0:
        ok = 0
    if (maxv-minv) < 0:
        ok = 0
    if step > (maxh-minh):
        ok = 0
    if step > (maxv-minv):
        ok = 0
    if step <= 0:
        ok = 0
    if pola is not None:
        if (pola > 180) or (pola < -180):
            ok = 0
    return ok


def check_plot_sph(minth, maxth, minph, maxph, step, dphi=None):
    """ check that user plot values are valid """
    ok = 1
    if (minth < -180) or (minph < -180):
        ok = 0
    if (maxth > 180) or (maxph > 180):
        ok = 0
    if (maxth-minth) < 0:
        ok = 0
    if (maxph-minph) < 0:
        ok = 0
    if step > (maxth-minth):
        ok = 0
    if step > (maxph-minph):
        ok = 0
    if step <= 0:
        ok = 0
    if dphi is not None:
        if (maxph-dphi > 180) or (minph-dphi < -180):
            ok = 0
    return ok


def check_abort():
    """ check if <ESC> was pressed to abort measurement sweep """
    keypressed = chr(ord(getch()))
    if keypressed == chr(27):
        print("")
        print("Are you sure you want to ABORT? [Y/N]")
        while keypressed not in ['Y', 'N']:
            keypressed = chr(ord(getch().upper()))
        if keypressed == 'Y':
            print("*** ABORTING ***")
            print("")
    else:
        keypressed = ''
    return keypressed == 'Y'


# =================================================
# ================ SWEEP FUNCTIONS ================
# =================================================

def millibox_1dsweep(dir, minh, maxh, minv, maxv, step, pangle, plot, tag, inst, accuracy="HIGH", meas_delay=0, plot_freq=0):
    """ 1D sweep - capture, plot and save the data """

    # print ("millibox_1dsweep: pangle = ", pangle)
    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_capture_'+timeStr+'_1d_'+dir+'_'+tag+'.csv')   # format CSV filename
    print(" Plot data is saved in file : " +str(filename))                      # tell user filename
    csvplot = open(filename, 'w', buffering=1)                                  # open CSV file for write
    capture = csv.writer(csvplot, lineterminator='\n')                          # set line terminator to newline only (no carraige return)

    val, freq = get_power(inst)                                                 # query the frequency points

    if num_motors >= 4:
        capture.writerow(['V', 'actual_V', 'H', 'actual_H', 'P', 'actual_P'] + freq)    # write the column headers to file (include pol)
    else:
        capture.writerow(['V', 'actual_V', 'H', 'actual_H'] + freq)             # write the column headers to file

    freqIdx = np.abs(np.array(freq) - plot_freq).argmin()                       # find index for value that is closest to plot_freq
    print("\n**** Plotting frequency = %0.3fGHz ****\n" % (freq[freqIdx]/1.0e9))

    num = int(np.floor((maxv-minv)/step))                                       # map of vertical angle iteration
    Vangle = np.linspace(minv,minv+num*step,num+1)                              # [min:step:max] with endpoints inclusive
    num = int(np.floor((maxh-minh)/step))                                       # map of horizontal angle iteration
    Hangle = np.linspace(minh,minh+num*step,num+1)                              # [min:step:max] with endpoints inclusive

    print(" V range is = " + str(Vangle))                                       # log tracker
    print(" H range is = " + str(Hangle))                                       # log tracker
    if num_motors >= 4:
        print(" Polarization position is = " + str(pangle))
        jump_angle_P(pangle, accuracy)

    inst.fix_status()                                                           # check and run calibration, if needed

    if dir == "H":
        heatmap = [np.nan for x in Hangle]                                      # Initialize heatmap array with all point = NaN
        i = 0
        total = len(Hangle)                                                     # total number of measurement points
        vert = min(Vangle)                                                      # vert angle is fixed during sweep
        jump_angle_V(vert, accuracy)                                            # jump to vert angle
        for hori in Hangle:                                                     # loop for horizontal motion

            if kbhit():                                                         # check if key pressed
                if check_abort():                                               # check if <ESC> pressed
                    gotoZERO(accuracy)                                          # go to home and abort
                    csvplot.close()
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return

            jump_angle_H(hori, accuracy)                                        # move to H position

            time.sleep(meas_delay)                                              # optional delay after movement before measuring
            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            actual_H = convertpostoangle(H, current_pos(H, 1))                  # record actual absolute position moto H reached
            actual_V = convertpostoangle(V, current_pos(V, 1))                  # record actual absolute position moto V reached

            if num_motors >= 4:
                actual_P = convertpostoangle(P, current_pos(P, 1))
                if len(val) == 1:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))
                else:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))

                entry = [vert, actual_V, hori, actual_H, pangle, actual_P] + val                     # record a new plot entry

            else:
                if len(val) == 1:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,val[freqIdx]))
                else:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,val[freqIdx]))

                entry = [vert, actual_V,  hori, actual_H] + val                     # record a new plot entry

            capture.writerow(entry)                                             # commit to CSV file
            heatmap[i] = val[freqIdx]                                           # append heatmap with actual captured val
            i += 1                                                              # update counter

            n = i                                                               # compute iterations completed
            t1 = time.time()                                                    # get the current time
            elapsed = t1 - t0                                                   # compute elapsed time
            total_time = elapsed / n * total                                    # estimate total time
            remain = total_time - elapsed                                       # compute remaining time
            print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

            if hori == Hangle[-1]:                                              # last point
                try:
                    inst.cont_trigger()                                         # enable cont_trigger if it has been implemented
                except:
                    pass
                gotoZERO(accuracy)                                              # go to (0,0)
                csvplot.close()                                                 # close the CSV file
                print("## THE PLOT WAS SAVED IN FILE :  " + str(filename) + "    ##")  # tell user where to find CSV file
                t1 = time.time()
                print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))   # display elapsed time
            if plot == 1:
                display_1dplot(dir,Vangle,Hangle,heatmap,vert,hori,plot_freq=freq[freqIdx],pangle=pangle)   # update the line plot after each data point

    elif dir == "V":
        heatmap = [np.nan for x in Vangle]                                      # Initialize heatmap array with all point = NaN
        i = 0
        total = len(Vangle)                                                     # total number of measurement points
        hori = min(Hangle)                                                      # hori angle is fixed during sweep
        jump_angle_H(hori, accuracy)                                            # jump to hori angle
        for vert in Vangle:                                                     # loop for vertical motion

            if kbhit():                                                         # check if key pressed
                if check_abort():                                               # check if <ESC> pressed
                    gotoZERO(accuracy)                                          # go to home and abort
                    csvplot.close()
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return

            jump_angle_V(vert, accuracy)                                        # move to V position

            time.sleep(meas_delay)                                              # optional delay after movement before measuring
            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            actual_H = convertpostoangle(H, current_pos(H, 1))                  # record actual absolute position moto H reached
            actual_V = convertpostoangle(V, current_pos(V, 1))                  # record actual absolute position moto V reached

            if num_motors >= 4:
                actual_P = convertpostoangle(P, current_pos(P, 1))
                if len(val) == 1:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))
                else:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))

                entry = [vert, actual_V, hori, actual_H, pangle, actual_P] + val                     # record a new plot entry

            else:
                if len(val) == 1:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,val[freqIdx]))
                else:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,val[freqIdx]))

                entry = [vert, actual_V,  hori, actual_H] + val                     # record a new plot entry

            capture.writerow(entry)                                             # commit to CSV file
            heatmap[i] = val[freqIdx]                                           # append heatmap with actual captured val
            i += 1                                                              # update counter

            n = i                                                               # compute iterations completed
            t1 = time.time()                                                    # get the current time
            elapsed = t1 - t0                                                   # compute elapsed time
            total_time = elapsed / n * total                                    # estimate total time
            remain = total_time - elapsed                                       # compute remaining time
            print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

            if vert == Vangle[-1]:                                              # last point
                try:
                    inst.cont_trigger()                                         # enable cont_trigger if it has been implemented
                except:
                    pass
                gotoZERO(accuracy)                                              # go to (0,0)
                csvplot.close()                                                 # close the CSV file
                print("## THE PLOT WAS SAVED IN FILE :  " + str(filename) + "    ##")  # tell user where to find CSV file
                t1 = time.time()
                print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))   # display elapsed time

            if plot == 1:
                display_1dplot(dir,Vangle,Hangle,heatmap,vert,hori,plot_freq=freq[freqIdx],pangle=pangle)     # update the line plot after each data point

    return


def millibox_1dsweep_sph(dir, minth, maxth, minph, maxph, step, dphi, plot, tag, inst, accuracy="HIGH", meas_delay=0, plot_freq=0):
    """ 1D sweep (spherical coords) - capture, plot and save the data """

    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_capture_'+timeStr+'_1d_sph_'+dir+'_'+tag+'.csv')   # format CSV filename
    print(" Plot data is saved in file : " +str(filename))                      # tell user filename
    csvplot = open(filename, 'w', buffering=1)                                  # open CSV file for write
    capture = csv.writer(csvplot, lineterminator='\n')                          # set line terminator to newline only (no carraige return)

    val, freq = get_power(inst)                                                 # query the frequency points

    if num_motors >= 6:
        capture.writerow(['PHI', 'actual_PHI', 'THETA', 'actual_THETA', 'DPHI', 'actual_DPHI'] + freq)  # write the column headers to file (include pol)
    else:
        capture.writerow(['PHI', 'actual_PHI', 'THETA', 'actual_THETA'] + freq)                         # write the column headers to file

    freqIdx = np.abs(np.array(freq) - plot_freq).argmin()                       # find index for value that is closest to plot_freq
    print("\n**** Plotting frequency = %0.3fGHz ****\n" % (freq[freqIdx]/1.0e9))

    num = int(np.floor((maxph-minph)/step))                                     # map of PHI angle iteration
    PHangle = np.linspace(minph,minph+num*step,num+1)                           # [min:step:max] with endpoints inclusive
    num = int(np.floor((maxth-minth)/step))                                     # map of THETA angle iteration
    THangle = np.linspace(minth,minth+num*step,num+1)                           # [min:step:max] with endpoints inclusive

    print(" PHI range is = " + str(PHangle))                                    # log tracker
    print(" THETA range is = " + str(THangle))                                  # log tracker
    if num_motors >= 6:
        print(" DPHI position is = " + str(dphi))

    inst.fix_status()                                                           # check and run calibration, if needed

    if dir == "T":
        heatmap = [np.nan for x in THangle]                                     # Initialize heatmap array with all point = NaN
        i = 0
        total = len(THangle)                                                    # total number of measurement points
        phi = min(PHangle)                                                      # PHI angle is fixed during sweep
        jump_angle_PH([phi, dphi], accuracy)                                    # jump to PHI angle
        for theta in THangle:                                                   # loop for THETA motion

            if kbhit():                                                         # check if key pressed
                if check_abort():                                               # check if <ESC> pressed
                    gotoZERO(accuracy)                                          # go to home and abort
                    csvplot.close()
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return

            jump_angle_TH(theta, accuracy)                                      # move to THETA position

            time.sleep(meas_delay)                                              # optional delay after movement before measuring
            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            actual_TH = convertpostoangle(TH, current_pos(TH, 1))               # record actual absolute position motor TH reached
            actual_PH, actual_DPH = convertpostoangle(PH, current_pos(PH, 1))   # record actual absolute position motor PH reached

            if num_motors >= 6:
                if len(val) == 1:
                    print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=%0.2f" % (phi,actual_PH,theta,actual_TH,dphi,actual_DPH,val[freqIdx]))
                else:
                    print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=[ ... %0.2f ... ]" % (phi,actual_PH,theta,actual_TH,dphi,actual_DPH,val[freqIdx]))

                entry = [phi, actual_PH, theta, actual_TH, dphi, actual_DPH] + val          # record a new plot entry

            capture.writerow(entry)                                             # commit to CSV file
            heatmap[i] = val[freqIdx]                                           # append heatmap with actual captured val
            i += 1                                                              # update counter

            n = i                                                               # compute iterations completed
            t1 = time.time()                                                    # get the current time
            elapsed = t1 - t0                                                   # compute elapsed time
            total_time = elapsed / n * total                                    # estimate total time
            remain = total_time - elapsed                                       # compute remaining time
            print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

            if theta == THangle[-1]:                                            # last point
                try:
                    inst.cont_trigger()                                         # enable cont_trigger if it has been implemented
                except:
                    pass
                gotoZERO(accuracy)                                              # go to (0,0)
                csvplot.close()                                                 # close the CSV file
                print("## THE PLOT WAS SAVED IN FILE :  " + str(filename) + "    ##")  # tell user where to find CSV file
                t1 = time.time()
                print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))   # display elapsed time
            if plot == 1:
                display_1dplot_sph(dir, PHangle, THangle, heatmap, phi, theta, plot_freq=freq[freqIdx],
                                   dphi=dphi)  # update the line plot after each data point

    elif dir == "P":
        heatmap = [np.nan for x in PHangle]                                     # Initialize heatmap array with all point = NaN
        i = 0
        total = len(PHangle)                                                    # total number of measurement points
        theta = min(THangle)                                                    # THETA angle is fixed during sweep
        jump_angle_TH(theta, accuracy)                                          # jump to THETA angle
        for phi in PHangle:                                                     # loop for PHI motion

            if kbhit():                                                         # check if key pressed
                if check_abort():                                               # check if <ESC> pressed
                    gotoZERO(accuracy)                                          # go to home and abort
                    csvplot.close()
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return

            jump_angle_PH([phi, dphi], accuracy)                                # move to PH position

            time.sleep(meas_delay)                                              # optional delay after movement before measuring
            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            actual_TH = convertpostoangle(TH, current_pos(TH, 1))               # record actual absolute position motor TH reached
            actual_PH, actual_DPH = convertpostoangle(PH, current_pos(PH, 1))   # record actual absolute position motor PH reached

            if num_motors >= 6:
                if len(val) == 1:
                    print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=%0.2f" % (phi,actual_PH,theta,actual_TH,dphi,actual_DPH,val[freqIdx]))
                else:
                    print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=[ ... %0.2f ... ]" % (phi,actual_PH,theta,actual_TH,dphi,actual_DPH,val[freqIdx]))

                entry = [phi, actual_PH, theta, actual_TH, dphi, actual_DPH] + val          # record a new plot entry

            capture.writerow(entry)                                             # commit to CSV file
            heatmap[i] = val[freqIdx]                                           # append heatmap with actual captured val
            i += 1                                                              # update counter

            n = i                                                               # compute iterations completed
            t1 = time.time()                                                    # get the current time
            elapsed = t1 - t0                                                   # compute elapsed time
            total_time = elapsed / n * total                                    # estimate total time
            remain = total_time - elapsed                                       # compute remaining time
            print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

            if phi == PHangle[-1]:                                              # last point
                try:
                    inst.cont_trigger()                                         # enable cont_trigger if it has been implemented
                except:
                    pass
                gotoZERO(accuracy)                                              # go to (0,0)
                csvplot.close()                                                 # close the CSV file
                print("## THE PLOT WAS SAVED IN FILE :  " + str(filename) + "    ##")  # tell user where to find CSV file
                t1 = time.time()
                print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))   # display elapsed time
            if plot == 1:
                display_1dplot_sph(dir, PHangle, THangle, heatmap, phi, theta, plot_freq=freq[freqIdx],
                                   dphi=dphi)  # update the line plot after each data point

    return


def millibox_hvsweep(min, max, step, pangle, plot, tag, inst, accuracy="HIGH", meas_delay=0, plot_freq=0):
    """ 1D sweep in H and V planes - capture, plot and save the data """

    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_capture_'+timeStr+'_hv_'+tag+'.csv')   # format CSV filename
    print(" Plot data is saved in file : " +str(filename))                      # tell user filename
    csvplot = open(filename, 'w', buffering=1)                                  # open CSV file for write
    capture = csv.writer(csvplot, lineterminator='\n')                          # set line terminator to newline only (no carraige return)

    val, freq = get_power(inst)                                                 # query the frequency points

    if num_motors >= 4:
        capture.writerow(['V', 'actual_V', 'H', 'actual_H', 'P', 'actual_P'] + freq)    # write the column headers to file (include pol)
    else:
        capture.writerow(['V', 'actual_V', 'H', 'actual_H'] + freq)             # write the column headers to file

    freqIdx = np.abs(np.array(freq) - plot_freq).argmin()                       # find index for value that is closest to plot_freq
    print("\n**** Plotting frequency = %0.3fGHz ****\n" % (freq[freqIdx]/1.0e9))

    num = int(np.floor((max-min)/step))                                         # map of vertical angle iteration
    Vangle = np.linspace(min,min+num*step,num+1)                                # [min:step:max] with endpoints inclusive
    num = int(np.floor((max-min)/step))                                         # map of horizontal angle iteration
    Hangle = np.linspace(min,min+num*step,num+1)                                # [min:step:max] with endpoints inclusive
    print(" V range is = " + str(Vangle))                                       # log tracker
    print(" H range is = " + str(Hangle))                                       # log tracker
    if num_motors >= 4:
        print(" Polarization position is = " + str(pangle))
        jump_angle_P(pangle, accuracy)                                          # make the polarization move

    heatmapV = [np.nan for x in Vangle]                                         # Initialize heatmap array with all point = NaN
    heatmapH = [np.nan for x in Hangle]                                         # Initialize heatmap array with all point = NaN

    i = 0
    total = len(Hangle) + len(Vangle)                                           # total number of points
    vert = 0                                                                    # Hsweep with vert=0
    jump_angle_V(vert, accuracy)                                                # jump to vert angle

    inst.fix_status()                                                           # check and run calibration, if needed

    for hori in Hangle:                                                         # loop for horizontal motion

        if kbhit():                                                             # check if key pressed
            if check_abort():                                                   # check if <ESC> pressed
                gotoZERO(accuracy)                                              # go to home and abort
                csvplot.close()
                if six.PY2:
                    plt.close('all')                                            # automatically close plot for Py2.x
                else:
                    print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                    plt.ioff()
                    plt.show(block=True)                                        # manually close plot for Py3.x
                return

        jump_angle_H(hori,accuracy)                                             # make the move

        time.sleep(meas_delay)                                                  # optional delay after movement before measuring
        val, freq = get_power(inst)                                             # #####################  this is where you get the value from measurement ####################

        actual_H = convertpostoangle(H, current_pos(H, 1))                      # record actual absolute position motor H reached
        actual_V = convertpostoangle(V, current_pos(V, 1))                      # record actual absolute position motor V reached
        if num_motors >= 4:
            actual_P = convertpostoangle(P, current_pos(P, 1))
            if len(val) == 1:
                print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))
            else:
                print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))

            entry = [vert, actual_V,  hori, actual_H, pangle, actual_P] + val                     # record a new plot entry

        else:
            if len(val) == 1:
                print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,val[freqIdx]))
            else:
                print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,val[freqIdx]))

            entry = [vert, actual_V,  hori, actual_H] + val                     # record a new plot entry

        capture.writerow(entry)                                                 # commit to CSV file

        heatmapH[i] = val[freqIdx]                                              # append heatmap with actual captured val
        i += 1                                                                  # update counter

        n = i                                                                   # compute iterations completed
        t1 = time.time()                                                        # get the current time
        elapsed = t1 - t0                                                       # compute elapsed time
        total_time = elapsed / n * total                                        # estimate total time
        remain = total_time - elapsed                                           # compute remaining time
        print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

        if hori == Hangle[-1]:
            if num_motors >= 4:
                jump_angle(0, 0, pangle, accuracy)                              # go to (0,0,pol) after last point
            else:
                gotoZERO(accuracy)                                              # go to (0,0) after last point

        if plot == 1:
            blocking = 0                                                        # set interactive (non-blocking) plot
            display_hvplot(Vangle,Hangle,heatmapV,heatmapH,blocking,plot_freq=freq[freqIdx],pangle=pangle)    # update the line plot after each data point

    i = 0
    hori = 0                                                                    # Vsweep with hori=0
    jump_angle_H(hori, accuracy)                                                # jump to hori angle

    inst.fix_status()                                                           # check and run calibration, if needed

    for vert in Vangle:                                                         # loop for vertical motion

        if kbhit():                                                             # check if key pressed
            if check_abort():                                                   # check if <ESC> pressed
                gotoZERO(accuracy)                                              # go to home and abort
                csvplot.close()
                if six.PY2:
                    plt.close('all')                                            # automatically close plot for Py2.x
                else:
                    print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                    plt.ioff()
                    plt.show(block=True)                                        # manually close plot for Py3.x
                return

        jump_angle_V(vert,accuracy)                                             # make the move

        time.sleep(meas_delay)                                                  # optional delay after movement before measuring
        val, freq = get_power(inst)                                             # #####################  this is where you get the value from measurement ####################

        actual_H = convertpostoangle(H, current_pos(H, 1))                      # record actual absolute position moto H reached
        actual_V = convertpostoangle(V, current_pos(V, 1))                      # record actual absolute position moto V reached
        if num_motors >= 4:
            actual_P = convertpostoangle(P, current_pos(P, 1))
            if len(val) == 1:
                print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))
            else:
                print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))

            entry = [vert, actual_V,  hori, actual_H, pangle, actual_P] + val                     # record a new plot entry

        else:
            if len(val) == 1:
                print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,val[freqIdx]))
            else:
                print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,val[freqIdx]))

            entry = [vert, actual_V,  hori, actual_H] + val                     # record a new plot entry
        capture.writerow(entry)                                                 # commit to CSV file

        heatmapV[i] = val[freqIdx]                                              # append heatmap with actual captured val
        i += 1                                                                  # update counter

        n = i + len(Hangle)                                                     # compute iterations completed
        t1 = time.time()                                                        # get the current time
        elapsed = t1 - t0                                                       # compute elapsed time
        total_time = elapsed / n * total                                        # estimate total time
        remain = total_time - elapsed                                           # compute remaining time
        print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

        if vert == Vangle[-1]:                                                  # last point
            try:
                inst.cont_trigger()                                             # enable cont_trigger if it has been implemented
            except:
                pass
            gotoZERO(accuracy)                                                  # go to (0,0)
            t1 = time.time()
            print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))  # display elapsed time
        if plot == 1:
            blocking = 0                                                        # set interactive (non-blocking) plot
            display_hvplot(Vangle,Hangle,heatmapV,heatmapH,blocking,plot_freq=freq[freqIdx],pangle=pangle)    # update the line plot after each data point

    csvplot.close()                                                             # close the CSV file
    print("## THE PLOT WAS SAVED IN FILE :  " +str(filename) + "    ##")        # tell user where to find CSV file

    if plot == 1:
        blocking = 1
        display_hvplot(Vangle,Hangle,heatmapV,heatmapH,blocking,plot_freq=freq[freqIdx],pangle=pangle)        # re-plot data as blocking

    return


def millibox_hvsweep_sph(min, max, step, dphi, plot, tag, inst, accuracy="HIGH", meas_delay=0, plot_freq=0):
    """ 1D sweep in Phi=0 and Phi=90 planes - capture, plot and save the data """

    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_capture_'+timeStr+'_hv_sph_'+tag+'.csv')   # format CSV filename
    print(" Plot data is saved in file : " +str(filename))                      # tell user filename
    csvplot = open(filename, 'w', buffering=1)                                  # open CSV file for write
    capture = csv.writer(csvplot, lineterminator='\n')                          # set line terminator to newline only (no carraige return)

    val, freq = get_power(inst)                                                 # query the frequency points

    if num_motors >= 6:
        capture.writerow(['PHI', 'actual_PHI', 'THETA', 'actual_THETA', 'DPHI', 'actual_DPHI'] + freq)  # write the column headers to file (include pol)
    else:
        capture.writerow(['PHI', 'actual_PHI', 'THETA', 'actual_THETA'] + freq)             # write the column headers to file

    freqIdx = np.abs(np.array(freq) - plot_freq).argmin()                       # find index for value that is closest to plot_freq
    print("\n**** Plotting frequency = %0.3fGHz ****\n" % (freq[freqIdx]/1.0e9))

    num = int(np.floor((max-min)/step))                                         # map of THETA angle iteration
    THangle = np.linspace(min,min+num*step,num+1)                               # [min:step:max] with endpoints inclusive
    PHangle = np.array([0.0, 90.0])
    print(" PH range is = " + str(PHangle))                                     # log tracker
    print(" TH range is = " + str(THangle))                                     # log tracker
    if num_motors >= 6:
        print(" DPHI position is = " + str(dphi))

    heatmapPH00 = [np.nan for x in THangle]                                     # Initialize heatmap array with all point = NaN
    heatmapPH90 = [np.nan for x in THangle]                                     # Initialize heatmap array with all point = NaN

    i = 0
    total = len(THangle) * len(PHangle)                                         # total number of points
    phi = 0                                                                     # THETA sweep with PHI=0
    jump_angle_PH([phi, dphi], accuracy)                                        # jump to PHI angle

    inst.fix_status()                                                           # check and run calibration, if needed

    for theta in THangle:                                                       # loop for THETA motion

        if kbhit():                                                             # check if key pressed
            if check_abort():                                                   # check if <ESC> pressed
                gotoZERO(accuracy)                                              # go to home and abort
                csvplot.close()
                if six.PY2:
                    plt.close('all')                                            # automatically close plot for Py2.x
                else:
                    print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                    plt.ioff()
                    plt.show(block=True)                                        # manually close plot for Py3.x
                return

        jump_angle_TH(theta,accuracy)                                           # make the move

        time.sleep(meas_delay)                                                  # optional delay after movement before measuring
        val, freq = get_power(inst)                                             # #####################  this is where you get the value from measurement ####################

        actual_TH = convertpostoangle(TH, current_pos(TH, 1))                   # record actual absolute position motor TH reached
        actual_PH, actual_DPH = convertpostoangle(PH, current_pos(PH, 1))       # record actual absolute position motor PH reached

        if num_motors >= 6:
            if len(val) == 1:
                print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=%0.2f" % (phi,actual_PH,theta,actual_TH,dphi,actual_DPH,val[freqIdx]))
            else:
                print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=[ ... %0.2f ... ]" % (phi,actual_PH,theta,actual_TH,dphi,actual_DPH,val[freqIdx]))

            entry = [phi, actual_PH, theta, actual_TH, dphi, actual_DPH] + val  # record a new plot entry

        capture.writerow(entry)                                                 # commit to CSV file

        heatmapPH00[i] = val[freqIdx]                                           # append heatmap with actual captured val
        i += 1                                                                  # update counter

        n = i                                                                   # compute iterations completed
        t1 = time.time()                                                        # get the current time
        elapsed = t1 - t0                                                       # compute elapsed time
        total_time = elapsed / n * total                                        # estimate total time
        remain = total_time - elapsed                                           # compute remaining time
        print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

        if theta == THangle[-1]:
            if num_motors >= 6:
                jump_angle_sph(0, [0, dphi], accuracy)                          # go to (0,0,dphi) after last point
            else:
                gotoZERO(accuracy)                                              # go to (0,0) after last point

        if plot == 1:
            blocking = 0                                                        # set interactive (non-blocking) plot
            display_hvplot_sph(PHangle,THangle,heatmapPH00,heatmapPH90,blocking,plot_freq=freq[freqIdx],dphi=dphi)    # update the line plot after each data point

    i = 0
    phi = 90                                                                    # THETA sweep with PHI=90
    jump_angle_PH([phi, dphi], accuracy)                                        # jump to PHI angle

    inst.fix_status()                                                           # check and run calibration, if needed

    for theta in THangle:                                                       # loop for THETA motion

        if kbhit():                                                             # check if key pressed
            if check_abort():                                                   # check if <ESC> pressed
                gotoZERO(accuracy)                                              # go to home and abort
                csvplot.close()
                if six.PY2:
                    plt.close('all')                                            # automatically close plot for Py2.x
                else:
                    print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                    plt.ioff()
                    plt.show(block=True)                                        # manually close plot for Py3.x
                return

        jump_angle_TH(theta,accuracy)                                           # make the move

        time.sleep(meas_delay)                                                  # optional delay after movement before measuring
        val, freq = get_power(inst)                                             # #####################  this is where you get the value from measurement ####################

        actual_TH = convertpostoangle(TH, current_pos(TH, 1))                   # record actual absolute position motor TH reached
        actual_PH, actual_DPH = convertpostoangle(PH, current_pos(PH, 1))       # record actual absolute position motor PH reached

        if num_motors >= 6:
            if len(val) == 1:
                print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=%0.2f" % (phi,actual_PH,theta,actual_TH,dphi,actual_DPH,val[freqIdx]))
            else:
                print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=[ ... %0.2f ... ]" % (phi,actual_PH,theta,actual_TH,dphi,actual_DPH,val[freqIdx]))

            entry = [phi, actual_PH, theta, actual_TH, dphi, actual_DPH] + val  # record a new plot entry

        capture.writerow(entry)                                                 # commit to CSV file

        heatmapPH90[i] = val[freqIdx]                                           # append heatmap with actual captured val
        i += 1                                                                  # update counter

        n = i + len(THangle)                                                    # compute iterations completed
        t1 = time.time()                                                        # get the current time
        elapsed = t1 - t0                                                       # compute elapsed time
        total_time = elapsed / n * total                                        # estimate total time
        remain = total_time - elapsed                                           # compute remaining time
        print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

        if theta == THangle[-1]:                                                # last point
            try:
                inst.cont_trigger()                                             # enable cont_trigger if it has been implemented
            except:
                pass
            gotoZERO(accuracy)                                                  # go to (0,0)
            t1 = time.time()
            print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))  # display elapsed time
        if plot == 1:
            blocking = 0                                                        # set interactive (non-blocking) plot
            display_hvplot_sph(PHangle,THangle,heatmapPH00,heatmapPH90,blocking,plot_freq=freq[freqIdx],dphi=dphi)    # update the line plot after each data point

    csvplot.close()                                                             # close the CSV file
    print("## THE PLOT WAS SAVED IN FILE :  " +str(filename) + "    ##")        # tell user where to find CSV file

    if plot == 1:
        blocking = 1
        display_hvplot_sph(PHangle,THangle,heatmapPH00,heatmapPH90,blocking,plot_freq=freq[freqIdx],dphi=dphi)        # re-plot data as blocking

    return


def millibox_2dsweep(minh, maxh, minv, maxv, step, pangle, plot, tag, inst, accuracy="HIGH", meas_delay=0, plot_freq=0, zigzag=False):
    """ 2D sweep - capture, plot and save the data - HV gimbal """

    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_capture_'+timeStr+'_2d_'+tag+'.csv')   # format CSV filename
    print(" Plot data is save in file : " +str(filename))                       # tell user filename
    csvplot = open(filename, 'w', buffering=1)                                  # open CSV file for write
    capture = csv.writer(csvplot, lineterminator='\n')                          # set line terminator to newline only (no carraige return)

    val, freq = get_power(inst)                                                 # query the frequency points

    if num_motors >= 4:
        capture.writerow(['V', 'actual_V', 'H', 'actual_H', 'P', 'actual_P'] + freq)    # write the column headers to file (include pol)
    else:
        capture.writerow(['V', 'actual_V', 'H', 'actual_H'] + freq)             # write the column headers to file
    freqIdx = np.abs(np.array(freq) - plot_freq).argmin()                       # find index for value that is closest to plot_freq
    print("\n**** Plotting frequency = %0.3fGHz ****\n" % (freq[freqIdx]/1.0e9))

    num = int(np.floor((maxv-minv)/step))                                       # map of vertical angle iteration
    Vangle = np.linspace(minv, minv+num*step, num+1)                            # [min:step:max] with endpoints inclusive
    num = int(np.floor((maxh-minh)/step))                                       # map of horizontal angle iteration
    Hangle = np.linspace(minh, minh+num*step, num+1)                            # [min:step:max] with endpoints inclusive

    heatmap = [[np.nan for x in Vangle] for y in Hangle]                        # Initialize heamap array with x is V, y is H with all point = NaN
    print(" V range is = " + str(Vangle))                                       # log tracker
    print(" H range is = " + str(Hangle))                                       # log tracker
    i = j = 0                                                                   # init loop counters
    total = len(Hangle) * len(Vangle)                                           # number of measurement points
    direction = 1                                                               # init direction for H movement
    blocking = False                                                            # only set final plot to blocking

    if num_motors >= 4:                                                         # if GIM04
        jump_angle_P(pangle, accuracy)                                          # move P to target position
    for vert in Vangle:                                                         # loop for vertical motion
        jump_angle_V(vert, accuracy)                                            # make the vertical move

        inst.fix_status()                                                       # check and run calibration, if needed

        entry_H = []                                                            # store all H sweep in single list before dumping to CSV
        if direction == 1:
            Hindex = range(0, len(Hangle), 1)                                   # set index to ascending
        else:
            Hindex = range(len(Hangle)-1, -1, -1)                               # set index to descending

        for hi in Hindex:                                                       # loop for horizontal motion
            hori = Hangle[hi]                                                   # H angle at current index

            if kbhit():                                                         # check for abort
                if check_abort():
                    gotoZERO(accuracy)
                    csvplot.close()
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return

            jump_angle_H(hori, accuracy)                                        # make the horizontal move

            time.sleep(meas_delay)                                              # optional delay after movement before measuring
            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            actual_H = convertpostoangle(H, current_pos(H, 1))                  # record actual absolute position motor H reached
            actual_V = convertpostoangle(V, current_pos(V, 1))                  # record actual absolute position motor V reached
            if num_motors >= 4:
                actual_P = convertpostoangle(P, current_pos(P, 1))              # record actual absolute position motor V reached
                if len(val) == 1:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))
                else:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,pangle,actual_P,val[freqIdx]))
                entry = [vert, actual_V,  hori, actual_H, pangle, actual_P] + val       # record a new plot entry
                # capture.writerow(entry)                                         # commit to CSV file
            else:
                if len(val) == 1:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=%0.2f" % (vert,actual_V,hori,actual_H,val[freqIdx]))
                else:
                    print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=[ ... %0.2f ... ]" % (vert,actual_V,hori,actual_H,val[freqIdx]))

                entry = [vert, actual_V,  hori, actual_H] + val                 # record a new plot entry
                # capture.writerow(entry)                                         # commit to CSV file

            if direction == 1:
                entry_H = entry_H + [entry]                                     # append entry to data if normal direction
            else:
                entry_H = [entry] + entry_H                                     # prepend entry to data if reverse direction

            heatmap[hi][j] = val[freqIdx]                                       # append heatmap with actual captured val

            i += 1                                                              # update H counter
            n = i + j * len(Hangle)                                             # compute iterations completed
            t1 = time.time()                                                    # get the current time
            elapsed = t1 - t0                                                   # compute elapsed time
            total_time = elapsed / n * total                                    # estimate total time
            remain = total_time - elapsed                                       # compute remaining time
            print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

            if vert == Vangle[-1] and hori == Hangle[Hindex[-1]]:               # last point
                try:
                    inst.cont_trigger()                                         # enable cont_trigger if it has been implemented
                except:
                    pass
                gotoZERO(accuracy)                                              # go to (0,0)
                print("## THE PLOT WAS SAVED IN FILE :  " + str(filename) + "    ##")  # tell user where to find CSV file
                t1 = time.time()
                print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))   # display elapsed time
                blocking = True                                                 # set last plot to blocking

            if plot == 3:                                                       # plot multi-line plot after each data point
                display_multilineplot(Vangle, Hangle, heatmap, vert, hori, plot_freq=freq[freqIdx], pangle=pangle, blocking=blocking)

        capture.writerows(entry_H)                                              # commit all H data to CSV file
        if zigzag:
            direction = -1 * direction                                          # switch direction if zigzag

        j += 1                                                                  # update V counter
        i = 0                                                                   # reset H counter

        if plot == 1:                                                           # interactive plot is not recommended for large plot, as it takes too much CPU resource
            display_surfplot(Vangle, Hangle, heatmap, vert, hori, plot_freq=freq[freqIdx], pangle=pangle, blocking=blocking)  # pass all values for interactive plot, last slice call to plot will be blocking here

        if plot == 2:                                                           # interactive plot is not recommended for large plot, as it takes too much CPU resource
            display_heatmap(Vangle, Hangle, heatmap, vert, hori, plot_freq=freq[freqIdx], pangle=pangle, blocking=blocking)  # pass all values for interactive plot, last slice call to plot will be blocking here

        print("")

    csvplot.close()                                                             # close the CSV file

    if plot > 0:
        display_millibox3d_ant_pattern(Vangle, Hangle, heatmap, vert, hori, step, plot_freq=freq[freqIdx], pangle=pangle, blocking=blocking)  # display 3D radiation pattern plot

    return


def millibox_2dsweep_sph(minth, maxth, minph, maxph, step, dphi, plot, tag, inst, accuracy="HIGH", meas_delay=0, plot_freq=0, zigzag=False):
    """ 2D sweep - capture, plot and save the data - SPHERICAL gimbal """

    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_capture_'+timeStr+'_2d_sph_'+tag+'.csv')   # format CSV filename
    print(" Plot data is save in file : " +str(filename))                       # tell user filename
    csvplot = open(filename, 'w', buffering=1)                                  # open CSV file for write
    capture = csv.writer(csvplot, lineterminator='\n')                          # set line terminator to newline only (no carraige return)

    val, freq = get_power(inst)                                                 # query the frequency points

    if num_motors >= 6:
        capture.writerow(['PHI', 'actual_PHI', 'THETA', 'actual_THETA', 'DPHI', 'actual_DPHI'] + freq)    # write the column headers to file (include pol)
    else:
        capture.writerow(['PHI', 'actual_PHI', 'THETA', 'actual_THETA'] + freq)         # write the column headers to file

    freqIdx = np.abs(np.array(freq) - plot_freq).argmin()                       # find index for value that is closest to plot_freq
    print("\n**** Plotting frequency = %0.3fGHz ****\n" % (freq[freqIdx]/1.0e9))

    num = int(np.floor((maxph-minph)/step))                                     # map of PHI angle iteration
    PHangle = np.linspace(minph, minph+num*step, num+1)                         # [min:step:max] with endpoints inclusive
    num = int(np.floor((maxth-minth)/step))                                     # map of THETA angle iteration
    THangle = np.linspace(minth, minth+num*step, num+1)                         # [min:step:max] with endpoints inclusive

    heatmap = [[np.nan for x in PHangle] for y in THangle]                      # Initialize heamap array with x is PH, y is TH with all point = NaN
    print(" PH range is = " + str(PHangle))                                     # log tracker
    print(" TH range is = " + str(THangle))                                     # log tracker
    i = j = 0                                                                   # init loop counters
    total = len(THangle) * len(PHangle)                                         # number of measurement points
    direction = 1                                                               # init direction for H movement
    blocking = False                                                            # only set final plot to blocking

    for phi in PHangle:                                                         # loop for PHI motion
        jump_angle_PH([phi, dphi], accuracy)                                    # make the PHI move

        inst.fix_status()                                                       # check and run calibration, if needed

        entry_TH = []                                                           # store all THETA sweep in single list before dumping to CSV
        if direction == 1:
            THindex = range(0, len(THangle), 1)                                 # set index to ascending
        else:
            THindex = range(len(THangle)-1, -1, -1)                             # set index to descending

        for thi in THindex:                                                     # loop for THETA motion
            theta = THangle[thi]                                                # THETA angle at current index

            if kbhit():                                                         # check for abort
                if check_abort():
                    gotoZERO(accuracy)
                    csvplot.close()
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return

            jump_angle_TH(theta, accuracy)                                      # make the THETA move

            time.sleep(meas_delay)                                              # optional delay after movement before measuring
            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            actual_TH = convertpostoangle(TH, current_pos(TH, 1))               # record actual absolute position motor TH reached
            actual_PH, actual_DPH = convertpostoangle(PH, current_pos(PH, 1))   # record actual absolute position motor PH reached

            if num_motors >= 6:
                if len(val) == 1:
                    print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=%0.2f" % (phi, actual_PH, theta, actual_TH, dphi, actual_DPH, val[freqIdx]))
                else:
                    print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=[ ... %0.2f ... ]" % (phi, actual_PH, theta, actual_TH, dphi, actual_DPH, val[freqIdx]))

                entry = [phi, actual_PH, theta, actual_TH, dphi, actual_DPH] + val  # record a new plot entry

                # capture.writerow(entry)                                       # commit to CSV file

            if direction == 1:
                entry_TH = entry_TH + [entry]                                   # append entry to data if normal direction
            else:
                entry_TH = [entry] + entry_TH                                   # prepend entry to data if reverse direction

            heatmap[thi][j] = val[freqIdx]                                      # append heatmap with actual captured val

            i += 1                                                              # update THETA counter
            n = i + j * len(THangle)                                            # compute iterations completed
            t1 = time.time()                                                    # get the current time
            elapsed = t1 - t0                                                   # compute elapsed time
            total_time = elapsed / n * total                                    # estimate total time
            remain = total_time - elapsed                                       # compute remaining time
            print("%5.1f %% complete - %s remaining" % (100.0*n/total, datetime.timedelta(seconds=int(remain))))    # print % complete and time remaining

            if phi == PHangle[-1] and theta == THangle[THindex[-1]]:            # last point
                try:
                    inst.cont_trigger()                                         # enable cont_trigger if it has been implemented
                except:
                    pass
                gotoZERO(accuracy)                                              # go to (0,0)
                print("## THE PLOT WAS SAVED IN FILE :  " + str(filename) + "    ##")  # tell user where to find CSV file
                t1 = time.time()
                print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))   # display elapsed time
                blocking = True                                                 # set last plot to blocking

        capture.writerows(entry_TH)                                             # commit all THETA data to CSV file
        if zigzag:
            direction = -1 * direction                                          # switch direction if zigzag

        j += 1                                                                  # update PHI counter
        i = 0                                                                   # reset THETA counter

        if plot == 1:                                                           # interactive plot is not recommended for large plot, as it takes too much CPU resource
            display_dir_cosine_sph(PHangle, THangle, heatmap, phi, theta, plot_freq=freq[freqIdx], dphi=dphi, blocking=blocking)  # pass all values for interactive plot, last slice call to plot will be blocking here
        if plot == 2:                                                           # interactive plot is not recommended for large plot, as it takes too much CPU resource
            display_polar_sph(PHangle, THangle, heatmap, phi, theta, plot_freq=freq[freqIdx], dphi=dphi, blocking=blocking)  # pass all values for interactive plot, last slice call to plot will be blocking here

        print("")

    csvplot.close()                                                             # close the CSV file

    if plot > 0:
        display_millibox3d_ant_pattern_sph(PHangle, THangle, heatmap, phi, theta, step, plot_freq=freq[freqIdx], dphi=dphi, blocking=blocking)  # display 3D radiation pattern plot

    return


def millibox_pat_sweep(pat_file, tag, inst, accuracy="HIGH", meas_delay=0, plot_freq=0):
    """ CSV-file defined pattern sweep - capture and save the data """

    patDir1 = os.path.join('..', '..', '_Internal', 'Patterns')                 # pattern search directory is ..\..\_Internal\Patterns
    patDir2 = os.path.join('.', 'patterns')                                     # pattern search directory is .\patterns
    path = ['', patDir1, patDir2]                                               # search path order

    filefound = False
    for pathdir in path:                                                        # search through the path in order
        if not filefound:                                                       # if file hasn't been found
            fullfile = os.path.join(pathdir, pat_file)                          # append the path to the filename
            if os.path.isfile(fullfile):
                filefound = True                                                # found = True
                pat_file = fullfile                                             # set pat_file with absolute path

    if not filefound:                                                           # if no file found
        if pat_file != '':
            print("*** ERROR: Pattern file %s does not exist! ***" % pat_file)  # if file does not exist, exit routine
        return
    else:
        print(" Pattern file: %s" % pat_file)                                   # display filename with full path

    csvin = open(pat_file, 'r')                                                 # open CSV file for read
    pattern = csv.reader(csvin, lineterminator='\n')                            # set line terminator to newline only (no carriage return)

    header = next(pattern)                                                      # check if pattern file type matches gimbal type
    if gim_type == HV:
        if header[0] != "H" or header[1] != "V" or header[2] != "P":
            print("*** ERROR: Pattern file does not match HV gimbal (H,V,P) ***")
            return
    if gim_type == SPHERICAL:
        if header[0] != "THETA" or header[1] != "PHI" or header[2] != "DPHI":
            print("*** ERROR: Pattern file does not match SPHERICAL gimbal (THETA,PHI,DPHI) ***")
            return

    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_capture_'+timeStr+'_pat_'+tag+'.csv')  # format CSV filename
    print(" Plot data is save in file : " +str(filename))                       # tell user filename
    csvout = open(filename, 'w', buffering=1)                                   # open CSV file for write
    capture = csv.writer(csvout, lineterminator='\n')                           # set line terminator to newline only (no carraige return)

    val, freq = get_power(inst)                                                 # query the frequency points

    if gim_type == HV:
        if num_motors >= 4:
            capture.writerow(['V', 'actual_V', 'H', 'actual_H', 'P', 'actual_P'] + freq)  # write the column headers to file (include pol)
        else:
            capture.writerow(['V', 'actual_V', 'H', 'actual_H'] + freq)         # write the column headers to file
    elif gim_type == SPHERICAL:
        if num_motors >= 6:
            capture.writerow(['PHI', 'actual_PHI', 'THETA', 'actual_THETA', 'DPHI', 'actual_DPHI'] + freq)    # write the column headers to file (include pol)

    freqIdx = np.abs(np.array(freq) - plot_freq).argmin()                       # find index for value that is closest to plot_freq
    print("\n**** Plotting frequency = %0.3fGHz ****\n" % (freq[freqIdx]/1.0e9))

    for angles in pattern:
        if gim_type == HV:
            hori = float(angles[0])
            vert = float(angles[1])
            pangle = float(angles[2])
            valid_move = check_move(hori, vert, pangle)
        elif gim_type == SPHERICAL:
            theta = float(angles[0])
            phi = float(angles[1])
            dphi = float(angles[2])
            valid_move = check_move_sph(theta, [phi, dphi])

        if valid_move:

            inst.fix_status()                                                   # check and run calibration, if needed

            if kbhit():                                                         # check for abort
                if check_abort():
                    gotoZERO(accuracy)
                    csvin.close()
                    csvout.close()
                    return

            if gim_type == HV:
                jump_angle(hori, vert, pangle, accuracy)                        # make the move

                time.sleep(meas_delay)                                          # optional delay after movement before measuring
                val, freq = get_power(inst)                                     # #####################  this is where you get the value from measurement ####################

                actual_H = convertpostoangle(H, current_pos(H, 1))              # record actual absolute position motor H reached
                actual_V = convertpostoangle(V, current_pos(V, 1))              # record actual absolute position motor V reached
                if num_motors >= 4:
                    actual_P = convertpostoangle(P, current_pos(P, 1))          # record actual absolute position motor P reached
                    if len(val) == 1:
                        print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=%0.2f" %
                              (vert, actual_V, hori, actual_H, pangle, actual_P, val[freqIdx]))
                    else:
                        print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| P=%+8.3f| actual_P=%+8.3f| VALUE=[ ... %0.2f ... ]" %
                              (vert, actual_V, hori, actual_H, pangle, actual_P, val[freqIdx]))
                    entry = [vert, actual_V, hori, actual_H, pangle, actual_P] + val  # record a new plot entry
                    capture.writerow(entry)                                     # commit to CSV file
                else:
                    if len(val) == 1:
                        print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=%0.2f" %
                              (vert, actual_V, hori, actual_H, val[freqIdx]))
                    else:
                        print("capture: V=%+8.3f| actual_V=%+8.3f| H=%+8.3f| actual_H=%+8.3f| VALUE=[ ... %0.2f ... ]" %
                              (vert, actual_V, hori, actual_H, val[freqIdx]))

                    entry = [vert, actual_V, hori, actual_H] + val              # record a new plot entry
                    capture.writerow(entry)                                     # commit to CSV file

            elif gim_type == SPHERICAL:
                jump_angle_sph(theta, [phi, dphi], accuracy)                        # make the move

                time.sleep(meas_delay)                                              # optional delay after movement before measuring
                val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

                actual_TH = convertpostoangle(TH, current_pos(TH, 1))               # record actual absolute position motor TH reached
                actual_PH, actual_DPH = convertpostoangle(PH, current_pos(PH, 1))   # record actual absolute position motor PH reached

                if num_motors >= 6:
                    if len(val) == 1:
                        print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=%0.2f" % (phi, actual_PH, theta, actual_TH, dphi, actual_DPH, val[freqIdx]))
                    else:
                        print("capture: PH=%+8.3f| actual_PH=%+8.3f| TH=%+8.3f| actual_TH=%+8.3f| DPH=%+8.3f| actual_DPH=%+8.3f| VALUE=[ ... %0.2f ... ]" % (phi, actual_PH, theta, actual_TH, dphi, actual_DPH, val[freqIdx]))

                    entry = [phi, actual_PH, theta, actual_TH, dphi, actual_DPH] + val  # record a new plot entry

                    capture.writerow(entry)                                     # commit to CSV file

    try:
        inst.cont_trigger()                                                     # enable cont_trigger if it has been implemented
    except:
        pass
    gotoZERO(accuracy)                                                          # go to (0,0)
    print("## THE SWEEP WAS SAVED IN FILE :  " + str(filename) + "    ##")      # tell user where to find CSV file
    t1 = time.time()
    print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1 - t0))))  # display elapsed time

    csvin.close()                                                               # close the CSV pattern file
    csvout.close()                                                              # close the CSV output file

    return


def milliboxacc(minh, maxh, minv, maxv, step, accuracy="HIGH", zigzag=False):
    """ capture position accuracy data, and save the data - HV gimbal """

    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_accuracy_'+timeStr+'.csv')             # format CSV filename
    print(" accuracy data is saved in file : " +str(filename))                  # tell user filename

    csvplot = open(filename, 'w', buffering=1)                                  # open CSV file for write
    capture = csv.writer(csvplot, lineterminator='\n')                          # set line terminator to newline only (no carraige return)
    capture.writerow(['V', 'Vquant', 'actual_V', 'H', 'Hquant', 'actual_H', 'Verr', 'Herr', 'Vtoterr', 'Htoterr'])        # write the column headers to file

    spanah = maxh - minh                                                        # calculate horizontal span in degree
    spanav = maxv - minv                                                        # calculate vertical span in degree

    num = int(np.floor((maxv-minv)/step))                                       # map of vertical angle iteration
    Vangle = np.linspace(minv,minv+num*step,num+1)                              # [min:step:max] with endpoints inclusive
    num = int(np.floor((maxh-minh)/step))                                       # map of horizontal angle iteration
    Hangle = np.linspace(minh,minh+num*step,num+1)                              # [min:step:max] with endpoints inclusive

    print(" x: V range is = " + str(Vangle))                                    # log tracker
    print(" y: H range is = " + str(Hangle))                                    # log tracker
    direction = 1                                                               # init direction for H movement

    for vert in Vangle:                                                         # loop for vertical motion
        print ("")
        jump_angle_V(vert, accuracy)                                            # jump to vert position

        entry_H = []                                                            # store all H sweep in single list before dumping to CSV
        if direction == 1:
            Hindex = range(0, len(Hangle), 1)                                   # set index to ascending
        else:
            Hindex = range(len(Hangle)-1, -1, -1)                               # set index to descending

        for hi in Hindex:                                                       # loop for horizontal motion
            hori = Hangle[hi]                                                   # H angle at current index

            if kbhit():
                if check_abort():
                    gotoZERO(accuracy)
                    csvplot.close()
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return

            jump_angle_H(hori, accuracy)                                        # make the move
            hquant = convertpostoangle(H,round(convertangletopos(H,hori)))      # compute the quantized H target angle
            vquant = convertpostoangle(V,round(convertangletopos(V,vert)))      # compute the quantized V target angle
            actual_H = convertpostoangle(H, current_pos(H, 1))
            actual_V = convertpostoangle(V, current_pos(V, 1))
            herr = actual_H - hquant                                            # error between actual and quantized
            verr = actual_V - vquant
            htoterr = actual_H - hori                                           # error between actual and target
            vtoterr = actual_V - vert
            entry = (vert, vquant, actual_V, hori, hquant, actual_H, verr, herr, vtoterr, htoterr)  # record a new plot entry
            print("capture: V=%+7.2f|V_quant=%+7.2f|actual_V=%+7.2f|H=%+7.2f|Hquant=%+7.2f|actual_H=%+7.2f|verr=%+7.2f|herr=%+7.2f|vtoterr=%+7.2f|htoterr=%+7.2f" % entry)
            # capture.writerow(list(entry))                                       # commit to CSV file

            if direction == 1:
                entry_H = entry_H + [entry]                                     # append entry to data if normal direction
            else:
                entry_H = [entry] + entry_H                                     # prepend entry to data if reverse direction

        capture.writerows(entry_H)                                              # commit all H data to CSV file
        if zigzag:
            direction = -1 * direction                                          # switch direction if zigzag

    csvplot.close()
    print("## THE PLOT WAS SAVED IN FILE :  " +str(filename) + "    ##")        # tell user where to find CSV file
    gotoZERO(accuracy)                                                          # always return to 0,0 when plot is done
    t1 = time.time()
    print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1 - t0))))  # display elapsed time

    return


def milliboxacc_sph(minth, maxth, minph, maxph, step, accuracy="HIGH", zigzag=False):
    """ capture position accuracy data, and save the data - SPHERICAL gimbal """

    t0 = time.time()                                                            # get the start time for routine
    timeStr = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())                # get day and time to build unique file names
    outdir = os.path.join('..', '..', 'MilliBox_plot_data')                     # outdir is ..\..\MilliBox_plot_data
    if not os.path.isdir(outdir):                                               # check if directory exists
        print("*** Creating output directory MilliBox_plot_data ***")
        os.mkdir(outdir)                                                        # create directory if it doesn't exist
    filename = os.path.join(outdir, 'mbx_accuracy_sph_'+timeStr+'.csv')         # format CSV filename
    print(" accuracy data is saved in file : " +str(filename))                  # tell user filename

    csvplot = open(filename, 'w', buffering=1)                                  # open CSV file for write
    capture = csv.writer(csvplot, lineterminator='\n')                          # set line terminator to newline only (no carraige return)
    capture.writerow(['PH', 'PHquant', 'actual_PH', 'TH', 'THquant', 'actual_TH', 'PHerr', 'THerr', 'PHtoterr', 'THtoterr'])        # write the column headers to file

    num = int(np.floor((maxph-minph)/step))                                     # map of PHI angle iteration
    PHangle = np.linspace(minph,minph+num*step,num+1)                           # [min:step:max] with endpoints inclusive
    num = int(np.floor((maxth-minth)/step))                                     # map of THETA angle iteration
    THangle = np.linspace(minth,minth+num*step,num+1)                           # [min:step:max] with endpoints inclusive

    print(" PH range is = " + str(PHangle))                                     # log tracker
    print(" TH range is = " + str(THangle))                                     # log tracker
    direction = 1                                                               # init direction for THETA movement

    for phi in PHangle:                                                         # loop for PHI motion
        print ("")
        jump_angle_PH([phi, 0], accuracy)                                       # jump to PHI position

        entry_TH = []                                                           # store all THETA sweep in single list before dumping to CSV
        if direction == 1:
            THindex = range(0, len(THangle), 1)                                 # set index to ascending
        else:
            THindex = range(len(THangle)-1, -1, -1)                             # set index to descending

        for thi in THindex:                                                     # loop for THETA motion
            theta = THangle[thi]                                                # THETA angle at current index

            if kbhit():
                if check_abort():
                    gotoZERO(accuracy)
                    csvplot.close()
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return

            jump_angle_TH(theta, accuracy)                                      # make the move
            thquant = convertpostoangle(TH,round(convertangletopos(TH,theta)))          # compute the quantized TH target angle
            phquant, dphquant = convertpostoangle(PH,convertangletopos(PH,[phi,0]))     # compute the quantized PH target angle
            actual_TH = convertpostoangle(TH, current_pos(TH, 1))
            actual_PH, actual_DPH = convertpostoangle(PH, current_pos(PH, 1))
            therr = actual_TH - thquant                                         # error between actual and quantized
            pherr = actual_PH - phquant
            thtoterr = actual_TH - theta                                        # error between actual and target
            phtoterr = actual_PH - phi
            entry = (phi, phquant, actual_PH, theta, thquant, actual_TH, pherr, therr, phtoterr, thtoterr)  # record a new plot entry
            print("capture: PH=%+7.2f|PH_quant=%+7.2f|actual_PH=%+7.2f|TH=%+7.2f|THquant=%+7.2f|actual_TH=%+7.2f|pherr=%+7.2f|therr=%+7.2f|phtoterr=%+7.2f|thtoterr=%+7.2f" % entry)
            # capture.writerow(list(entry))                                     # commit to CSV file

            if direction == 1:
                entry_TH = entry_TH + [entry]                                   # append entry to data if normal direction
            else:
                entry_TH = [entry] + entry_TH                                   # prepend entry to data if reverse direction

        capture.writerows(entry_TH)                                             # commit all THETA data to CSV file
        if zigzag:
            direction = -1 * direction                                          # switch direction if zigzag

    csvplot.close()
    print("## THE PLOT WAS SAVED IN FILE :  " +str(filename) + "    ##")        # tell user where to find CSV file
    gotoZERO(accuracy)                                                          # always return to 0,0 when plot is done
    t1 = time.time()
    print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1 - t0))))  # display elapsed time

    return


def center_of_mass(pos, val):
    """ compute center of mass for position/mass vectors """
    center_pos = np.sum(np.array(pos)*np.array(val)*1.0)/np.sum(np.array(val))
    return center_pos


def beam_align_hv_single(inst, minh=-90.0, maxh=90.0, minv=-90.0, maxv=90.0, step=1.0, pangle=0.0, vert0=0.0, accuracy="VERY HIGH", keepplot=False):
    """ electronic alignment of beam peak for HV Gimbal """

    H_off = None
    V_off = None

    if gim_type == HV:
        t0 = time.time()                                                        # get the start time for routine

        plot = 1

        num = int(np.floor((maxv-minv)/step))                                   # map of vertical angle iteration
        Vangle = np.linspace(minv,minv+num*step,num+1)                          # [minv:step:maxv] with endpoints inclusive
        num = int(np.floor((maxh-minh)/step))                                   # map of horizontal angle iteration
        Hangle = np.linspace(minh,minh+num*step,num+1)                          # [minh:step:maxh] with endpoints inclusive
        print(" x: V range is = " + str(Vangle))                                # log tracker
        print(" y: H range is = " + str(Hangle))                                # log tracker
        if num_motors >= 4:
            print(" p: Polarization position is = " + str(pangle))
            jump_angle_P(pangle, accuracy)                                      # make the polarization move

        heatmapV = [np.nan for x in Vangle]                                     # Initialize heatmap array with all point = NaN
        heatmapH = [np.nan for x in Hangle]                                     # Initialize heatmap array with all point = NaN

        print("H alignment sweep")

        i = 0
        print("Moving to V=%0.3f" % vert0)
        vert = vert0                                                            # Hsweep with vert=vert0
        jump_angle_V(vert, accuracy)                                            # jump to vert angle

        inst.fix_status()                                                       # check and run calibration, if needed

        for hori in Hangle:                                                     # loop for horizontal motion

            if kbhit():                                                         # check if key pressed
                if check_abort():                                               # check if <ESC> pressed
                    gotoZERO(accuracy)                                          # go to home and abort
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return H_off, V_off

            jump_angle_H(hori, accuracy)                                        # make the move

            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            freqIdx = int(len(val)/2)                                           # choose midpoint index
            # print("%+8.3f, %+8.3f" % (hori, val[freqIdx]))

            heatmapH[i] = val[freqIdx]                                          # append heatmap with actual captured val
            i += 1                                                              # update counter

            if hori == Hangle[-1]:
                if num_motors >= 4:
                    jump_angle(0, 0, pangle, accuracy)                          # go to (0,0,pol) after last point
                else:
                    jump_angle(0, 0, 0, accuracy)                               # go to (0,0) after last point

            if plot == 1:
                blocking = 0                                                    # set interactive (non-blocking) plot
                display_hvplot(Vangle,Hangle,heatmapV,heatmapH,blocking,plot_freq=freq[freqIdx],pangle=pangle)    # update the line plot after each data point

        heatmap = np.array(heatmapH)*1.0
        heatmap_rel = heatmap - heatmap.max()                                   # compute power relative to peak
        heatmap_mass = 10**(heatmap_rel/5.0)                                    # empirically use 10^(P_rel/5.0)

        H_off = center_of_mass(Hangle, heatmap_mass)                            # calculate center of mass
        print("H center = %0.3f" % H_off)

        print("V alignment sweep")

        i = 0
        print("Moving to H=%0.3f" % H_off)
        hori = H_off                                                            # Vsweep with hori=H_off
        jump_angle_H(hori, accuracy)                                            # jump to hori angle

        inst.fix_status()                                                       # check and run calibration, if needed

        for vert in Vangle:                                                     # loop for vertical motion

            if kbhit():                                                         # check if key pressed
                if check_abort():                                               # check if <ESC> pressed
                    gotoZERO(accuracy)                                          # go to home and abort
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return H_off, V_off

            jump_angle_V(vert, accuracy)                                        # make the move

            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            freqIdx = int(len(val)/2)                                           # choose midpoint index
            # print("%+8.3f, %+8.3f" % (vert,val[freqIdx]))

            heatmapV[i] = val[freqIdx]                                          # append heatmap with actual captured val
            i += 1                                                              # update counter

            if vert == Vangle[-1]:                                              # last point
                try:
                    inst.cont_trigger()                                         # enable cont_trigger if it has been implemented
                except:
                    pass
                jump_angle(0, 0, pangle, accuracy)                              # go to (0,0,pol) after last point
                t1 = time.time()
                print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))  # display elapsed time
            if plot == 1:
                blocking = 0                                                    # set interactive (non-blocking) plot
                block_final = False
                display_hvplot(Vangle,Hangle,heatmapV,heatmapH,blocking,plot_freq=freq[freqIdx],pangle=pangle,block_final=block_final)    # update the line plot after each data point

        heatmap = np.array(heatmapV)*1.0
        heatmap_rel = heatmap - heatmap.max()                                   # compute power relative to peak
        heatmap_mass = 10**(heatmap_rel/5.0)                                    # empirically use 10^(P_rel/5.0)

        V_off = center_of_mass(Vangle, heatmap_mass)                            # calculate center of mass
        print("V center = %0.3f" % V_off)

        vert = V_off
        jump_angle_V(vert, accuracy)                                            # jump to V_off angle

        if plot == 1:
            blocking = 1
            block_final = keepplot                                              # only block last point if final pass
            display_hvplot(Vangle,Hangle,heatmapV,heatmapH,blocking,plot_freq=freq[freqIdx],pangle=pangle,block_final=block_final)        # re-plot data as blocking

        jump_angle_H(H_off, accuracy)                                           # jump to H_off angle
        jump_angle_V(V_off, accuracy)                                           # jump to V_off angle

    else:
        print("ERROR: Incorrect gimbal type. Cannot run HV electronic alignment")

    return H_off, V_off


def beam_align_hv(inst, pangle=0.0, accuracy="VERY HIGH"):
    """ 2-pass electronic alignment of beam peak of HV Gimbal """

    H1 = None
    V1 = None

    if gim_type == HV:
        t0 = time.time()                                                        # get the start time for routine

        print("Coarse alignment search")                                        # coarse search with -90 90 -90 90 5
        H0, V0 = beam_align_hv_single(inst, -90, 90, -90, 90, 5, pangle, vert0=0.0, accuracy=accuracy, keepplot=False)
        if H0 is None or V0 is None:
            return H1, V1
        print("Coarse alignment center (H,V) = (%0.3f, %0.3f)" % (H0, V0))

        print("Fine alignment search")                                          # fine alignment search with +/-40 from (H0,V0)
        H0x = np.round(H0, 0)
        V0x = np.round(V0, 0)
        H1, V1 = beam_align_hv_single(inst, H0x-40, H0x+40, V0x-40, V0x+40, 1, pangle, vert0=V0, accuracy=accuracy, keepplot=True)
        if H1 is None or V1 is None:
            return H1, V1
        print("Fine alignment center (H,V) = (%0.3f, %0.3f)" % (H1, V1))

        jump_angle_H(H1, accuracy)                                              # move to found center (H1,V1)
        jump_angle_V(V1, accuracy)

        # t1 = time.time()
        # print("*** Total elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1 - t0))))     # display elapsed time

        print("")
        print("")
        print("******************************************")
        print("**** ELECTRONIC BEAM ALIGNMENT RESULT ****")
        print("******************************************")
        print("")
        print("         (H,V) = (%0.3f, %0.3f)" % (H1, V1))
        print("")

    return H1, V1


def beam_align_sph_single(inst, minth=-90.0, maxth=90.0, minph=-90.0, maxph=90.0, step=1.0, phi0=0.0, accuracy="VERY HIGH", keepplot=False):
    """ electronic alignment of beam peak of Spherical Gimbal """

    TH_off = None
    PH_off = None

    if gim_type == SPHERICAL:
        t0 = time.time()                                                        # get the start time for routine

        plot = 1

        num = int(np.floor((maxph-minph)/step))                                 # map of phi angle iteration
        PHangle = np.linspace(minph,minph+num*step,num+1)                       # [minph:step:maxph] with endpoints inclusive
        num = int(np.floor((maxth-minth)/step))                                 # map of theta angle iteration
        THangle = np.linspace(minth,minth+num*step,num+1)                       # [minth:step:maxth] with endpoints inclusive
        print(" x: PH range is = " + str(PHangle))                              # log tracker
        print(" y: TH range is = " + str(THangle))                              # log tracker

        heatmapPH = [np.nan for x in PHangle]                                   # Initialize heatmap array with all point = NaN
        heatmapTH = [np.nan for x in THangle]                                   # Initialize heatmap array with all point = NaN

        print("TH alignment sweep")

        i = 0
        print("Moving to PH=%0.3f" % phi0)
        phi = [phi0, phi0]                                                      # THsweep with PH=[phi0, phi0]
        jump_angle_PH(phi, accuracy)                                            # jump to phi angle

        inst.fix_status()                                                       # check and run calibration, if needed

        for theta in THangle:                                                   # loop for theta motion

            if kbhit():                                                         # check if key pressed
                if check_abort():                                               # check if <ESC> pressed
                    gotoZERO(accuracy)                                          # go to home and abort
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return TH_off, PH_off

            jump_angle_TH(theta, accuracy)                                      # make the move

            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            freqIdx = int(len(val)/2)                                           # choose midpoint index
            # print("%+8.3f, %+8.3f" % (hori, val[freqIdx]))

            heatmapTH[i] = val[freqIdx]                                         # append heatmap with actual captured val
            i += 1                                                              # update counter

            if theta == THangle[-1]:
                jump_angle_sph(0, [0, 0], accuracy)                             # go to (0,[0,0]) after last point

            if plot == 1:
                blocking = 0                                                    # set interactive (non-blocking) plot
                display_hvplot(PHangle,THangle,heatmapPH,heatmapTH,blocking,plot_freq=freq[freqIdx],
                               legend=['TH sweep','PH sweep'])                  # update the line plot after each data point

        heatmap = np.array(heatmapTH)*1.0
        heatmap_rel = heatmap - heatmap.max()                                   # compute power relative to peak
        heatmap_mass = 10**(heatmap_rel/5.0)                                    # empirically use 10^(P_rel/5.0)

        TH_off = center_of_mass(THangle, heatmap_mass)                          # calculate center of mass
        print("TH center = %0.3f" % TH_off)

        print("PH alignment sweep")

        i = 0
        print("Moving to TH=%0.3f" % TH_off)
        theta = TH_off                                                          # PHsweep with theta=TH_off
        jump_angle_TH(theta, accuracy)                                          # jump to theta angle

        inst.fix_status()                                                       # check and run calibration, if needed

        for phi in PHangle:                                                     # loop for vertical motion

            if kbhit():                                                         # check if key pressed
                if check_abort():                                               # check if <ESC> pressed
                    gotoZERO(accuracy)                                          # go to home and abort
                    if six.PY2:
                        plt.close('all')                                        # automatically close plot for Py2.x
                    else:
                        print("-----------CLOSE PLOT GRAPHIC TO RETURN TO MENU-----------------")
                        plt.ioff()
                        plt.show(block=True)                                    # manually close plot for Py3.x
                    return TH_off, PH_off

            jump_angle_PH([phi, phi], accuracy)                                 # make the move

            val, freq = get_power(inst)                                         # #####################  this is where you get the value from measurement ####################

            freqIdx = int(len(val)/2)                                           # choose midpoint index
            # print("%+8.3f, %+8.3f" % (vert,val[freqIdx]))

            heatmapPH[i] = val[freqIdx]                                         # append heatmap with actual captured val
            i += 1                                                              # update counter

            if phi == PHangle[-1]:                                              # last point
                try:
                    inst.cont_trigger()                                         # enable cont_trigger if it has been implemented
                except:
                    pass
                jump_angle_sph(0, [0, 0], accuracy)                             # go to (0,[0,0]) after last point
                t1 = time.time()
                print("*** Elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1-t0))))  # display elapsed time
            if plot == 1:
                blocking = 0                                                    # set interactive (non-blocking) plot
                block_final = False
                display_hvplot(PHangle,THangle,heatmapPH,heatmapTH,blocking,plot_freq=freq[freqIdx],block_final=block_final,
                               legend=['TH sweep','PH sweep'])                  # update the line plot after each data point

        heatmap = np.array(heatmapPH)*1.0
        heatmap_rel = heatmap - heatmap.max()                                   # compute power relative to peak
        heatmap_mass = 10**(heatmap_rel/5.0)                                    # empirically use 10^(P_rel/5.0)

        phi = center_of_mass(PHangle, heatmap_mass)                             # calculate center of mass
        print("PH center = %0.3f" % phi)

        PH_off = [phi, phi]
        jump_angle_PH(PH_off, accuracy)                                         # jump to PH_off angle

        if plot == 1:
            blocking = 1
            block_final = keepplot                                              # only block last point if final pass
            display_hvplot(PHangle,THangle,heatmapPH,heatmapTH,blocking,plot_freq=freq[freqIdx],block_final=block_final,
                           legend=['TH sweep','PH sweep'])                      # re-plot data as blocking

        jump_angle_TH(TH_off, accuracy)                                         # jump to TH_off angle
        jump_angle_PH(PH_off, accuracy)                                         # jump to PH_off angle

    else:
        print("ERROR: Incorrect gimbal type. Cannot run SPHERICAL electronic alignment")

    return TH_off, PH_off


def beam_align_sph(inst, accuracy="VERY HIGH"):
    """ 2-pass electronic alignment of beam peak of Spherical Gimbal """

    TH1 = None
    PH1 = None

    if gim_type == SPHERICAL:
        # t0 = time.time()                                                        # get the start time for routine

        print("Coarse alignment search")                                        # coarse search with -90 90 -90 90 5
        TH0, PH0 = beam_align_sph_single(inst, -90, 90, -90, 90, 5, phi0=0.0, accuracy=accuracy, keepplot=False)
        if TH0 is None or PH0 is None:
            return TH1, PH1
        print("Coarse alignment center (TH,PH,DPH) = (%0.3f, %0.3f, %0.3f)" % (TH0, PH0[0], PH0[1]))

        print("Fine alignment search")                                          # fine alignment search with +/-40 from (TH0,PH0)
        TH0x = np.round(TH0, 0)
        PH0x = [np.round(PH0[0], 0), np.round(PH0[1], 0)]
        TH1, PH1 = beam_align_sph_single(inst, TH0x-40, TH0x+40, PH0x[0]-40, PH0x[0]+40, 1, phi0=PH0[0], accuracy=accuracy, keepplot=True)
        if TH1 is None or PH1 is None:
            return TH1, PH1

        jump_angle_TH(TH1, accuracy)                                            # move to found center (TH1,PH1)
        jump_angle_PH(PH1, accuracy)

        # t1 = time.time()
        # print("*** Total elapsed time = %s ***" % (datetime.timedelta(seconds=int(t1 - t0))))     # display elapsed time

        print("")
        print("")
        print("******************************************")
        print("**** ELECTRONIC BEAM ALIGNMENT RESULT ****")
        print("******************************************")
        print("")
        print("   (TH,PH,DPH) = (%0.3f, %0.3f, %0.3f)" % (TH1, PH1[0], PH1[1]))
        print("")

    return TH1, PH1

