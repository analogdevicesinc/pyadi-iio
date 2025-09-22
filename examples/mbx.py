#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Copyright 2018-2022 MILLIWAVE SILICON SOLUTIONS, inc.j


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


# Author: Jeanmarc Laurent, Chinh Doan - Milliwave Silicon Solutions


from __future__ import division                             # division compatibility Python 2.7 and Python 3.6+
import sys
import six
if sys.platform == "win32":                                 # if we run windows, we can use getch from OS
    from msvcrt import getch
else:                                                       # but if we use MACos or Linux we need to create getch()
    def getch():
        x = six.moves.input()
        if len(x) > 1:
            x = chr(0)
            print("too long")
        elif len(x) == 0:
            x = chr(13)     # enter
            print("enter")
        return x
from mbx_functions import *
from mbx_plot import *
import mbx_instrument as equipk
import mbx_test_config as config
import pickle
import os


BAUDRATE                    = 57600                     # for windows and Linux set to 1000000 for MacOS change BAUDRATE to 57600 and set the motor baudrate accordingly
DEVICENAME                  = "/dev/ttyUSB0" \
""                        # Check which port is being used on your controller
                                                            # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"
MAN_STEP                    = 11.25                         # Initial step size used during manual alignment 128*(360/4096)
ACCURACY                    = "HIGH"                        # set to STANDARD, HIGH, or VERY HIGH for gimbal positional accuracy
ZIGZAG                      = True                          # set to True to enable zigzag movement mode for 2D sweeps
DISPLAY_TEST_MENU           = False                         # set to True to display special TEST menu
RELEASE_VER                 = 22.0                          # software release version


print("")
print("MilliBox Software Release: %0.1f" % (RELEASE_VER))   # display SW release version
print("Python Version: " + sys.version)                     # display Python version

if connect(DEVICENAME, BAUDRATE):                           # initiate connection with motors, check communication and register settings
    print("Device connected")
    set_velocity()                                          # initialize velocity using default (max) on all motors
else:
    print("Press any key to terminate...")                  # terminate if error communicating with motor
    getch()
    quit()

gim_type = get_gimtype()                                    # get gimbal type - HV or SPHERICAL
print ("GIM TYPE = " +str(gim_type))
num_motors = get_nummotors()                                # get number of motors
wait_stop_moving(ACCURACY)
print("Found %d motor(s)" % num_motors)
print("Gimbal accuracy setting = %s" % ACCURACY)

print("++++++++++++++++ MilliBox Gimbal is ready  +++++++++++++++")
print("")

# load instrument setup information from previous run
meas_fname = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meas_setup")     # look for meas_setup in cwd
if not os.path.isfile(meas_fname):
    meas_mode = "NONE"                                      # if meas_setup file does not exist, default to NONE / SIMULATION
    addr = ["SIMULATION"]                                   # addr is list of VISA addresses
    data = (meas_mode, addr)
    fileObject = open(meas_fname, 'wb')
    pickle.dump(data, fileObject)                           # store the tuple in the file
    fileObject.close()                                      # close the file
    print("measurement mode saved to file")                 # use previous measurement mode on next run
else:
    data = pickle.load(open(meas_fname, "rb"))              # load the previous measurement mode and addr
    if isinstance(data, tuple):                             # check if data is a tuple
        meas_mode = data[0]
        addr = data[1]                                      # addr is list of VISA addresses
    else:
        meas_mode = "NONE"
        addr = ["SIMULATION"]jump_angle

# initalize VISA instrument control or set to use SIMULATION mode
inst = equip.inst_setup(meas_mode, addr)
inst.init_meas()

print("\n\n******* Measurement Mode = %s *******" % meas_mode)

