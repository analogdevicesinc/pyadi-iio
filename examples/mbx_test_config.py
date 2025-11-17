#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Copyright 2020-2022 MILLIWAVE SILICON SOLUTIONS, inc.

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

# mbx_test_config.py:
# -------------------
# Wrapper functions between mbx.py (main menu) and mbx_functions.py (sweep). Purpose is:
#   - get values for parametric sweeps
#       - fixed frequency - set at a single fixed frequency
#       - frequency sweep - multiple frequencies
#       - repeatability - same measurement N times
#       - delay - add fixed delay (in ms) after movement before measurement
#   - loop over parametric values
#       - call single sweep function
#
# NOTE: This file can act as a purely transparent pass-through if the run-time parameters are not
# needed for the sweeps
#
# Author: Chinh Doan - Milliwave Silicon Solutions


import MantaRayTx_Cal.mbx_functions as mbxf
import numpy as np
import sys
import six
if sys.platform == "win32":                                 # if we run windows, we can use getch from OS
    from msvcrt import getch
else:                                                       # but if we use MACos or Linux we need to create getch()
    def getch():
        x=six.moves.input()
        if len(x) > 1:
            x = chr(0)
            print("too long")
        elif len(x) == 0:
            x = chr(13)     # enter
            print("enter")
        return x


def get_meas_params(inst):
    """ get parametric values for sweeps (if needed)
    e.g., fixed freq, swept freq, repeated measurement, time delay"""

    # set to True to allow for discrete frequency sweeping using spectrum analyzer
    spec_analyzer_freq_sweep = False

    freqList = np.array([28.0e9])                                               # default to 28GHz if simulation mode or no instrument mode
    if inst.inst_type.find("SA") > -1:
        if inst.port_open:                                                      # if connected to an instrument, get freq
            if not spec_analyzer_freq_sweep:
                freq_ghz = inst.get_marker_freq(1) / 1.0e9                      # find current location of marker1
                f = float(mbxf.input_num(("Enter your freq [GHz] [ENTER for %g]: " % freq_ghz), freq_ghz))     # fixed freq measurement with spectrum analyzer
                freqList = np.array([f*1.0e9])
            else:
                min_f = float(mbxf.input_num("Enter your start freq [GHz]: "))  # frequency sweep
                max_f = float(mbxf.input_num("Enter your end freq [GHz]: "))
                step_f = float(mbxf.input_num("Enter your step freq [GHz]: "))
                if max_f > min_f:
                    num = np.floor((max_f - min_f) / step_f)                    # freq sweep if max_f > min_f
                else:
                    num = 0                                                     # fixed freq if max_f <= min_f
                freqList = np.linspace(min_f, min_f + num * step_f, num + 1)    # [min:step:max] with endpoints inclusive
                print("")
    elif inst.inst_type.find("VNA") > -1:
        if inst.port_open:                                                      # if connected to an instrument, get freq
            plot_f = float(mbxf.input_num("Enter the freq [GHz] to plot: "))    # capture all data for VNA, but plot one freq
            freqList = [plot_f*1e9]

    meas_delay = 0                                                              # no delay between gimbal movement and measurement
    # meas_delay = float(mbxf.input_num("Enter delay after movement before measurement [sec]: "))  # uncomment this line to allow user-specified delay
    # print("")

    return freqList, meas_delay


