#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Copyright 2021 MILLIWAVE SILICON SOLUTIONS, inc.

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

# Author: Chinh Doan Milliwave Silicon Solutions

import mbx_instrument as equip
import time
import six

print("")
print("*************  MILLIBOX INSTRUMENT DRIVER DIAGNOSTICS  *************")
print("*                                                                  *")
print("* This program checks the driver implementation for the equipment  *")
print("* control in mbx_instrument.py and used by mbx.py. All of the      *")
print("* necessary commands are exercised.                                *")
print("*                                                                  *")
print("* Adjust the SCPI commands and sequence until no error occurs.     *")
print("*                                                                  *")
print("********************************************************************")

# list all VISA devices
print("")
print("All connected devices:")
print("----------------------")
x = equip.list_resources()
x.insert(0, 'MANUAL ENTRY')                                                 # pre-pend "MANUAL ENTRY" to the list - used to type in a socket address
for k in range(len(x)):
    print("%3d) %s" % (k, x[k]))
print("")
sel = six.moves.input("Select the instrument address: ")
sel_num = int(sel)
if sel_num == 0:
    VISA_ADD = str(six.moves.input("Enter equipment VISA address: "))
else:
    VISA_ADD = x[sel_num]                                                   # set the address of the instrument


# select the equipment type (meas_mode)
print("")
print("Select the equipment type:")
print("----------------------------")
x = ['SA', 'SG', 'VNA']
for k in range(len(x)):
    print("%s) %s" % (chr(k+ord("a")), x[k]))
print("")
sel = six.moves.input("Select the equipment type: ")
equip_type = str(x[ord(sel)-ord("a")])

print("VISA address = %s" % VISA_ADD)
inst = equip.inst_setup(equip_type, VISA_ADD)
print("")


if equip_type == 'VNA':
    if inst.port_open:
        print("testing: VNA mode")
        # test basic VNA commands that need to be implemented for all VNA equipment drivers
        #   init_meas()
        #   get_status()
        #   fix_status()
        #   get_freq_list()
        #   single_trigger()
        #   get_s_dbphase()
        #   cont_trigger()

        six.moves.input('Press enter to continue...')

        print("")
        print(">> init_meas()...")
        six.moves.input('Press enter to continue...')
        t0 = time.time()
        inst.init_meas()
        t1 = time.time()
        print("done")
        print("%0.2f sec to initalize" % (t1-t0))

        print("")
        print(">> get_status()...")
        six.moves.input('Press enter to continue...')
        status = inst.get_status()
        print("done")
        print("status = %s" % str(status))

        print("")
        print(">> fix_status...")
        six.moves.input('Press enter to continue...')
        t0 = time.time()
        inst.fix_status()
        t1 = time.time()
        print("done")
        print("%0.2f sec to fix status" % (t1 - t0))

        print("")
        print(">> get_freq_list()...")
        six.moves.input('Press enter to continue...')
        freqlist = inst.get_freq_list()
        freqlist = [round(x/1.e9, 3) for x in freqlist]
        print("done")
        print("freqlist = %s" % str(freqlist))

        print("")
        print(">> single_trigger()...")
        six.moves.input('Press enter to continue...')
        t0 = time.time()
        inst.single_trigger()
        t1 = time.time()
        print("done")
        print("%0.2f sec for single sweep" % (t1-t0))

        print("")
        print(">> get_s_dbphase()...")
        six.moves.input('Press enter to continue...')
        t0 = time.time()
        db, phase = inst.get_s_dbphase()
        t1 = time.time()
        print("done")
        print("%0.2f sec to read data" % (t1-t0))
        db = [round(x, 2) for x in db]
        print("db = %s" % str(db))

        print("")
        print(">> cont_trigger()...")
        six.moves.input('Press enter to continue...')
        inst.cont_trigger()
        print("done")

elif equip_type == 'SA':
    if inst.port_open:
        print("testing: Spectrum analyzer mode")
        # test basic SA commands that need to be implemented for all SA equipment drivers
        #   init_meas()
        #   get_status()
        #   fix_status()
        #   enable_marker(1)
        #   set_freq
        #   set_marker_freq(1)
        #   get_marker_freq(1)
        #   get_marker(1)

        six.moves.input('Press enter to continue...')
        print("")

        freq = float(six.moves.input("enter frequency [Hz]: "))

        print("")
        print(">> init_meas()...")
        six.moves.input('Press enter to continue...')
        t0 = time.time()
        inst.init_meas()
        t1 = time.time()
        print("done")
        print("%0.2f sec to initalize" % (t1 - t0))

        print("")
        print(">> get_status()...")
        six.moves.input('Press enter to continue...')
        status = inst.get_status()
        print("done")
        print("status = %s" % str(status))

        print("")
        print(">> fix_status()...")
        six.moves.input('Press enter to continue...')
        t0 = time.time()
        inst.fix_status()
        t1 = time.time()
        print("done")
        print("%0.2f sec to fix status" % (t1 - t0))

        print("")
        print(">> enable_marker(1)...")
        six.moves.input('Press enter to continue...')
        inst.enable_marker(1)
        print("done")

        print("")
        print(">> set_freq(%f)..." % freq)
        six.moves.input('Press enter to continue...')
        inst.set_freq(freq)
        print("done")

        print("")
        print(">> set_marker_freq(1, %f)..." % freq)
        six.moves.input('Press enter to continue...')
        inst.set_marker_freq(1, freq)
        print("done")

        print("")
        print(">> get_marker_freq(1)...")
        six.moves.input('Press enter to continue...')
        freq = inst.get_marker_freq(1)
        print("done")
        print("freq = %s" % str(freq))

        print("")
        print(">> get_marker(1)...")
        six.moves.input('Press enter to continue...')
        pwr = inst.get_marker(1)
        print("done")
        print("pwr = %s" % str(pwr))

elif equip_type == 'SG':
    if inst.port_open:
        print("Signal generator mode")
        # test basic SG commands that need to be implemented for all SG equipment drivers
        #   init_meas()
        #   output_on()
        #   set_power()
        #   set_freq()

        six.moves.input('Press enter to continue...')
        print("")

        pwr = float(six.moves.input("enter power level [dBm]: "))
        freq = float(six.moves.input("enter frequency [Hz]: "))

        print("")
        print(">> init_meas()...")
        six.moves.input('Press enter to continue...')
        t0 = time.time()
        inst.init_meas()
        t1 = time.time()
        print("done")
        print("%0.2f sec to initalize" % (t1 - t0))

        print("")
        print(">> output_on()...")
        six.moves.input('Press enter to continue...')
        inst.output_on()
        print("done")

        print("")
        print(">> set_power(%f)..." % pwr)
        six.moves.input('Press enter to continue...')
        inst.set_power(pwr)
        print("done")

        print("")
        print(">> set_freq(%f)..." % freq)
        six.moves.input('Press enter to continue...')
        inst.set_freq(freq)
        print("done")

print("*************  DONE WITH INSTRUMENT DRIVER DIAGNOSTICS  *************")
