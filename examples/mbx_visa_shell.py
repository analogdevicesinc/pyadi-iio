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

import six
import sys
import time
import mbx_scpi_connection as scpi


connected = False
visa_add = ""
port = []
cmd = ""
logfile = "visa_log.txt"


class Logger:
    """ mirrors STDOUT to screen and log file """

    def __init__(self, stdout, filename):
        self.stdout = stdout
        self.logfile = open(filename, 'a', buffering=1)

    def write(self, text):
        self.stdout.write(text)
        self.stdout.flush()
        self.logfile.write(text)

    def close(self):
        self.stdout.close()
        self.logfile.close()

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here
        pass


def connect_instr():
    """ select instrument from list or manual entry and connect """

    conn = False
    addr = ''
    p = scpi.visa_connection()

    print("")
    print("************** INSTRUMENT LIST **************")
    resources = scpi.list_resources()                                       # find list of potential instruments
    resources = list(resources)
    resources.insert(0, 'MANUAL ENTRY')                                     # pre-pend "MANUAL ENTRY" to the list - used to type in a socket address

    for y in range(len(resources)):                                         # list all the resources
        print("    %3d) %s" % (y, resources[y]))
    print("*********************************************")
    print("")

    done = False
    while not done:
        sel = six.moves.input("Select instrument: ")
        print(sel)

        try:
            sel_num = int(sel)                                              # try to convert selection to number
        except ValueError:
            sel_num = -1                                                    # non-integer input

        if sel_num in range(len(resources)):                                # valid selection
            if sel_num == 0:
                addr = str(six.moves.input("Enter equipment VISA address: "))
                conn = p.open_resource(addr)
                done = True
            else:
                addr = resources[sel_num]                                   # set the address of the instrument
                conn = p.open_resource(addr)                                # open new instrument port
                conn = True
                done = True

        if not done:
            print("Invalid selection. Please try again\n")

    print ("")
    print("Measurement instrument selected: %s" % addr)
    print ("")

    return p, addr, conn


print("")
print("****************** MilliBox VISA Shell Debugger ******************")
print(" This program allows connection to an instrument and interactive")
print(" debugging of the SCPI commands using basic write/read/query.")
print("")

while cmd not in ["Y", "N"]:
    cmd = six.moves.input("Save session to '%s'? [Y/N] " % logfile)
    cmd = cmd.upper()
    print("")

if cmd == "Y":
    # add header to log file
    f = open(logfile, 'a', buffering=1)
    f.write("\n\n\n\n")
    f.write("*****************************************************************************\n")
    f.write("*********     MilliBox VISA Shell Session - %s      ********\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    f.write("*****************************************************************************\n")
    f.write("\n\n\n")
    f.close()

    # send output to stdout and append to logfile visa_log.txt
    writer = Logger(sys.stdout, "visa_log.txt")
    sys.stdout = writer

while cmd != "X":
    if not connected:
        cmd = six.moves.input("NOT CONNECTED :: <C>onnect, E<X>it --> ")
        cmd = cmd.upper()
        print(cmd)

        if cmd == "C":
            (port, visa_add, connected) = connect_instr()

    else:
        cmd = six.moves.input("CONNECTED to %s :: <W>rite, <Q>uery, <R>ead, <T>imeout, <C>onnect, E<X>it --> " % visa_add)
        cmd = cmd.upper()
        print(cmd)

        if cmd == "W":
            x = six.moves.input("Write --> ")
            print(x)
            port.write(x)
            print("")

        if cmd == "Q":
            x = six.moves.input("Query --> ")
            print(x)
            try:
                print("Reply --> '%s'" % port.query(x))
            except:
                print("\n!! ERROR in Query. Please check command. !!\n")

        if cmd == "R":
            try:
                print("Read --> '%s'" % port.read())
            except:
                print("\n!! ERROR in Read. Please check command. !!\n")

        if cmd == "T":
            x = six.moves.input("Timeout (ms) [current = %g] --> " % (port.get_timeout()*1000.0))
            print(x)
            port.set_timeout(float(x)/1000.0)
            print("")

        if cmd == "C":
            (port, visa_add, connected) = connect_instr()