while True:
    if gim_type == HV:                                      # get current position (H, V, P)
        ang1 = convertpostoangle(H, current_pos(H, 1))
        ang2 = convertpostoangle(V, current_pos(V, 1))
        ang3 = convertpostoangle(P, current_pos(P, 1))
    elif gim_type == SPHERICAL:                             # get current position (TH, PH, DPH)
        ang1 = convertpostoangle(TH, current_pos(TH, 1))
        ang2, ang3 = convertpostoangle(PH, current_pos(PH, 1))
    print("")
    print("**************************************************")
    print("*")
    print("*       Mode: %s" % meas_mode)
    print("* Instrument: %s" % inst.addr)
    print("*   Accuracy: %s" % ACCURACY)
    print("*     Zigzag: %s" % ZIGZAG)
    if num_motors >= 4:
        print("*   Position: (%0.2f, %0.2f, %0.2f)" % (ang1, ang2, ang3))
    elif num_motors >= 2:
        print("*   Position: (%0.2f, %0.2f)" % (ang1, ang2))
    else:
        print("*   Position: (%0.2f)" % ang1)
    print("*")
    print("************* MAIN MENU **************************")
    print("************ USE KEYBOARD ************************")
    print("* Press <ESC> or <q> to close ports and quit!")

    if gim_type == HV:
        if num_motors >= 2:
            print("* use <arrow keys> or <ijkl> to adjust H and V angles")
        else:
            print("* use <arrow keys> or <jl> to adjust H angle")
        if num_motors >= 4:
            print("* use <[> or <]> to adjust polarization angle")
        print("* use <a> to reduce step size for finer alignment resolution")
        print("* use <s> to increase step size for coarser alignment resolution")
        if num_motors >= 4:
            print("* press <ENTER> key to store H0 V0 P0 position")
            print("* press <h> to go home to last saved H0 V0 P0 home position")
        elif num_motors >= 2:
            print("* press <ENTER> key to store H0 V0 position")
            print("* press <h> to go home to last saved H0 V0 home position")
        else:
            print("* press <ENTER> key to store H0 position")
            print("* press <h> to go home to last saved H0 home position")
        print("* press <g> to print current position")
        if num_motors >= 2:
            print("* press <d> to start default plot H -90 90 V -90 90 Step 15deg ")     # 2D sweep for GIM01 or GIM03 or GIM04
        else:
            print("* press <d> to start default plot H -180 180 Step 10deg")             # single axis sweep for GIM1D

    elif gim_type == SPHERICAL:
        if num_motors >= 6:
            print("* use <arrow keys> or <ijkl> to adjust THETA and PHI angles")
            print("* use <[> or <]> to adjust DELTA_PHI angle")
            print("* use <{> or <}> to adjust T MOTOR angle ONLY")
        print("* use <a> to reduce step size for finer alignment resolution")
        print("* use <s> to increase step size for coarser alignment resolution")
        if num_motors >= 6:
            print("* press <ENTER> key to store TH0 PH0 DPH0 position")
            print("* press <h> to go home to last saved TH0 PH0 DPH0 home position")
        print("* press <g> to print current position")
        if num_motors >= 6:
            print("* press <d> to start default plot TH 0 90 PH -180 180 Step 10deg ")  # 2D spherical sweep for GIM05

    print("* press <e> to cycle through accuracy setting")
    print("* press <c> to start accuracy position check menu ")
    print("* press <r> to test motor register configuration ")
    print("* press <v> to open the velocity setting menu")
    print("* press <m> to open the direct move travel menu")
    print("* press <b> to change motor baudrate configuration ")
    print("* press <w> to reset offset for home position ")
    print("* press <y> to set measurement mode (VNA/SG+SA/SA/NONE) and set equipment VISA address")
    print("* press <f> to force instrument re-initialization")
    print("* press <x> to get current power measurement")
    print("* press <p> to plot from file")
    print("* press <z> to toggle zigzag movement mode for 2D sweeps")
    print("* press <t> to start electronic beam alignment")
    print("* press <1> to start a 1-D sweep")
    if num_motors >= 2:                                                         # 2D sweep options available for all but GIM1D
        print("* press <2> to start a 2-D sweep")
        print("* press <3> to start a 1-D sweep in E-plane and H-plane")
    print("*********************************************************")

    if DISPLAY_TEST_MENU:
        if gim_type == HV:
            print("**********************  TEST MENU  **********************")
            print("* press <Shift-1> to show Gimbal platform")
            print("* press <Shift-2> to test Gimbal full range of motion")
            if num_motors >= 2:
                print("* press <Shift-3> to run a full Gimbal sweep H -180 180 V -180 180 Step 20deg")  # full 2D sweep for GIM01 or GIM03
            else:
                print("* press <Shift-3> to run a full Gimbal sweep H -180 180 Step 5deg")              # full single axis sweep for GIM1D
            if num_motors >= 4:
                print("* press <Shift-4> to test range of X-pol")               # X-pol rotation for GIM04x
            if num_motors >= 2:
                print("* press <Shift-5> to run Gimbal sweep H -40 40 V -40 40 Step 5deg - 2D heatmap plot")
            else:
                print("* press <Shift-5> to run Gimbal sweep H -40 40 Step 1deg")
            print("* press <Shift-6> to run CSV-file defined pattern sweep")
            print("*********************************************************")

        if gim_type == SPHERICAL:
            print("**********************  TEST MENU  **********************")
            print("* press <Shift-1> to show Gimbal platform")
            print("* press <Shift-2> to test Gimbal full range of motion")
            if num_motors >= 6:
                print("* press <Shift-3> to run a full Gimbal sweep TH -180 180 PH -180 180 Step 20deg")    # full 2D sweep for GIM05
            if num_motors >= 6:
                print("* press <Shift-4> to GIM05 motion loop")                 # Phi rotation for GIM05
            print("* press <Shift-5> to run Gimbal sweep TH 0 40 PH -180 180 Step 10deg - 2D heatmap plot")
            print("* press <Shift-6> to run CSV-file defined pattern sweep")
            print("*********************************************************")

    pressedkey = ord(getch())

    if pressedkey == 224:                                                       # check for arrow keys
        nextkey = ord(getch())
        if nextkey == 72:                                                       # up -> map to "i" for vertical up move
            pressedkey = ord("i")
        elif nextkey == 80:                                                     # down -> map to "k" for vertical down move
            pressedkey = ord("k")
        elif nextkey == 75:                                                     # left -> map to "j" for horizontal left move
            pressedkey = ord("j")
        elif nextkey == 77:                                                     # right -> map to "l" for horizontal right move
            pressedkey = ord("l")

    if pressedkey == ord("i"):                                                  # "i": vertical/phi up move
        if gim_type == HV:
            if num_motors >= 2:
                print("up")
                move(V, MAN_STEP, ACCURACY)
        if gim_type == SPHERICAL:
            if num_motors >= 6:
                print("phi up")
                move_sph(PH, MAN_STEP, ACCURACY)

    elif pressedkey == ord("k"):                                                # "k": vertical/phi down move
        if gim_type == HV:
            if num_motors >= 2:
                print("down")
                move(V, MAN_STEP * -1, ACCURACY)
        if gim_type == SPHERICAL:
            if num_motors >= 6:
                print("phi down")
                move_sph(PH, MAN_STEP * -1, ACCURACY)

    elif pressedkey == ord("j"):                                                # "j": horizontal/theta left move
        if gim_type == HV:
            print("left")
            move(H, MAN_STEP * -1, ACCURACY)
        if gim_type == SPHERICAL:
            print("theta down")
            move_sph(TH, MAN_STEP * -1, ACCURACY)

    elif pressedkey == ord("l"):                                                # "l": horizontal/theta right move
        if gim_type == HV:
            print("right")
            move(H, MAN_STEP, ACCURACY)
        if gim_type == SPHERICAL:
            print("theta up")
            move_sph(TH, MAN_STEP, ACCURACY)

    elif pressedkey == ord("["):                                                # "[": polarization/delta_phi left
        if gim_type == HV:
            if num_motors >= 4:
                print("polarization left")
                move(P, MAN_STEP*-1, ACCURACY)
        if gim_type == SPHERICAL:
            if num_motors >= 6:
                print("delta_phi down")
                move_sph(DPH, MAN_STEP*-1, ACCURACY)

    elif pressedkey == ord("]"):                                                # "]": polarization/delta_phi right
        if gim_type == HV:
            if num_motors >= 4:
                print("polarization right")
                move(P, MAN_STEP, ACCURACY)
        if gim_type == SPHERICAL:
            if num_motors >= 6:
                print("delta_phi up")
                move_sph(DPH, MAN_STEP, ACCURACY)

    elif pressedkey == ord("{"):                                                # "{": T MOTOR left
        if gim_type == SPHERICAL:
            if num_motors >= 6:
                print("T MOTOR down")
                move_sph(T, MAN_STEP*-1, ACCURACY)

    elif pressedkey == ord("}"):                                                # "}": T motor right
        if gim_type == SPHERICAL:
            if num_motors >= 6:
                print("T MOTOR up")
                move_sph(T, MAN_STEP, ACCURACY)

    elif pressedkey == 27 or pressedkey == ord("q"):                            # esc or "q": close port
        gotoZERO(ACCURACY)                                                      # park Gimbal home upon exiting controller

        print("")
        print("Disable TORQUE on motors? [Y/N]")
        key = None                                                              # ask to disable torque on motors at close
        while key not in ['Y', 'N']:
            key = chr(ord(getch().upper()))
            if key == 'Y':
                print("disabling torque on all motors")
                disable_torque(H)
                if gim_type == HV:
                    if num_motors >= 2:
                        disable_torque(V)
                    # if num_motors >= 3:
                    #     disable_torque(R)
                    if num_motors >= 4:
                        disable_torque(P)
                if gim_type == SPHERICAL:
                    if num_motors >= 5:
                        disable_torque(T)
                    if num_motors >= 6:
                        disable_torque(Z)

        print("")
        print("exit called bye bye!")
        inst.close_instrument()                                                 # close all instruments
        exit()

    elif pressedkey == ord("r"):                                                # r: register test program
        print(" check and program gimbal registers")
        test()

    elif pressedkey == ord("h"):                                                # h: go home
        print("0")
        print("go to 0 position")                                               # move to (0,0,0) and prints move time
        if gim_type == HV:
            gim_move(0, 0, 0, ACCURACY)
        elif gim_type == SPHERICAL:
            gim_move_sph(0, [0, 0], ACCURACY)

    elif pressedkey == ord("a"):                                                # a: reduce step size by half
        print("a")
        MAN_STEP = MAN_STEP/2
        print("step size is now: " +str(MAN_STEP))

    elif pressedkey == ord("s"):                                                # s: increase step size by two
        print("s")
        MAN_STEP = MAN_STEP*2
        print("step size is now: " +str(MAN_STEP))

    elif pressedkey == ord("e"):                                                # e: cycle through accuracy setting
        print("e")
        if ACCURACY == "HIGH":
            ACCURACY = "VERY HIGH"
        elif ACCURACY == "VERY HIGH":
            ACCURACY = "HIGH"
        print("Gimbal accuracy setting = %s" % ACCURACY)

    elif pressedkey == ord("z"):                                                # z: toggle zigzag movement mode
        print("z")
        ZIGZAG = not ZIGZAG
        print("Zigzag movement mode = %s" % ZIGZAG)

    elif pressedkey == ord("v"):                                                # v: set velocity
        print("this menu sets rotation velocity")                               # initiates velocity menu
        get_velocity()                                                          # print current velocity settings
        if gim_type == HV:
            H_VEL = float(input_num("Enter your desired rotation velocity for H in RPM (enter 0 for default): "))
            if num_motors >= 2:
                V_VEL = float(input_num("Enter your desired rotation velocity for V in RPM: (enter 0 for default): "))
            else:
                V_VEL = 0
            if num_motors >= 4:
                P_VEL = float(input_num("Enter your desired rotation velocity for P in RPM: (enter 0 for default): "))
            else:
                P_VEL = 0
            set_velocity(H_VEL, V_VEL, P_VEL)

        if gim_type == SPHERICAL:
            H_VEL = float(input_num("Enter your desired rotation velocity for H in RPM (enter 0 for default): "))
            if num_motors >= 5:
                T_VEL = float(input_num("Enter your desired rotation velocity for T in RPM: (enter 0 for default): "))
            else:
                T_VEL = 0
            if num_motors >= 6:
                Z_VEL = float(input_num("Enter your desired rotation velocity for Z in RPM: (enter 0 for default): "))
            else:
                Z_VEL = 0
            set_velocity(H_VEL, T_VEL, Z_VEL)

    elif pressedkey == ord("m"):                                                # m: direct move menu
        if gim_type == HV:
            H_TARGET = float(input_num("Enter targeted angle in horizontal plane in degree: "))
            if num_motors >= 2:
                V_TARGET = float(input_num("Enter targeted angle in vertical plane in degree: "))
            else:
                V_TARGET = None
            if num_motors >= 4:
                P_TARGET = float(input_num("Enter targeted angle in polarization plane in degree: "))
            else:
                P_TARGET = None

            if check_move(H_TARGET, V_TARGET, P_TARGET) == 1:
                print("## Please make sure everything is ready to start measurement ##")  # warning
                print("#####      Automatic motion of MilliBox will start!!       ####")
                print("##   Press SPACE BAR when all is ready to start plotting     ##")
                if sys.platform == "win32":                                     # if we run windows, we can abort with <ESC>
                    print("##   Press ESC to abort                                      ##")
                key = None
                while key != 32 and key != 27:                                  # wait for space bar
                    key = ord(getch())
                    if key == 32:
                        gim_move(H_TARGET, V_TARGET, P_TARGET, ACCURACY)        # make the move

        if gim_type == SPHERICAL:
            THETA_TARGET = float(input_num("Enter targeted angle in THETA in degree: "))
            if num_motors >= 5:
                PHI_TARGET = float(input_num("Enter targeted angle in PHI in degree: "))
            else:
                PHI_TARGET = None
            if num_motors >= 6:
                DPHI_TARGET = float(input_num("Enter targeted angle in DELTA_PHI in degree: "))
            else:
                DPHI_TARGET = None

            if check_move_sph(THETA_TARGET, [PHI_TARGET, DPHI_TARGET]) == 1:
                print("## Please make sure everything is ready to start measurement ##")  # warning
                print("#####      Automatic motion of MilliBox will start!!       ####")
                print("##   Press SPACE BAR when all is ready to start plotting     ##")
                if sys.platform == "win32":  # if we run windows, we can abort with <ESC>
                    print("##   Press ESC to abort                                      ##")
                key = None
                while key != 32 and key != 27:                                  # wait for space bar
                    key = ord(getch())
                    if key == 32:
                        gim_move_sph(THETA_TARGET, [PHI_TARGET, DPHI_TARGET], ACCURACY)  # make the move

    elif pressedkey == ord("d"):                                                # d: run default plot
        print("d")
        gotoZERO(ACCURACY)                                                      # make sure millibox is reset to (0,0)
        print("## Please make sure everything is ready to start measurement ##")# warning
        print("#####      Automatic motion of MilliBox will start!!       ####")
        print("##   Press SPACE BAR when all is ready to start plotting     ##")
        if sys.platform == "win32":                                             # if we run windows, we can abort with <ESC>
            print("##   Press ESC to abort                                      ##")
        key = None                                                              # block on space bar
        while key != 32 and key != 27:
            key = ord(getch())
            if key == 32:
                if gim_type == HV:
                    if num_motors >= 4:
                        millibox_2dsweep(-90, 90, -90, 90, 15, 0, 1, 'default', inst, ACCURACY, zigzag=ZIGZAG)      # start default 2d sweep
                    elif num_motors >= 2:
                        millibox_2dsweep(-90, 90, -90, 90, 15, None, 1, 'default', inst, ACCURACY, zigzag=ZIGZAG)   # start default 2d sweep
                    else:
                        millibox_1dsweep('H', -180, 180, 0, 0, 10, None, 1, 'default', inst, ACCURACY)              # start default 1d sweep
                elif gim_type == SPHERICAL:
                    if num_motors >= 6:
                        millibox_2dsweep_sph(0, 90, -180, 180, 10, 0, 1, 'default', inst, ACCURACY, zigzag=ZIGZAG)  # start default 2d sweep

    elif pressedkey == ord("w"):                                                # w: reset the offset for home position.
        print(" WARNING you need to have the gimbal close to its home position to proceed")
        print("press any key to go back to main menu and SPACE BAR to proceed with Offset reset")
        key = ord(getch())
        if key == 32:
            resetoffset()
        else:
            print("back top menu")

    elif pressedkey == ord("b"):                                                # b: change baudrate
        print("### This menu changes the motor communication baudrate ####")
        print("### proceed with caution as you may loose communication with motors ####")
        print("### the baudrate set in the motors and the baudrate in mbx.py global settings have to match ####")
        BRATE = int(input_num("Enter (1) for 57600 kbps, enter (3) for 1 MBps, any other number to exit: "))
        if (BRATE == 1) or (BRATE == 3):
            changerate(BRATE)

    elif pressedkey == ord("g"):                                                # g: get motors current position
        print("g")
        getposition()

    elif pressedkey == 13:                                                      # ENTER: write current position as home position
        setoffset_all()
        gotoZERO(ACCURACY)
        print("this position is now HOME position")

    elif pressedkey == ord("y"):                                                # list and select VISA instrument
        (meas_mode, inst) = visa(meas_mode, inst)
        fileObject = open(meas_fname, 'wb')
        data = (meas_mode, inst.addr)
        pickle.dump(data, fileObject)                                           # store the value in the file
        fileObject.close()                                                      # close the file
        print("measurement mode and equipment saved to file")                   # use measurement mode on next run

    elif pressedkey == ord("f"):                                                # force instrument re-initialization
        print("\nresetting instruments\n")
        if inst.port_open:
            inst.init_meas()

    elif pressedkey == ord("x"):                                                # readback motor position and power level
        print("x")
        wait_stop_moving(ACCURACY)

        if gim_type == HV:
            if num_motors >= 4:
                print("power at (H,V,P) = (%0.1f,%0.1f,%0.1f):" % (convertpostoangle(H,current_pos(H,1)),convertpostoangle(V,current_pos(V,1)),convertpostoangle(P,current_pos(P,1))))
            elif num_motors >= 2:
                print("power at (H,V) = (%0.1f,%0.1f):" % (convertpostoangle(H,current_pos(H,1)),convertpostoangle(V,current_pos(V,1))))
            else:
                print("power at (H) = (%0.1f):" % (convertpostoangle(H,current_pos(H,1))))
        elif gim_type == SPHERICAL:
            if num_motors >= 6:
                th = convertpostoangle(TH,current_pos(TH,1))
                ph,dphi = convertpostoangle(PH,current_pos(PH,1))
                print("power at (TH,PH,DPH) = (%0.1f,%0.1f,%0.1f):" % (th,ph,dphi))

        val, freq = get_power(inst)
        for i in range(len(val)):
            print("%7.2fGHz : %7.2f" % (freq[i]/1e9,val[i]))

        try:
            inst.cont_trigger()                                                 # set to cont sweep after power measurement
        except:
            pass

    elif pressedkey == ord("p"):                                                # plot from file
        print("p")
        mbx_plot(DISPLAY_TEST_MENU)

    elif pressedkey == ord("t"):                                                # beam alignment
        print("t")
        print("##                 ELECTRONIC BEAM ALIGNMENT                 ##")# warning
        print("##                 -------------------------                 ##")# warning
        print("## Please make sure everything is ready to start measurement ##")# warning
        print("#####      Automatic motion of MilliBox will start!!       ####")
        print("##   Press SPACE BAR when all is ready to start plotting     ##")
        if sys.platform == "win32":                                             # if we run windows, we can abort with <ESC>
            print("##   Press ESC to abort                                      ##")
        key = None                                                              # block on space bar
        while key != 32 and key != 27:
            key = ord(getch())
            if key == 32:
                if gim_type == HV:
                    x1, x2 = beam_align_hv(inst, 0, ACCURACY)
                elif gim_type == SPHERICAL:
                    x1, x2 = beam_align_sph(inst, ACCURACY)

        if x1 is not None and x2 is not None:                                   # if valid return values (alignment was not aborted)
            print("Save position as new HOME? [Y/N]")
            key = None                                                          # ask if user wants to commit position as home
            while key not in ['Y', 'N']:
                key = chr(ord(getch().upper()))
                if key == 'Y':
                    setoffset_all()
                    gotoZERO(ACCURACY)
                    print("this position is now HOME position")

    elif pressedkey == ord("1"):                                                # 1: start 1-D sweep menu
        gotoZERO(ACCURACY)
        print("\n\n************ 1-D Single Direction Sweep ************\n")
        print("Plot display options:")
        print("  0 - no interactive plot")                                      # no graphic - save data to CSV file only
        print("  1 - interactive plot")                                         # line plot
        print("")
        PLOT = -1
        while PLOT not in [0,1]:
            PLOT = int(input_num("Select the plot display option: "))
        print("")

        if gim_type == HV:
            MINH = MAXH = MINV = MAXV = POLA = 0
            STEP = 10
            DIR = 'H'
            while check_plot_1d(DIR, MINH, MAXH, MINV, MAXV, STEP, POLA) == 0:      # loop until valid data is entered
                if num_motors >= 2:
                    print("<H>orizontal or <V>ertical sweep?")
                    DIR = None
                    while DIR not in ['H', 'V']:
                        DIR = chr(ord(getch().upper()))
                else:
                    DIR = "H"
                if DIR == "H":
                    if num_motors >= 2:
                        MINV = float(input_num("Enter your FIXED angle in vertical plane in degree: "))
                    else:
                        MINV = 0.0
                    MAXV = MINV
                    MINH = float(input_num("Enter your start angle in horizontal plane in degree: "))
                    MAXH = float(input_num("Enter your last angle in horizontal plane in degree: "))
                    STEP = float(input_num("Enter your step size in degree : "))          # capture user entries for H sweep
                    if num_motors >= 4:
                        POLA = float(input_num("Enter your polarization position in degree : "))
                    else:
                        POLA = None
                elif DIR == "V":
                    MINH = float(input_num("Enter your FIXED angle in horizontal plane in degree: "))
                    MAXH = MINH
                    MINV = float(input_num("Enter your start angle in vertical plane in degree: "))
                    MAXV = float(input_num("Enter your last angle in vertical plane in degree: "))
                    STEP = float(input_num("Enter your step size in degree : "))          # capture user entries for V sweep
                    if num_motors >= 4:
                        POLA = float(input_num("Enter your polarization position in degree : "))
                    else:
                        POLA = None
                if check_plot_1d(DIR, MINH, MAXH, MINV, MAXV, STEP, POLA) == 0:
                    print("\n\n#####################################################################")
                    print("##    ERROR :  THOSE VALUES CAN'T PLOT, Please try other values    ##")
                    print("#####################################################################\n\n")

            print("")
            tag = six.moves.input("Enter a tag to append to filename or [ENTER] for no tag: ")
            print("")
            config.millibox_1dsweep_wrapper(DIR, MINH, MAXH, MINV, MAXV, STEP, POLA, PLOT, tag, inst, ACCURACY)     # start plot with user inputs

        elif gim_type == SPHERICAL:
            MINTH = MAXTH = MINPH = MAXPH = DPHI = 0
            STEP = 10
            DIR = 'T'
            while check_plot_1d_sph(DIR, MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI) == 0:  # loop until valid data is entered
                if num_motors >= 5:
                    print("<T>heta or <P>hi sweep?")
                    DIR = None
                    while DIR not in ['T', 'P']:
                        DIR = chr(ord(getch().upper()))
                else:
                    DIR = "T"
                if DIR == "T":
                    if num_motors >= 5:
                        MINPH = float(input_num("Enter your FIXED angle for PHI in degree: "))
                    else:
                        MINPH = 0.0
                    MAXPH = MINPH
                    MINTH = float(input_num("Enter your start angle in THETA in degree: "))
                    MAXTH = float(input_num("Enter your last angle in THETA in degree: "))
                    STEP = float(input_num("Enter your step size in degree : "))  # capture user entries for H sweep
                    if num_motors >= 6:
                        DPHI = float(input_num("Enter your DELTA_PHI in degree : "))
                    else:
                        DPHI = None
                elif DIR == "P":
                    MINTH = float(input_num("Enter your FIXED angle in THETA in degree: "))
                    MAXTH = MINTH
                    MINPH = float(input_num("Enter your start angle in PHI in degree: "))
                    MAXPH = float(input_num("Enter your last angle in PHI in degree: "))
                    STEP = float(input_num("Enter your step size in degree : "))  # capture user entries for V sweep
                    if num_motors >= 6:
                        DPHI = float(input_num("Enter your DELTA_PHI in degree : "))
                    else:
                        DPHI = None
                if check_plot_1d_sph(DIR, MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI) == 0:
                    print("\n\n#####################################################################")
                    print("##    ERROR :  THOSE VALUES CAN'T PLOT, Please try other values    ##")
                    print("#####################################################################\n\n")

            print("")
            tag = six.moves.input("Enter a tag to append to filename or [ENTER] for no tag: ")
            print("")
            config.millibox_1dsweep_wrapper_sph(DIR, MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI, PLOT, tag, inst, ACCURACY)   # start plot with user inputs

    elif (pressedkey == ord("2")) and num_motors >= 2:                          # 2: start 2-D sweep menu
        if gim_type == HV:
            gotoZERO(ACCURACY)
            print("This is your zero position: center of the plot")
            print("\n\n************ 2-Axis Sweep ************\n")
            print("Plot display options:")
            print("  0 - no interactive plot display")                              # no graphic - save data to CSV file only
            print("  1 - 3d surface plot")                                          # 3D surface plot + 3D radiation pattern
            print("  2 - 2d heatmap plot")                                          # 2D heatmap plot + 3D radiation pattern
            print("  3 - multi-trace line plot")                                    # multi-trace line plot + 3D radiation pattern
            print("  4 - 3d radiation pattern ONLY")                                # 3D radiation pattern only
            print("")
            PLOT = -1
            while PLOT not in [0,1,2,3,4]:
                PLOT = int(input_num("Select the plot display option: "))
            print("")

            MINH = MAXH = MINV = MAXV = POLA = 0
            STEP = 10
            while check_plot(MINH, MAXH, MINV, MAXV, STEP, POLA) == 0:              # loop until valid data is entered
                MINH = float(input_num("Enter your start angle in horizontal plane in degree: "))
                MAXH = float(input_num("Enter your last angle in horizontal plane in degree: "))
                MINV = float(input_num("Enter your start angle in vertical plane in degree: "))
                MAXV = float(input_num("Enter your last angle in vertical plane in degree: "))
                STEP = float(input_num("Enter your step size in degree : "))              # capture user entries
                if num_motors >= 4:
                    POLA = float(input_num("Enter your polarization position in degree : "))
                else:
                    POLA = None

                if check_plot(MINH, MAXH, MINV, MAXV, STEP, POLA) == 0:
                    print("\n\n#####################################################################")
                    print("##    ERROR :  THOSE VALUES CAN'T PLOT, Please try other values    ##")
                    print("#####################################################################\n\n")

            print("")
            tag = six.moves.input("Enter a tag to append to filename or [ENTER] for no tag: ")
            print("")

            config.millibox_2dsweep_wrapper(MINH, MAXH, MINV, MAXV, STEP, POLA, PLOT, tag, inst, ACCURACY, zigzag=ZIGZAG)  # start plot with user inputs

        elif gim_type == SPHERICAL:
            gotoZERO(ACCURACY)
            print("This is your zero position: center of the plot")
            print("\n\n************ 2-Axis Sweep ************\n")
            print("Plot display options:")
            print("  0 - no interactive plot display")                          # no graphic - save data to CSV file only
            print("  1 - 2d direction cosine plot")                             # 2D direction cosine plot + 3D radiation pattern
            print("  2 - 2d polar spherical plot")                              # 2D polar spherical plot + 3D radiation pattern
            print("  3 - 3d radiation pattern ONLY")                            # 3D radiation pattern only
            print("")
            PLOT = -1
            while PLOT not in [0, 1, 2, 3]:
                PLOT = int(input_num("Select the plot display option: "))
            print("")

            MINTH = MAXTH = MINPH = MAXPH = DPHI = 0
            STEP = 10
            while check_plot_sph(MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI) == 0:  # loop until valid data is entered
                MINTH = float(input_num("Enter your start angle in THETA in degree: "))
                MAXTH = float(input_num("Enter your last angle in THETA in degree: "))
                MINPH = float(input_num("Enter your start angle in PHI in degree: "))
                MAXPH = float(input_num("Enter your last angle in PHI in degree: "))
                STEP = float(input_num("Enter your step size in degree : "))  # capture user entries
                if num_motors >= 6:
                    DPHI = float(input_num("Enter your DELTA_PHI in degree : "))
                else:
                    DPHI = None

                if check_plot_sph(MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI) == 0:
                    print("\n\n#####################################################################")
                    print("##    ERROR :  THOSE VALUES CAN'T PLOT, Please try other values    ##")
                    print("#####################################################################\n\n")

            print("")
            tag = six.moves.input("Enter a tag to append to filename or [ENTER] for no tag: ")
            print("")

            config.millibox_2dsweep_wrapper_sph(MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI, PLOT, tag, inst, ACCURACY, zigzag=ZIGZAG)  # start plot with user inputs

    elif pressedkey == ord("3") and num_motors >= 2:                            # 3: start 1-D plot menu for E- and H-plane
        gotoZERO(ACCURACY)
        print("\n\n************ 1-D Single Direction Sweep in E-plane and H-plane ************\n")
        print("Plot display options:")
        print("  0 - no interactive plot")                                      # no graphic - save data to CSV file only
        print("  1 - interactive plot")                                         # line plot
        print("")
        PLOT = -1
        while PLOT not in [0,1]:
            PLOT = int(input_num("Select the plot display option: "))
        print("")

        if gim_type == HV:
            MIN = MAX = POLA = 0
            STEP = 10
            while check_plot(MIN, MAX, MIN, MAX, STEP, POLA) == 0:
                MIN = float(input_num("Enter your start angle in degree: "))
                MAX = float(input_num("Enter your last angle in degree: "))
                STEP = float(input_num("Enter your step size in degree : "))              # capture user entries
                if num_motors >= 4:
                    POLA = float(input_num("Enter your polarization position in degree : "))
                else:
                    POLA = None
                if check_plot(MIN, MAX, MIN, MAX, STEP, POLA) == 0:
                    print("\n\n#####################################################################")
                    print("##    ERROR :  THOSE VALUES CAN'T PLOT, Please try other values    ##")
                    print("#####################################################################\n\n")

            print("")
            tag = six.moves.input("Enter a tag to append to filename or [ENTER] for no tag: ")
            print("")

            config.millibox_hvsweep_wrapper(MIN, MAX, STEP, POLA, PLOT, tag, inst, ACCURACY)  # start plot with user inputs

        if gim_type == SPHERICAL:
            MIN = MAX = DPHI = 0
            STEP = 10
            while check_plot_sph(MIN, MAX, 0, 90, STEP, DPHI) == 0:
                MIN = float(input_num("Enter your start angle in degree: "))
                MAX = float(input_num("Enter your last angle in degree: "))
                STEP = float(input_num("Enter your step size in degree : "))  # capture user entries
                if num_motors >= 4:
                    DPHI = float(input_num("Enter your DELTA_PHI in degree : "))
                else:
                    DPHI = None
                if check_plot_sph(MIN, MAX, 0, 90, STEP, DPHI) == 0:
                    print("\n\n#####################################################################")
                    print("##    ERROR :  THOSE VALUES CAN'T PLOT, Please try other values    ##")
                    print("#####################################################################\n\n")

            print("")
            tag = six.moves.input("Enter a tag to append to filename or [ENTER] for no tag: ")
            print("")

            config.millibox_hvsweep_wrapper_sph(MIN, MAX, STEP, DPHI, PLOT, tag, inst, ACCURACY)  # start plot with user inputs

    elif pressedkey == ord("c"):                                                # c: start accuracy plot menu
        gotoZERO(ACCURACY)
        print("This is your zero position: center of the plot")
        check_ok = 0
        while check_ok == 0:
            if gim_type == HV:
                MINH = float(input_num("Enter your start angle in horizontal plane in degree: "))
                MAXH = float(input_num("Enter your last angle in horizontal plane in degree: "))
                if num_motors >= 2:
                    MINV = float(input_num("Enter your start angle in vertical plane in degree: "))
                    MAXV = float(input_num("Enter your last angle in vertical plane in degree: "))
                else:
                    MINV = MAXV = 0
                STEP = float(input_num("Enter your step size in degree : "))        # capture user entries
                if num_motors >= 2:
                    check_ok = check_plot(MINH, MAXH, MINV, MAXV, STEP)
                else:
                    check_ok = check_plot_1d('H', MINH, MAXH, MINV, MAXV, STEP)
            elif gim_type == SPHERICAL:
                MINTH = float(input_num("Enter your start angle in THETA in degree: "))
                MAXTH = float(input_num("Enter your last angle in THETA in degree: "))
                MINPH = float(input_num("Enter your start angle in PHI in degree: "))
                MAXPH = float(input_num("Enter your last angle in PHI in degree: "))
                STEP = float(input_num("Enter your step size in degree : "))        # capture user entries
                check_ok = check_plot_sph(MINTH, MAXTH, MINPH, MAXPH, STEP)

            if check_ok == 1:
                print("## Please make sure everything is ready to start measurement ##")# warning
                print("#####      Automatic motion of MilliBox will start!!       ####")
                print("##   Press SPACE BAR when all is ready to start plotting     ##")
                if sys.platform == "win32":                                     # if we run windows, we can abort with <ESC>
                    print("##   Press ESC to abort                                      ##")
                key = None
                while key != 32 and key != 27:                                  # wait for space bar
                    key = ord(getch())
                    if key == 32:
                        if gim_type == HV:
                            milliboxacc(MINH, MAXH, MINV, MAXV, STEP, ACCURACY, zigzag=ZIGZAG)      # start position accuracy check with user inputs
                        elif gim_type == SPHERICAL:
                            milliboxacc_sph(MINTH, MAXTH, MINPH, MAXPH, STEP, ACCURACY, zigzag=ZIGZAG)  # start position accuracy check with user inputs
            else:
                print("\n\n#####################################################################")
                print("##    ERROR :  THOSE VALUES CAN'T PLOT, Please try other values    ##")
                print("#####################################################################\n\n")

    # test modes
    elif pressedkey == ord("!"):                                                # Shift-1: test mode, move to -110deg angle to show platform
        if gim_type == HV:
            jump_angle(-110, 0, 0)
        else:
            jump_angle_sph(-110, [0, 0])
    elif pressedkey == ord("@"):                                                # Shift-2: test mode, demonstrate range of gimbal
        if gim_type == HV:
            gotoZERO()
            jump_angle_H(-180)
            jump_angle_H(180)
            jump_angle_H(0)
            if num_motors >= 2:
                jump_angle_V(-180)
                jump_angle_V(180)
                jump_angle_V(0)
                if num_motors >= 4:
                    jump_angle_P(0)
                    jump_angle_P(-90)
                    jump_angle_P(0)
            gotoZERO()
        elif gim_type == SPHERICAL:
            gotoZERO()
            jump_angle_TH(-180)
            jump_angle_TH(180)
            jump_angle_TH(0)
            if num_motors >= 6:
                jump_angle_PH([-180, 0])
                jump_angle_PH([180, 0])
                jump_angle_PH([0, 0])

                jump_angle_PH([0, -180])
                jump_angle_PH([0, 180])
                jump_angle_PH([0, 0])
            gotoZERO()
    elif pressedkey == ord("#"):                                                # Shift-3: test mode, full sweep -180 180 -180 180 20
        gotoZERO(ACCURACY)                                                      # make sure millibox is reset to (0,0)
        print("## Please make sure everything is ready to start measurement ##")# warning
        print("#####      Automatic motion of MilliBox will start!!       ####")
        print("##   Press SPACE BAR when all is ready to start plotting     ##")
        if sys.platform == "win32":                                             # if we run windows, we can abort with <ESC>
            print("##   Press ESC to abort                                      ##")
        key = None                                                              # block on space bar
        while key != 32 and key != 27:
            key = ord(getch())
            if key == 32:
                if gim_type == HV:
                    if num_motors >= 4:
                        millibox_2dsweep(-180, 180, -180, 180, 20, 0, 1, 'full', inst, ACCURACY, zigzag=ZIGZAG)     # start full 2d sweep
                    elif num_motors >= 2:
                        millibox_2dsweep(-180, 180, -180, 180, 20, None, 1, 'full', inst, ACCURACY, zigzag=ZIGZAG)  # start full 2d sweep
                    else:
                        millibox_1dsweep('H', -180, 180, 0, 0, 5, None, 1, 'full', inst, ACCURACY)    # start full 1d sweep
                elif gim_type == SPHERICAL:
                    if num_motors >= 6:
                        millibox_2dsweep_sph(-180, 180, -180, 180, 20, 0, 2, 'full', inst, ACCURACY, zigzag=ZIGZAG) # start full 2d sweep
    elif pressedkey == ord("$"):                                                # Shift-4: test mode, x-pol demonstration
        if gim_type == HV:
            if num_motors >= 4:
                jump_angle(-60, 0, 0)
                jump_angle_P(0)
                jump_angle_P(-180)                                              # clockwise 180deg rotation
                time.sleep(1)
                jump_angle_P(0)
                time.sleep(1)
                jump_angle_P(-180)                                              # clockwise 180deg rotation
                time.sleep(1)
                jump_angle_P(0)
        elif gim_type == SPHERICAL:                                             # GIM05 motion loop
            if num_motors >= 6:
                jump_angle_sph(90, [90, 0])
                time.sleep(0.1)
                jump_angle_sph(-90, [-90, 0])
                time.sleep(0.1)
                gotoZERO()
    elif pressedkey == ord("%"):                                                # Shift-5: test mode, zoomed in accurate demo
        gotoZERO(ACCURACY)                                                      # make sure millibox is reset to (0,0)
        print("## Please make sure everything is ready to start measurement ##")# warning
        print("#####      Automatic motion of MilliBox will start!!       ####")
        print("##   Press SPACE BAR when all is ready to start plotting     ##")
        if sys.platform == "win32":                                             # if we run windows, we can abort with <ESC>
            print("##   Press ESC to abort                                      ##")
        key = None                                                              # block on space bar
        while key != 32 and key != 27:
            key = ord(getch())
            if key == 32:
                if gim_type == HV:
                    if num_motors >= 4:
                        millibox_2dsweep(-40, 40, -40, 40, 5, 0, 2, 'zoom', inst, ACCURACY, zigzag=ZIGZAG)      # start zoom in accurate sweep, 2D heatmap plot
                    elif num_motors >= 2:
                        millibox_2dsweep(-40, 40, -40, 40, 5, None, 2, 'zoom', inst, ACCURACY, zigzag=ZIGZAG)   # start zoom in accurate sweep, 2D heatmap plot
                    else:
                        millibox_1dsweep('H', -40, 40, 0, 0, 1, None, 1, 'zoom', inst, ACCURACY)                # start zoom in accurate 1d sweep
                elif gim_type == SPHERICAL:
                    if num_motors >= 6:
                        millibox_2dsweep_sph(0, 40, -180, 180, 10, 0, 1, 'zoom', inst, ACCURACY, zigzag=ZIGZAG)     # start zoom in accurate sweep, 2D heatmap plot
    elif pressedkey == ord("^"):                                                # Shift-6: test mode, CSV-file defined pattern
        gotoZERO(ACCURACY)                                                      # make sure millibox is reset to (0,0)
        print("")
        pat_file = six.moves.input("Enter CSV filename with Gimbal coordinates or [ENTER] for default (gimpat.csv): ")
        print("")
        if pat_file == '':
            pat_file = 'gimpat.csv'
        tag = six.moves.input("Enter a tag to append to filename or [ENTER] for no tag: ")
        print("")
        print("## Please make sure everything is ready to start measurement ##")# warning
        print("#####      Automatic motion of MilliBox will start!!       ####")
        print("##   Press SPACE BAR when all is ready to start plotting     ##")
        if sys.platform == "win32":                                             # if we run windows, we can abort with <ESC>
            print("##   Press ESC to abort                                      ##")
        key = None                                                              # block on space bar
        print("")
        while key != 32 and key != 27:
            key = ord(getch())
            if key == 32:
                millibox_pat_sweep(pat_file, tag, inst, ACCURACY)