def millibox_1dsweep_wrapper(DIR, MINH, MAXH, MINV, MAXV, STEP, POL, PLOT, tag, inst, ACCURACY):
    """ wrapper function for 1D sweep - HV gimbal """

    print("")
    freqList, meas_delay = get_meas_params(inst)                                # get sweep parameters

    print("## Please make sure everything is ready to start measurement ##")    # warning
    print("#####      Automatic motion of MilliBox will start!!       ####")
    print("##   Press SPACE BAR when all is ready to start plotting     ##")
    if sys.platform == "win32":                                                 # if we run windows, we can abort with <ESC>
        print("##   Press ESC to abort                                      ##")
    key = None
    while key != 32 and key != 27:                                              # wait for space bar or ESC
        key = ord(getch())
    if key == 27:
        return

    if inst.inst_type.find("SA") > -1 or inst.inst_type == "":                  # spectrum analyzer (or simulated) measurement
        for freq in freqList:                                                   # freq sweep
            print("")
            print("Setting freq to %g GHz..." % (freq/1e9))
            freq_str = str("f%05.0f" % (freq/1e9*1000))

            if inst.port_open:
                print("Setting instrument frequency")
                inst.set_freq(freq)                                             # set SA center freq / SG output freq
                inst.set_marker_freq(1, freq)                                   # set marker1 to center freq

            print("Measurement delay = %g msec" % (meas_delay*1000))
            if meas_delay > 0:
                meas_delay_str = str("del%0.0f_" % (meas_delay*1000))
            else:
                meas_delay_str = ""

            tag_full = ("%s_%s%s" % (freq_str, meas_delay_str, tag))            # tag name of data file

            mbxf.millibox_1dsweep(DIR, MINH, MAXH, MINV, MAXV, STEP, POL, PLOT, tag_full, inst, ACCURACY, meas_delay=meas_delay, plot_freq=freq)

    elif inst.inst_type.find("VNA") > -1:                                       # VNA measurement

        print("Measurement delay = %g msec" % (meas_delay*1000))
        if meas_delay > 0:
            meas_delay_str = str("del%0.0f_" % (meas_delay * 1000))
        else:
            meas_delay_str = ""

        tag_full = ("%s%s" % (meas_delay_str, tag))                             # tag name of data file

        mbxf.millibox_1dsweep(DIR, MINH, MAXH, MINV, MAXV, STEP, POL, PLOT, tag_full, inst, ACCURACY, meas_delay=meas_delay, plot_freq=freqList[0])

    return


def millibox_1dsweep_wrapper_sph(DIR, MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI, PLOT, tag, inst, ACCURACY):
    """ wrapper function for 1D sweep - SPHERICAL gimbal """

    print("")
    freqList, meas_delay = get_meas_params(inst)                                # get sweep parameters

    print("## Please make sure everything is ready to start measurement ##")    # warning
    print("#####      Automatic motion of MilliBox will start!!       ####")
    print("##   Press SPACE BAR when all is ready to start plotting     ##")
    if sys.platform == "win32":                                                 # if we run windows, we can abort with <ESC>
        print("##   Press ESC to abort                                      ##")
    key = None
    while key != 32 and key != 27:                                              # wait for space bar or ESC
        key = ord(getch())
    if key == 27:
        return

    if inst.inst_type.find("SA") > -1 or inst.inst_type == "":                  # spectrum analyzer (or simulated) measurement
        for freq in freqList:                                                   # freq sweep
            print("")
            print("Setting freq to %g GHz..." % (freq/1e9))
            freq_str = str("f%05.0f" % (freq/1e9*1000))

            if inst.port_open:
                print("Setting instrument frequency")
                inst.set_freq(freq)                                             # set SA center freq / SG output freq
                inst.set_marker_freq(1, freq)                                   # set marker1 to center freq

            print("Measurement delay = %g msec" % (meas_delay*1000))
            if meas_delay > 0:
                meas_delay_str = str("del%0.0f_" % (meas_delay*1000))
            else:
                meas_delay_str = ""

            tag_full = ("%s_%s%s" % (freq_str, meas_delay_str, tag))            # tag name of data file

            mbxf.millibox_1dsweep_sph(DIR, MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI, PLOT, tag_full, inst, ACCURACY, meas_delay=meas_delay, plot_freq=freq)

    elif inst.inst_type.find("VNA") > -1:                                       # VNA measurement

        print("Measurement delay = %g msec" % (meas_delay*1000))
        if meas_delay > 0:
            meas_delay_str = str("del%0.0f_" % (meas_delay * 1000))
        else:
            meas_delay_str = ""

        tag_full = ("%s%s" % (meas_delay_str, tag))                             # tag name of data file

        mbxf.millibox_1dsweep_sph(DIR, MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI, PLOT, tag_full, inst, ACCURACY, meas_delay=meas_delay, plot_freq=freqList[0])

    return


def millibox_hvsweep_wrapper(MIN, MAX, STEP, POL, PLOT, tag, inst, ACCURACY):
    """ wrapper function for HV sweep - HV gimbal """

    print("")
    freqList, meas_delay = get_meas_params(inst)                                # get sweep parameters

    print("## Please make sure everything is ready to start measurement ##")    # warning
    print("#####      Automatic motion of MilliBox will start!!       ####")
    print("##   Press SPACE BAR when all is ready to start plotting     ##")
    if sys.platform == "win32":                                                 # if we run windows, we can abort with <ESC>
        print("##   Press ESC to abort                                      ##")
    key = None
    while key != 32 and key != 27:                                              # wait for space bar or ESC
        key = ord(getch())
    if key == 27:
        return

    if inst.inst_type.find("SA") > -1 or inst.inst_type == "":                  # spectrum analyzer (or simulated) measurement
        for freq in freqList:                                                   # freq sweep
            print("")
            print("Setting freq to %g GHz..." % (freq/1e9))
            freq_str = str("f%05.0f" % (freq/1e9*1000))

            if inst.port_open:
                print("Setting instrument frequency")
                inst.set_freq(freq)                                             # set SA center freq / SG output freq
                inst.set_marker_freq(1,freq)                                    # set marker1 to center freq

            print("Measurement delay = %g msec" % (meas_delay*1000))
            if meas_delay > 0:
                meas_delay_str = str("del%0.0f_" % (meas_delay*1000))
            else:
                meas_delay_str = ""

            tag_full = ("%s_%s%s" % (freq_str, meas_delay_str, tag))            # tag name of data file

            mbxf.millibox_hvsweep(MIN, MAX, STEP, POL, PLOT, tag_full, inst, ACCURACY, meas_delay=meas_delay, plot_freq=freq)

    elif inst.inst_type.find("VNA") > -1:                                       # VNA measurement

        print("Measurement delay = %g msec" % (meas_delay * 1000))
        if meas_delay > 0:
            meas_delay_str = str("del%0.0f_" % (meas_delay * 1000))
        else:
            meas_delay_str = ""

        tag_full = ("%s%s" % (meas_delay_str, tag))                             # tag name of data file

        mbxf.millibox_hvsweep(MIN, MAX, STEP, POL, PLOT, tag_full, inst, ACCURACY, meas_delay=meas_delay, plot_freq=freqList[0])

    return


def millibox_hvsweep_wrapper_sph(MIN, MAX, STEP, DPHI, PLOT, tag, inst, ACCURACY):
    """ wrapper function for HV sweep - SPHERICAL gimbal """

    print("")
    freqList, meas_delay = get_meas_params(inst)                                # get sweep parameters

    print("## Please make sure everything is ready to start measurement ##")    # warning
    print("#####      Automatic motion of MilliBox will start!!       ####")
    print("##   Press SPACE BAR when all is ready to start plotting     ##")
    if sys.platform == "win32":                                                 # if we run windows, we can abort with <ESC>
        print("##   Press ESC to abort                                      ##")
    key = None
    while key != 32 and key != 27:                                              # wait for space bar or ESC
        key = ord(getch())
    if key == 27:
        return

    if inst.inst_type.find("SA") > -1 or inst.inst_type == "":                  # spectrum analyzer (or simulated) measurement
        for freq in freqList:                                                   # freq sweep
            print("")
            print("Setting freq to %g GHz..." % (freq/1e9))
            freq_str = str("f%05.0f" % (freq/1e9*1000))

            if inst.port_open:
                print("Setting instrument frequency")
                inst.set_freq(freq)                                             # set SA center freq / SG output freq
                inst.set_marker_freq(1,freq)                                    # set marker1 to center freq

            print("Measurement delay = %g msec" % (meas_delay*1000))
            if meas_delay > 0:
                meas_delay_str = str("del%0.0f_" % (meas_delay*1000))
            else:
                meas_delay_str = ""

            tag_full = ("%s_%s%s" % (freq_str, meas_delay_str, tag))            # tag name of data file

            mbxf.millibox_hvsweep_sph(MIN, MAX, STEP, DPHI, PLOT, tag_full, inst, ACCURACY, meas_delay=meas_delay, plot_freq=freq)

    elif inst.inst_type.find("VNA") > -1:                                       # VNA measurement

        print("Measurement delay = %g msec" % (meas_delay * 1000))
        if meas_delay > 0:
            meas_delay_str = str("del%0.0f_" % (meas_delay * 1000))
        else:
            meas_delay_str = ""

        tag_full = ("%s%s" % (meas_delay_str, tag))                             # tag name of data file

        mbxf.millibox_hvsweep_sph(MIN, MAX, STEP, DPHI, PLOT, tag_full, inst, ACCURACY, meas_delay=meas_delay, plot_freq=freqList[0])

    return


def millibox_2dsweep_wrapper(MINH, MAXH, MINV, MAXV, STEP, POL, PLOT, tag, inst, ACCURACY, zigzag=False):
    """ wrapper function for 2D sweep - HV gimbal """

    print("")
    freqList, meas_delay = get_meas_params(inst)                                # get sweep parameters

    print("## Please make sure everything is ready to start measurement ##")    # warning
    print("#####      Automatic motion of MilliBox will start!!       ####")
    print("##   Press SPACE BAR when all is ready to start plotting     ##")
    if sys.platform == "win32":                                                 # if we run windows, we can abort with <ESC>
        print("##   Press ESC to abort                                      ##")
    key = None
    while key != 32 and key != 27:                                              # wait for space bar or ESC
        key = ord(getch())
    if key == 27:
        return

    if inst.inst_type.find("SA") > -1 or inst.inst_type == "":                  # spectrum analyzer (or simulated) measurement
        for freq in freqList:                                                   # freq sweep
            print("")
            print("Setting freq to %g GHz..." % (freq/1e9))
            freq_str = str("f%05.0f" % (freq/1e9*1000))

            if inst.port_open:
                print("Setting instrument frequency")
                inst.set_freq(freq)                                             # set SA center freq / SG output freq
                inst.set_marker_freq(1,freq)                                    # set marker1 to center freq

            print("Measurement delay = %g msec" % (meas_delay*1000))
            if meas_delay > 0:
                meas_delay_str = str("del%0.0f_" % (meas_delay*1000))
            else:
                meas_delay_str = ""

            tag_full = ("%s_%s%s" % (freq_str, meas_delay_str, tag))            # tag name of data file

            mbxf.millibox_2dsweep(MINH, MAXH, MINV, MAXV, STEP, POL, PLOT, tag_full, inst, ACCURACY, meas_delay, plot_freq=freq, zigzag=zigzag)

    elif inst.inst_type.find("VNA") > -1:                                       # VNA measurement

        print("Measurement delay = %g msec" % (meas_delay * 1000))
        if meas_delay > 0:
            meas_delay_str = str("del%0.0f_" % (meas_delay * 1000))
        else:
            meas_delay_str = ""

        tag_full = ("%s%s" % (meas_delay_str, tag))                             # tag name of data file

        mbxf.millibox_2dsweep(MINH, MAXH, MINV, MAXV, STEP, POL, PLOT, tag_full, inst, ACCURACY, meas_delay, plot_freq=freqList[0], zigzag=zigzag)

    return


def millibox_2dsweep_wrapper_sph(MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI, PLOT, tag, inst, ACCURACY, zigzag=False):
    """ wrapper function for 2D sweep - SPHERICAL gimbal """

    print("")
    freqList, meas_delay = get_meas_params(inst)                                # get sweep parameters

    print("## Please make sure everything is ready to start measurement ##")    # warning
    print("#####      Automatic motion of MilliBox will start!!       ####")
    print("##   Press SPACE BAR when all is ready to start plotting     ##")
    if sys.platform == "win32":                                                 # if we run windows, we can abort with <ESC>
        print("##   Press ESC to abort                                      ##")
    key = None
    while key != 32 and key != 27:                                              # wait for space bar or ESC
        key = ord(getch())
    if key == 27:
        return

    if inst.inst_type.find("SA") > -1 or inst.inst_type == "":                  # spectrum analyzer (or simulated) measurement
        for freq in freqList:                                                   # freq sweep
            print("")
            print("Setting freq to %g GHz..." % (freq/1e9))
            freq_str = str("f%05.0f" % (freq/1e9*1000))

            if inst.port_open:
                print("Setting instrument frequency")
                inst.set_freq(freq)                                             # set SA center freq / SG output freq
                inst.set_marker_freq(1,freq)                                    # set marker1 to center freq

            print("Measurement delay = %g msec" % (meas_delay*1000))
            if meas_delay > 0:
                meas_delay_str = str("del%0.0f_" % (meas_delay*1000))
            else:
                meas_delay_str = ""

            tag_full = ("%s_%s%s" % (freq_str, meas_delay_str, tag))            # tag name of data file

            mbxf.millibox_2dsweep_sph(MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI, PLOT, tag_full, inst, ACCURACY, meas_delay, plot_freq=freq, zigzag=zigzag)

    elif inst.inst_type.find("VNA") > -1:                                       # VNA measurement

        print("Measurement delay = %g msec" % (meas_delay * 1000))
        if meas_delay > 0:
            meas_delay_str = str("del%0.0f_" % (meas_delay * 1000))
        else:
            meas_delay_str = ""

        tag_full = ("%s%s" % (meas_delay_str, tag))                             # tag name of data file

        mbxf.millibox_2dsweep_sph(MINTH, MAXTH, MINPH, MAXPH, STEP, DPHI, PLOT, tag_full, inst, ACCURACY, meas_delay, plot_freq=freqList[0], zigzag=zigzag)

    return


