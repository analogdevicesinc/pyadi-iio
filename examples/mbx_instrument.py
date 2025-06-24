#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Copyright 2020 MILLIWAVE SILICON SOLUTIONS, inc.

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

import numpy as np                                                              # numpy numerical library
import re                                                                       # regexp library
import fnmatch                                                                  # basic wildcard string matching
import six                                                                      # Python2/Python3 input handling
import mbx_scpi_connection as scpi                                              # SCPI instrument controller


PRINT_VISA_TRAFFIC  = False                                                     # flag to print all VISA write/query traffic to screen for debug

TIMEOUT_IDN         = 5.0                                                       # max time to readback *IDN?
TIMEOUT_MEMLOAD     = 20.0                                                      # max time to load instrument state from memory
TIMEOUT_VNASWEEP    = 60.0                                                      # max time to perform a single VNA sweep
TIMEOUT_ALIGN       = 30.0                                                      # max time to perform spectrum analyzer alignment


############################################
# Instrument drivers using SCPI commands
############################################

def list_resources():
    """ list all VISA resources """
    return scpi.list_resources()


class Instrument(object):
    """ Basic class for instrument control using PyVisa """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = ""

    def __init__(self):                                                         # init function when object is created
        self.rm = []                                                            # resource manager
        self.port = scpi.visa_connection()                                      # port for the instrument
        self.addr = [""]                                                        # no default instrument address
        self.port_open = 0                                                      # flag if port to equipment is open
        return

    def open_instrument(self, addr):                                            # open instrument at given ADDR
        """ open instrument at given ADDR """
        self.close_instrument()                                                 # close current port, if open
        self.addr = addr                                                        # set the address
        x = scpi.visa_connection()
        if x.open_resource(addr[0]):
            self.port = x
            self.port_open = 1
        else:
            self.port_open = 0
        return

    def close_instrument(self):                                                 # close the instrument
        """ close the instrument """
        if self.port_open:
            self.port.close()
        self.port_open = 0
        return

    def write(self, cmd):                                                       # visa write with basic error handling
        """ visa write with basic error handling """
        if self.port_open:
            if PRINT_VISA_TRAFFIC:
                print("DEBUG:: VISA WRITE >> '%s'" % cmd)
            try:
                self.port.write(cmd)
            except:
                print("ERROR!! Timeout during instrument WRITE. Check connection.")
        return

    def query(self, cmd):                                                       # visa query with basic error handling
        """ visa query with basic error handling """
        if self.port_open:
            if PRINT_VISA_TRAFFIC:
                print("DEBUG:: VISA QUERY >> '%s'" % cmd)
            try:
                x = self.port.query(cmd)
            except:
                x = ""
            if PRINT_VISA_TRAFFIC:
                print("DEBUG::      REPLY << '%s'" % x)
            if x == "":
                print("ERROR!! QUERY error. Check connection or driver command.")
        else:
            x = ""
        return x

    def read(self):                                                             # visa read with basic error handling
        """ visa read with basic error handling """
        if self.port_open:
            try:
                x = self.port.read()
            except:
                x = ""
            if PRINT_VISA_TRAFFIC:
                print("DEBUG::  VISA READ << '%s'" % x)
            if x == "":
                print("ERROR!! READ error. Check connection or driver command.")
        else:
            x = ""
        return x

    def query_float(self, cmd):                                                 # visa query for float with basic error handling
        """ visa query for float with basic error handling """
        x = str(self.query(cmd))
        try:
            y = float(x)
        except:
            y = float("NaN")
            print("ERROR!! Returned value is not a FLOAT.")
        return y

    def query_int(self, cmd):                                                   # visa query for int with basic error handling
        """ visa query for int with basic error handling """
        x = str(self.query(cmd))
        try:
            y = int(x)
        except:
            y = float("NaN")
            print("ERROR!! Returned value is not an INT.")
        return y

    def init_meas(self):
        """ Stub function header to define the intialization to setup the measurement """
        return

    def get_status(self):
        """ Stub function header to report any error condition status for the equipment """
        status = 0
        return status

    def fix_status(self, status=None):
        """Stub function header to fix any error condition of the instrument """
        return


class SA_Generic(Instrument):
    """ generic spectrum analyzer instrument driver - based on Keysight SA commands """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "SA"

    def init_meas(self):                                                        # basic initialization to set up measurement
        """ basic initialization to set up measurement """
        if self.port_open:
            self.enable_marker(1)                                               # enable marker1
        return

    def enable_marker(self, num):                                               # enable marker (num)
        """ enable marker (num) """
        self.write("CALC:MARK%d:MODE POS" % num)
        return

    def set_marker_freq(self, num, freq):                                       # set marker freq (in Hz)
        """ set marker freq (in Hz) """
        self.write("CALC:MARK%d:X %f" % (num, freq))
        return

    def set_marker_peak(self, num):                                             # set marker to peak
        """ set marker to peak """
        self.write("CALC:MARK%d:MAX" % num)
        return

    def get_marker_freq(self, num):                                             # get marker freq (in Hz)
        """ get marker freq (in Hz) """
        return self.query_float("CALC:MARKER%d:X?" % num)

    def get_marker(self, num):                                                  # read value of marker
        """ read value of marker """
        return self.query_float("CALC:MARKER%d:Y?" % num)

    def set_freq(self, freq_Hz):                                                # set center freq (in Hz)
        """ set center freq (in Hz) """
        self.write("FREQ:CENTER %f" % freq_Hz)
        return

    def set_span(self, span_Hz):                                                # set span (in Hz)
        """ set span (in Hz) """
        self.write("FREQ:SPAN %f" % span_Hz)
        return

    def set_atten(self, atten_dB):                                              # set attenuator (in dB)
        """ set attenuator (in dB) """
        self.write("POW:ATT %f" % atten_dB)
        return

    def set_rbw(self, rbw_Hz):                                                  # set RBW (in Hz)
        """ set RBW (in Hz) """
        self.write("BAND %f" % rbw_Hz)
        return

    def set_vbw(self, vbw_Hz):                                                  # set VBW (in Hz)
        """ set VBW (in Hz) """
        self.write("BAND:VID %f" % vbw_Hz)
        return

    def set_rlev(self, rlev_dBm):                                               # set RLEV (in dBm)
        """ set RLEV (in dBm) """
        self.write("DISP:WIND:TRAC:Y:RLEV %f" % rlev_dBm)
        return


class SA_RohdeSchwarz_FSW(SA_Generic):
    """ R&S FSW instrument driver """

    # include any specific FSW commands here
    def SA_RohdeSchwarz_FSW_specific_func(self):
        return

    def init_meas(self):                                                        # basic initialization to set up measurement
        """ basic initialization to set up measurement """
        # code tested on FSW67
        if self.port_open:

            # example settings for good CW measurements
            # adjust as desired
            self.write("SYST:DISP:UPD ON")                                      # enable display during remote control
            self.set_span(5e6)                                                  # 5MHz span
            self.set_rbw(100e3)                                                 # 100kHz RBW
            self.set_vbw(1e3)                                                   # 1kHz VBW
            self.set_rlev(-20)                                                  # set RLEV=-20dBm
            self.set_atten(0)                                                   # 0dB attenuation
            self.enable_marker(1)                                               # enable marker1
        return

    # command syntax for setting attenuator different than SA_Generic (Keysight) command
    def set_atten(self, atten_dB):                                              # set attenuator (in dB)
        """ set attenuator (in dB) """
        self.write("INP:ATT %f" % atten_dB)
        return

    # command syntax for enabling marker different than SA_Generic (Keysight) command
    def enable_marker(self, num):                                               # enable marker (num)
        """ enable marker (num) """
        self.write("CALC:MARK%d:STATE ON" % num)
        return


class SA_Keysight_Generic(SA_Generic):
    """ Keysight generic instrument driver """

    # include any specific Keysight commands here
    def SA_Keysight_Generic_specific_func(self):
        return

    def init_meas(self):                                                        # initialize to set up measurement
        """ initialize to set up measurement """
        # code tested on Agilent N9010B spectrum analyzer
        if self.port_open:
            # example settings for good CW measurements
            # adjust as desired

            # may want to turn alignment off during sweep
            # alignment checking and re-starting alignment differs depending on model
            # generic driver does not disable alignment

            # self.align_auto_off()                                               # turn off auto alignment

            self.set_span(5e6)                                                  # 5MHz span
            self.set_rbw(100e3)                                                 # 100kHz RBW
            self.set_vbw(1e3)                                                   # 1kHz VBW
            self.set_rlev(-20)                                                  # set RLEV=-20dBm
            self.set_atten(0)                                                   # 0dB attenuation
            self.enable_marker(1)                                               # enable marker1

            self.fix_status()                                                   # check ready status, and fix if needed
        return

    def get_status(self):                                                       # get error status
        """ get error status """
        status = 0
        return status

    def fix_status(self, status=None):                                          # pass in status argument from get_status, if available
        """ pass in status argument from get_status, if available """
        pass
        return


class SA_Keysight_EXA(SA_Keysight_Generic):
    """ Keysight EXA instrument driver """

    # include any specific Keysight EXA commands here
    def SA_Keysight_EXA_specific_func(self):
        return

    def init_meas(self):                                                        # initialize to set up measurement
        """ initialize to set up measurement """
        # code tested on Agilent N9010B spectrum analyzer
        if self.port_open:
            self.align_auto_off()                                               # turn off auto alignment

            # example settings for good CW measurements
            # adjust as desired
            self.set_span(5e6)                                                  # 5MHz span
            self.set_rbw(100e3)                                                 # 100kHz RBW
            self.set_vbw(1e3)                                                   # 1kHz VBW
            self.set_rlev(-20)                                                  # set RLEV=-20dBm
            self.set_atten(0)                                                   # 0dB attenuation
            self.enable_marker(1)                                               # enable marker1
            self.cont_trigger()                                                 # continuous trigger

            self.fix_status()                                                   # check ready status, and fix if needed
        return

    def single_trigger(self):                                                   # trigger and hold trace
        """ trigger and hold trace """
        # print("single_trigger")                                                 # debug
        self.write('INIT:CONT 0')
        self.write('INIT:IMM')
        self.query('*OPC?')
        return

    def cont_trigger(self):                                                     # enable continuous trigger
        """ enable continuous trigger """
        self.write('INIT:CONT 1')
        return

    def get_status(self):                                                       # get error status
        """ get error status """
        # code tested on Agilent N9010B spectrum analyzer
        status = 0
        if self.port_open:
            status = status | self.align_needed() * 2 ** 0                      # bit0 - alignment needed
        return status

    def fix_status(self, status=None):                                          # pass in status argument from get_status, if available
        """ pass in status argument from get_status, if available """
        # code tested on Agilent N9010B spectrum analyzer
        if self.port_open:
            if status is None:
                status = self.get_status()                                      # if status value is not passed, readback status
            if status & 2**0 > 0:                                               # check bit0 - alignment needed
                print("*** ALIGNING EXPIRED CALIBRATION ***")
                self.align_exp_now()                                            # align all expired calibrations
                if self.align_needed():                                         # expired cal may not be enough, then run full alignment
                    print("*** ALIGNING FULL CALIBRATION ***")
                    self.align_all_now()
        return

    def align_auto_on(self):                                                    # set alignment = auto
        """ set alignment = auto """
        self.write("CAL:AUTO ON")
        return

    def align_auto_partial(self):                                               # set alignment = partial
        """ set alignment = partial """
        self.write("CAL:AUTO PART")
        return

    def align_auto_off(self):                                                   # set alignment = off
        """ set alignment = off """
        self.write("CAL:AUTO OFF")
        return

    def align_all_now(self, blocking=1):                                        # align all now
        """ align all now """
        if blocking:                                                            # blocking calibration - wait until done before returning
            timeout_orig = self.port.get_timeout()
            self.port.set_timeout(TIMEOUT_ALIGN)                                # set timeout to TIMEOUT_ALIGN
            status = self.query_int("CAL?")                                     # align all - wait until done to continue
            self.port.set_timeout(timeout_orig)                                 # restore timeout value
        else:
            self.write("CAL:NPEN")                                              # non-blocking calibration - do not wait for completion
            # self.query('STAT:OPER:COND?')                                     # query bit0 of stat:oper:cond? to see when cal is completed
        return

    def align_exp_now(self):                                                    # align expired cals
        """ align expired cals """
        timeout_orig = self.port.get_timeout()
        self.port.set_timeout(TIMEOUT_ALIGN)                                    # set timeout to TIMEOUT_ALIGN
        status = self.query_int("CAL:EXP?")                                     # align expired - wait until done to continue
        self.port.set_timeout(timeout_orig)                                     # restore timeout value
        return

    def align_done(self):                                                       # query alignment done status
        """ query alignment done status """
        stat_oper_cond = self.query_int('STAT:OPER:COND?')                      # query the status operating condition
        cal_done = stat_oper_cond & 2**0 == 0                                   # check bit0 (0 - done, 1 - running)
        return cal_done

    def align_needed(self):                                                     # query if alignment is needed
        """ query if alignment is needed """
        stat_ques_cal_cond = self.query_int('STAT:QUES:CAL:COND?')              # check if errors or failures of previous calibration
        cal_needed = stat_ques_cal_cond & 2 ** 14 > 0                           # check bit 14
        return cal_needed


class SG_Generic(Instrument):
    """ generic signal generator instrument driver """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "SG"

    def init_meas(self):                                                        # basic initialize to set up measurement
        """ basic initialize to set up measurement """
        if self.port_open:
            # example settings for good CW measurements
            # adjust as desired
            self.set_power(10)                                                  # Pout = 10dBm
            self.output_on()                                                    # enable Pout
        return

    def set_freq(self, freq_Hz):                                                # set freq (in Hz)
        """ set freq (in Hz) """
        self.write("FREQ %f" % freq_Hz)
        return

    def set_power(self, power_dBm):                                             # set output power (in dBm)
        """ set output power (in dBm) """
        self.write("POW %f" % power_dBm)
        return

    def output_on(self):                                                        # enable RF output
        """ enable RF output """
        self.write("OUTP 1")
        return

    def output_off(self):                                                       # disable RF output
        """ disable RF output """
        self.write("OUTP 0")
        return


class SG_Keysight_MXG(SG_Generic):
    """ Keysight MXG instrument driver """
    # include any specific Keysight MXG commands here
    def SG_Keysight_MXG_specific_func(self):
        return


class VNA_Generic(Instrument):
    """ Generic VNA driver - does not do anything, but defines the required functions """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "VNA"

    def init_meas(self):                                                        # initialize VNA
        """ initialize VNA """
        print("Generic VNA driver stub: init_meas()")
        return

    def get_status(self):                                                       # optional function to check error status
        """ optional function to check error status """
        print("Generic VNA driver stub: get_status()")
        status = 0
        return status

    def fix_status(self, status=None):                                          # optional function to fix error status
        """ optional function to fix error status """
        print("Generic VNA driver stub: fix_status()")
        return

    def get_freq_list(self):                                                    # query VNA sweep freq list
        """ query VNA sweep freq list """
        print("Generic VNA driver stub: get_freq_list()")
        freqList = [28.0e9]
        return freqList

    def single_trigger(self):                                                   # trigger and hold trace
        """ trigger and hold trace """
        print("Generic VNA driver stub: single_trigger()")
        return

    def cont_trigger(self):                                                     # enable continuous trigger
        """ enable continuous trigger """
        print("Generic VNA driver stub: cont_trigger()")
        return

    def get_sparam(self):
        """ return S-parameters on ACTIVE trace as list of complex numbers """
        print("Generic VNA driver stub: get_sparam()")
        sComplex = [1.0]
        return sComplex

    def get_s_dbphase(self):
        """ return S-parameters on ACTIVE trace as a tuple with list of log mag and list of phase """
        s = self.get_sparam()
        db = [20*np.log10(np.abs(x)) for x in s]
        phase = [np.angle(x, deg=True) for x in s]
        return db, phase


class VNA_Anritsu(VNA_Generic):
    """ Anritsu VNA driver - Tested with Anritsu MS464xB Vector Star """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "VNA"

    def init_meas(self):                                                        # initialize VNA
        """ initialize VNA """
        if self.port_open:

            # save cal state file to C:\MILLIBOX\MBX.CHX or change this file name
            # this cal file resides on the VNA hard drive
            calfile = "C:\\MILLIBOX\\MBX.CHX"

            print("")
            print("******************** IMPORTANT ********************")
            print("  Loading %s" % calfile)
            print("  Ensure VNA is calibrated, frequencies are set, and")
            print("  transmission measurement is on the ACTIVE trace")
            print("***************************************************")

            timeout_orig = self.port.get_timeout()
            self.port.set_timeout(TIMEOUT_MEMLOAD)                              # set timeout to TIMEOUT_MEMLOAD
            print("loading cal file...")
            self.write("MMEM:LOAD '%s'" % calfile)                              # load cal file
            self.query("*OPC?")                                                 # wait until done
            self.port.set_timeout(timeout_orig)                                 # restore timeout value
            print("setting to logmag...")
            self.write("CALC1:SEL:FORM MLOG")                                   # set currently selected trace to display in logmag
            print("continuous trigger on...")
            self.write("SENS:HOLD:FUNC CONT")                                   # set continuous sweep
        return

    def get_status(self):                                                       # optional function to check error status
        """ optional function to check error status """
        status = 0
        return status

    def fix_status(self, status=None):                                          # optional function to fix error status
        """ optional function to fix error status """
        return

    def get_freq_list(self):                                                    # query VNA sweep freq list
        """ query VNA sweep freq list """
        startFreq = self.query_float("SENS1:FREQ:STAR?")
        stopFreq = self.query_float("SENS1:FREQ:STOP?")
        numPts = self.query_int("SENS1:SWE:POIN?")
        freqList = list(np.linspace(startFreq, stopFreq, numPts))
        return freqList

    def single_trigger(self):                                                   # trigger and hold trace
        """ trigger and hold trace """
        timeout_orig = self.port.get_timeout()
        self.port.set_timeout(TIMEOUT_VNASWEEP)                                 # set timeout to TIMEOUT_VNASWEEP
        self.write("SENS1:HOLD:FUNC HOLD")                                      # put instrument in manual sweep mode
        self.write("TRIG:SING")                                                 # trigger a sweep and wait until it's completed
        sweepDone = self.query("*OPC?")
        # print("Sweep is done: " + str(sweepDone))
        self.port.set_timeout(timeout_orig)                                     # restore timeout value
        return

    def cont_trigger(self):                                                     # enable continuous trigger
        """ enable continuous trigger """
        self.write("SENS1:HOLD:FUNC CONT")                                      # put instrument in continuous sweep mode
        return

    def get_sparam(self):
        """ return S-parameters on ACTIVE trace as list of complex numbers """
        self.write("FORM:DATA ASC")                                             # change to ASCII
        sData = self.query("CALC1:DATA:SDAT?")                                  # get the S-param data in real, imag format
        sStr = str(sData)                                                       # convert from unicode to string
        sStr = str.strip(sStr)                                                  # remove trailing whitespace (cr/lf)
        sStr = re.sub('^#[0-9]+[\s]*', '', sStr)                                # strip header of #XXXX at the start of the data
        x = re.split('[\s,]+',sStr)                                             # split comma and whitespace delimited string to individual strings
        sComplex = []
        for i in range(0, len(x), 2):
            sComplex.append(float(x[i]) + 1j*float(x[i+1]))                     # create a list of complex numbers
        return sComplex

    def get_s_dbphase(self):
        """ return S-parameters on ACTIVE trace as a tuple with list of log mag and list of phase """
        s = self.get_sparam()
        db = [20*np.log10(np.abs(x)) for x in s]
        phase = [np.angle(x, deg=True) for x in s]
        return db, phase


class VNA_Keysight_PNA(VNA_Generic):
    """ Keysight/Agilent VNA driver - Tested with Agilent E8361A """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "VNA"

    def init_meas(self):                                                        # initialize VNA
        """ initialize VNA """

        # save cal state file to C:\MILLIBOX\MBX.CSA or change this file name
        # this cal file resides on the VNA hard drive
        calfile = "C:\\MILLIBOX\\MBX.CSA"

        print("")
        print("******************** IMPORTANT ********************")
        print("  Loading %s" % calfile)
        print("  Ensure VNA is calibrated, frequencies are set, and")
        print("  transmission measurement is the only active trace")
        print("***************************************************")

        timeout_orig = self.port.get_timeout()
        self.port.set_timeout(TIMEOUT_MEMLOAD)                                  # set timeout to TIMEOUT_MEMLOAD
        print("loading cal file...")
        self.write("MMEM:LOAD '%s'" % calfile)                                  # load state and cal file
        self.query("*OPC?")                                                     # wait until done
        self.port.set_timeout(timeout_orig)                                     # restore timeout value
        print("querying the first trace...")
        traces = self.query("CALC:PAR:CAT?")                                    # query the trace names
        traces = str(traces)                                                    # convert from unicode to string
        traces = re.sub('[\'\"]', '', traces)                                   # remove quotes ' and " from string
        x = re.split('[\s,]+', traces)                                          # split comma and whitespace delimited string to individual strings
        print("selecting trace '%s'..." % x[0])
        self.write("CALC:PAR:SEL '%s'" % x[0])                                  # select the first (only) trace
        print("setting to logmag...")
        self.write("CALC1:FORM MLOG")                                           # set display to logmag
        print("continuous trigger on...")
        self.write("INIT:CONT ON")                                              # set continuous sweep
        return

    def get_status(self):                                                       # optional function to check error status
        """ optional function to check error status """
        status = 0
        return status

    def fix_status(self, status=None):                                          # optional function to fix error status
        """ optional function to fix error status """
        return

    def get_freq_list(self):                                                    # query VNA sweep freq list
        """ query VNA sweep freq list """
        startFreq = self.query_float("SENS1:FREQ:STAR?")
        stopFreq = self.query_float("SENS1:FREQ:STOP?")
        numPts = self.query_int("SENS1:SWE:POIN?")
        freqList = list(np.linspace(startFreq, stopFreq, numPts))
        return freqList

    def single_trigger(self):                                                   # trigger and hold trace
        """ trigger and hold trace """
        timeout_orig = self.port.get_timeout()
        self.port.set_timeout(TIMEOUT_VNASWEEP)                                 # set timeout to TIMEOUT_VNASWEEP
        self.write("INIT:CONT OFF")                                             # put instrument in manual sweep mode
        self.write("INIT:IMM")                                                  # trigger a sweep
        sweepDone = self.query("*OPC?")                                         # wait until it's completed
        # print("Sweep is done: " + str(sweepDone))
        self.port.set_timeout(timeout_orig)                                     # restore timeout value
        return

    def cont_trigger(self):                                                     # enable continuous trigger
        """ enable continuous trigger """
        self.write("INIT:CONT ON")                                              # put instrument in continuous sweep mode
        return

    def get_sparam(self):
        """ return S-parameters as list of complex numbers """
        traces = self.query("CALC:PAR:CAT?")                                    # query the trace names
        traces = str(traces)                                                    # convert from unicode to string
        traces = re.sub('[\'\"]', '', traces)                                   # remove quotes ' and " from string
        x = re.split('[\s,]+', traces)                                          # split comma and whitespace delimited string to individual strings
        self.write("CALC:PAR:SEL '%s'" % x[0])                                  # select the first (only) trace
        self.write("FORMat ASCII")                                              # change to ASCII
        sData = self.query("CALC1:DATA? SDATA")                                 # get the S-param data in real, imag format
        sStr = str(sData)                                                       # convert from unicode to string
        sStr = str.strip(sStr)                                                  # remove trailing whitespace (cr/lf)
        x = re.split('[\s,]+', sStr)                                            # split comma and whitespace delimited string to individual strings
        sComplex = []
        for i in range(0, len(x), 2):
            sComplex.append(float(x[i]) + 1j*float(x[i+1]))                     # create a list of complex numbers
        return sComplex

    def get_s_dbphase(self):
        """ return S-parameters as a tuple with list of log mag and list of phase """
        s = self.get_sparam()
        db = [20*np.log10(np.abs(x)) for x in s]
        phase = [np.angle(x, deg=True) for x in s]
        return db, phase


class VNA_RohdeSchwarz_ZVA(VNA_Generic):
    """ Rohde & Schwarz VNA driver - Tested with Rohde ZVA67 """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "VNA"

    def init_meas(self):                                                        # initialize VNA
        """ initialize VNA """

        # save cal state file to C:\MILLIBOX\MBX.ZVX or change this file name
        # this cal file resides on the VNA hard drive
        calfile = "C:\\MILLIBOX\\MBX.ZVX"

        print("")
        print("******************** IMPORTANT ********************")
        print("  Loading %s" % calfile)
        print("  Ensure VNA is calibrated, frequencies are set, and")
        print("  transmission measurement is the ONLY active trace")
        print("***************************************************")

        timeout_orig = self.port.get_timeout()
        self.port.set_timeout(TIMEOUT_MEMLOAD)                                  # set timeout to TIMEOUT_MEMLOAD
        print("enable system display in remote control mode...")
        self.write("SYST:DISP:UPD ON")                                          # enable display during remote control
        print("loading cal file...")
        self.write("MMEM:LOAD:STAT 1, '%s'" % calfile)                          # load state and cal file
        self.query("*OPC?")                                                     # wait until done
        self.port.set_timeout(timeout_orig)                                     # restore timeout value
        print("selecting the first trace...")
        traces = self.query("CALC:PAR:CAT?")                                    # query the trace names
        traces = str(traces)                                                    # convert from unicode to string
        traces = re.sub('[\'\"]', '', traces)                                   # remove quotes ' and " from string
        x = re.split('[\s,]+', traces)                                          # split comma and whitespace delimited string to individual strings
        print("setting to trace '%s'..." % x[0])
        self.write("CALC:PAR:SEL '%s'" % x[0])                                  # select the first (only) trace
        print("setting to logmag...")
        self.write("CALC:FORM MLOG")                                            # set display to logmag
        print("continuous trigger on...")
        self.write("INIT:CONT ON")                                              # set continuous sweep
        return

    def get_status(self):                                                       # optional function to check error status
        """ optional function to check error status """
        status = 0
        return status

    def fix_status(self, status=None):                                          # optional function to check error status
        """ optional function to check error status """
        return

    def get_freq_list(self):                                                    # query VNA sweep freq list
        """ query VNA sweep freq list """
        startFreq = self.query_float("SENS:FREQ:STAR?")
        stopFreq = self.query_float("SENS:FREQ:STOP?")
        numPts = self.query_int("SENS:SWE:POIN?")
        freqList = list(np.linspace(startFreq, stopFreq, numPts))
        return freqList

    def single_trigger(self):                                                   # trigger and hold trace
        """ trigger and hold trace """
        timeout_orig = self.port.get_timeout()
        self.port.set_timeout(TIMEOUT_VNASWEEP)                                 # set timeout to TIMEOUT_VNASWEEP
        self.write("INIT:CONT OFF")                                             # put instrument in manual sweep mode
        self.write("INIT:IMM")                                                  # trigger a sweep
        sweepDone = self.query("*OPC?")                                         # wait until it's completed
        # print("Sweep is done: " + str(sweepDone))
        self.port.set_timeout(timeout_orig)                                     # restore timeout value
        return

    def cont_trigger(self):                                                     # enable continuous trigger
        """ enable continuous trigger """
        self.write("INIT:CONT ON")                                              # put instrument in continuous sweep mode
        return

    def get_sparam(self):
        """ return S-parameters as list of complex numbers """
        traces = self.query("CALC:PAR:CAT?")                                    # query the trace names
        traces = str(traces)                                                    # convert from unicode to string
        traces = re.sub('[\'\"]', '', traces)                                   # remove quotes ' and " from string
        x = re.split('[\s,]+', traces)                                          # split comma and whitespace delimited string to individual strings
        self.write("CALC:PAR:SEL '%s'" % x[0])                                  # select the first (only) trace
        self.write("FORMat ASCII")                                              # change to ASCII
        sData = self.query("CALC:DATA? SDATA")                                  # get the S-param data in real, imag format
        sStr = str(sData)                                                       # convert from unicode to string
        sStr = str.strip(sStr)                                                  # remove trailing whitespace (cr/lf)
        x = re.split('[\s,]+',sStr)                                             # split comma and whitespace delimited string to individual strings
        sComplex = []
        for i in range(0, len(x), 2):
            sComplex.append(float(x[i]) + 1j*float(x[i+1]))                     # create a list of complex numbers
        return sComplex

    def get_s_dbphase(self):
        """ return S-parameters as a tuple with list of log mag and list of phase """
        s = self.get_sparam()
        db = [20*np.log10(np.abs(x)) for x in s]
        phase = [np.angle(x, deg=True) for x in s]
        return db, phase


class VNA_RohdeSchwarz_ZVK(VNA_Generic):
    """ Rohde & Schwarz VNA driver - Tested with Rohde ZVK """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "VNA"

    def init_meas(self):                                                        # initialize VNA
        """ initialize VNA """

        # save cal state file to C:\MILLIBOX\MBX.ZVX or change this file name
        # this cal file resides on the VNA hard drive
        # calfile = "C:\\MILLIBOX\\MBX.ZVX"

        print("")
        print("******************** IMPORTANT ********************")
        # print("  Loading %s" % calfile)                                         # loading calfile on ZVK not working
        print("  Ensure VNA is calibrated, frequencies are set, and")
        print("  transmission measurement is on CHANNEL1")
        print("***************************************************")

        # timeout_orig = self.port.get_timeout()
        # self.port.set_timeout(TIMEOUT_MEMLOAD)                                  # set timeout to TIMEOUT_MEMLOAD
        print("enable system display in remote control mode...")
        self.write("SYST:DISP:UPD ON")                                          # enable display during remote control
        # print("loading cal file...")
        # self.write("MMEM:LOAD:STAT 1, '%s'" % calfile)                          # load state and cal file
        # self.query("*OPC?")                                                     # wait until done
        # self.port.set_timeout(timeout_orig)                                     # restore timeout value
        print("setting to single screen display...")
        self.write("DISP:FORM SING")                                            # set display to single screen
        self.write("INST:COUP NONE")                                            # disable coupled channels
        print("setting to CHANNEL1...")
        self.write("INST:SEL CHANNEL1")                                         # select Channel1
        print("setting to logmag...")
        self.write("CALC1:FORM MAGN")                                           # set display to logmag
        print("continuous trigger on...")
        self.write("INIT:CONT ON")                                              # set continuous sweep
        return

    def get_status(self):                                                       # optional function to check error status
        """ optional function to check error status """
        status = 0
        return status

    def fix_status(self, status=None):                                          # optional function to check error status
        """ optional function to check error status """
        return

    def get_freq_list(self):                                                    # query VNA sweep freq list
        """ query VNA sweep freq list """
        startFreq = self.query_float("SENS:FREQ:STAR?")
        stopFreq = self.query_float("SENS:FREQ:STOP?")
        numPts = self.query_int("SENS:SWE:POIN?")
        freqList = list(np.linspace(startFreq, stopFreq, numPts))
        return freqList

    def single_trigger(self):                                                   # trigger and hold trace
        """ trigger and hold trace """
        timeout_orig = self.port.get_timeout()
        self.port.set_timeout(TIMEOUT_VNASWEEP)                                 # set timeout to TIMEOUT_VNASWEEP
        self.write("INIT:CONT OFF")                                             # put instrument in manual sweep mode
        self.write("INIT:IMM")                                                  # trigger a sweep
        sweepDone = self.query("*OPC?")                                         # wait until it's completed
        # print("Sweep is done: " + str(sweepDone))
        self.port.set_timeout(timeout_orig)                                     # restore timeout value
        return

    def cont_trigger(self):                                                     # enable continuous trigger
        """ enable continuous trigger """
        self.write("INIT:CONT ON")                                              # put instrument in continuous sweep mode
        return

    def get_sparam(self):
        """ return S-parameters as list of complex numbers """
        self.write("FORMat ASCII")                                              # change to ASCII
        sData = self.query("TRAC:DATA:RESP:BODY? CH1DATA")                      # get the S-param data in real, imag format (CHANNEL1)
        sStr = str(sData)                                                       # convert from unicode to string
        sStr = str.strip(sStr)                                                  # remove trailing whitespace (cr/lf)
        x = re.split('[\s,]+',sStr)                                             # split comma and whitespace delimited string to individual strings
        sComplex = []
        for i in range(0, len(x), 2):
            sComplex.append(float(x[i]) + 1j*float(x[i+1]))                     # create a list of complex numbers
        return sComplex

    def get_s_dbphase(self):
        """ return S-parameters as a tuple with list of log mag and list of phase """
        s = self.get_sparam()
        db = [20*np.log10(np.abs(x)) for x in s]
        phase = [np.angle(x, deg=True) for x in s]
        return db, phase


class VNA_CopperMountain(VNA_Generic):
    """ Copper Mountain VNA driver - Tested with S2VNA Software v21.4.4 """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "VNA"

    def init_meas(self):                                                        # initialize VNA
        """ initialize VNA """
        if self.port_open:

            # save cal state file to C:\MILLIBOX\MBX.STA or change this file name
            # this cal file resides on the VNA hard drive
            calfile = "C:\\MILLIBOX\\MBX.STA"

            print("")
            print("******************** IMPORTANT ********************")
            print("  Loading %s" % calfile)
            print("  Ensure VNA is calibrated, frequencies are set, and")
            print("  transmission measurement is on the ACTIVE trace")
            print("***************************************************")

            timeout_orig = self.port.get_timeout()
            self.port.set_timeout(TIMEOUT_MEMLOAD)                              # set timeout to TIMEOUT_MEMLOAD
            print("loading cal file...")
            self.write("MMEM:LOAD '%s'" % calfile)                              # load cal file
            self.query("*OPC?")                                                 # wait until done
            self.port.set_timeout(timeout_orig)                                 # restore timeout value
            print("setting to logmag...")
            self.write("CALC:FORM MLOG")                                        # set display to logmag
            print("continuous trigger on...")
            self.write("INIT:CONT ON")                                          # keep the trigger in continuous state
            self.write("TRIG:SOUR INT")                                         # set to internal trigger source
        return

    def get_status(self):                                                       # optional function to check error status
        """ optional function to check error status """
        status = 0
        return status

    def fix_status(self, status=None):                                          # optional function to fix error status
        """ optional function to fix error status """
        return

    def get_freq_list(self):                                                    # query VNA sweep freq list
        """ query VNA sweep freq list """
        startFreq = self.query_float("SENS1:FREQ:STAR?")
        stopFreq = self.query_float("SENS1:FREQ:STOP?")
        numPts = self.query_int("SENS1:SWE:POIN?")
        freqList = list(np.linspace(startFreq, stopFreq, numPts))
        return freqList

    def single_trigger(self):                                                   # trigger and hold trace
        """ trigger and hold trace """
        timeout_orig = self.port.get_timeout()
        self.port.set_timeout(TIMEOUT_VNASWEEP)                                 # set timeout to TIMEOUT_VNASWEEP
        self.write("TRIG:SOUR BUS")                                             # set trigger source to BUS
        self.write("TRIG:SING")                                                 # trigger a sweep
        sweepDone = self.query("*OPC?")                                         # wait until it's completed
        # print("Sweep is done: " + str(sweepDone))
        self.port.set_timeout(timeout_orig)                                     # restore timeout value
        return

    def cont_trigger(self):                                                     # enable continuous trigger
        """ enable continuous trigger """
        self.write("TRIG:SOUR INT")                                             # set to internal trigger source
        return

    def get_sparam(self):
        """ return S-parameters on ACTIVE trace as list of complex numbers """
        self.write("FORM:DATA ASC")                                             # change to ASCII
        sData = self.query("CALC1:DATA:SDAT?")                                  # get the S-param data in real, imag format
        sStr = str(sData)                                                       # convert from unicode to string
        sStr = str.strip(sStr)                                                  # remove trailing whitespace (cr/lf)
        x = re.split('[\s,]+',sStr)                                             # split comma and whitespace delimited string to individual strings
        sComplex = []
        for i in range(0, len(x), 2):
            sComplex.append(float(x[i]) + 1j*float(x[i+1]))                     # create a list of complex numbers
        return sComplex

    def get_s_dbphase(self):
        """ return S-parameters on ACTIVE trace as a tuple with list of log mag and list of phase """
        s = self.get_sparam()
        db = [20*np.log10(np.abs(x)) for x in s]
        phase = [np.angle(x, deg=True) for x in s]
        return db, phase


class SGSA_Combo(object):
    """ Combination class for Sig Gen + Spectrum Analyzer """

    # class attribute for the instrument type (SA,VNA,SG,etc.)
    inst_type = "SG+SA"

    def __init__(self, sg=SG_Generic(), sa=SA_Generic()):                       # init function when object is created
        self.addr = [sg.addr[0], sa.addr[0]]                                    # no default instrument address
        self.port_open = sg.port_open and sa.port_open                          # flag if both ports to equipment are open
        self.inst_sg = sg
        self.inst_sa = sa
        return

    def init_meas(self):                                                        # init both SG and SA
        """ init both SG and SA """
        self.inst_sg.init_meas()
        self.inst_sa.init_meas()
        return

    def open_instrument(self, addr):                                            # open instrument at given ADDR
        """ open instrument at given ADDR """
        self.inst_sg.open_instrument([addr[0]])
        # print "open_instrument: [addr[0]] = " + str([addr[0]])
        self.inst_sa.open_instrument([addr[1]])
        # print "open_instrument: [addr[1]] = " + str([addr[1]])
        self.addr = addr
        # print "open_instrument: self.addr = " + str(self.addr)
        self.port_open = self.inst_sg.port_open and self.inst_sa.port_open      # flag if ports to both equipment are open

    def close_instrument(self):                                                 # close the instruments
        """ close the instruments """
        self.inst_sg.close_instrument()
        self.inst_sa.close_instrument()
        self.port_open = 0

    def get_status(self):                                                       # get error status
        """ get error status """
        return self.inst_sa.get_status()

    def fix_status(self, status=None):                                          # pass in status argument from get_status, if available
        """ pass in status argument from get_status, if available """
        self.inst_sa.fix_status(status)
        return

    # SA-only functions
    def single_trigger(self):                                                   # single trigger
        """ trigger and hold trace (if exists) """
        try:
            self.inst_sa.single_trigger()
        except AttributeError:
            pass
        return

    def cont_trigger(self):                                                     # continuous trigger
        """ enable continuous trigger (if exists) """
        try:
            self.inst_sa.cont_trigger()
        except AttributeError:
            pass
        return

    def enable_marker(self, num):                                               # enable marker1
        """ enable marker1 """
        self.inst_sa.enable_marker(num)
        return

    def set_marker_freq(self, num, freq):                                       # set marker freq (in Hz)
        """ set marker freq (in Hz) """
        self.inst_sa.set_marker_freq(num, freq)
        return

    def set_marker_peak(self, num):                                             # set marker to peak
        """ set marker to peak """
        self.inst_sa.set_marker_peak(num)
        return

    def get_marker_freq(self, num):                                             # get marker freq (in Hz)
        """ get marker freq (in Hz) """
        return self.inst_sa.get_marker_freq(num)

    def get_marker(self, num):                                                  # read value of marker
        """ read value of marker """
        return self.inst_sa.get_marker(num)

    def sa_set_freq(self, freq_Hz):                                             # set center freq (in Hz)
        """ set center freq (in Hz) """
        self.inst_sa.set_freq(freq_Hz)
        return

    def set_span(self, span_Hz):                                                # set span (in Hz)
        """ set span (in Hz) """
        self.inst_sa.set_span(span_Hz)
        return

    def set_atten(self, atten_dB):                                              # set attenuator (in dB)
        """ set attenuator (in dB) """
        self.inst_sa.set_atten(atten_dB)
        return

    def set_rbw(self, rbw_Hz):                                                  # set RBW (in Hz)
        """ set RBW (in Hz) """
        self.inst_sa.set_rbw(rbw_Hz)
        return

    def set_vbw(self, vbw_Hz):                                                  # set VBW (in Hz)
        """ set VBW (in Hz) """
        self.inst_sa.set_vbw(vbw_Hz)
        return

    def set_rlev(self, rlev_dBm):                                               # set RLEV (in dBm)
        """ set RLEV (in dBm) """
        self.inst_sa.set_rlev(rlev_dBm)
        return

    # SG-only functions
    def sg_set_freq(self, freq_Hz):                                             # set freq (in Hz)
        """ set freq (in Hz) """
        self.inst_sg.set_freq(freq_Hz)
        return

    def sg_set_power(self, power_dBm):                                          # set output power (in dBm)
        """ set output power (in dBm) """
        self.inst_sg.set_power(power_dBm)
        return

    def sg_output_on(self):                                                     # enable RF output
        """ enable RF output """
        self.inst_sg.output_on()
        return

    def sg_output_off(self):                                                    # disable RF output
        """ disable RF output """
        self.inst_sg.output_off()
        return

    # SG and SA functions
    def set_freq(self, freq_Hz):                                                # set center freq (in Hz)
        """ set center freq (in Hz) """
        self.inst_sg.set_freq(freq_Hz)
        self.inst_sa.set_freq(freq_Hz)
        return


############################################
# Instrument driver setup
############################################

def query_idn(addr):
    """ query the IDN of the equipment connected at addr """
    inst = scpi.visa_connection()
    if inst.open_resource(addr):
        try:
            timeout_orig = inst.get_timeout()
            inst.set_timeout(TIMEOUT_IDN)                                       # set timeout to TIMEOUT_IDN
            idn = str(inst.query("*IDN?")).upper().split(",")                   # split into manufacturer, model, serial no, firmware ver
            inst.set_timeout(timeout_orig)
        except:
            idn = ["", "", "", ""]                                              # VISA timeout, set to unknown
    else:
        print("ERROR opening resource. Check connection.")
        idn = ["", "", "", ""]                                                  # VISA IO error
    idn = [str.strip(x) for x in idn]                                           # strip leading/trailing spaces for all entries
    return idn


def find_driver(mode, manufacturer, model):
    """ search for driver based on measurement mode and IDN info for mfr/model """

    global driver_list, driver_default_list

    found = False                                                               # flag if driver is found
    inst = []                                                                   # instrument object if driver is found
    default = True                                                              # flag if specific model is not found and using default driver

    # search through known model list
    for x in driver_list:
        # print "checking... " + str(x)
        if fnmatch.fnmatch(mode, x[0]) and fnmatch.fnmatch(manufacturer, x[1]) and fnmatch.fnmatch(model, x[2]):
            print("Found!!")
            print(x)
            inst = x[3]
            found = True
            default = False                                                     # known model was found
            break

    # search through default model list
    if not found:
        for x in driver_default_list:
            # print "checking... " + str(x)
            if fnmatch.fnmatch(mode, x[0]) and fnmatch.fnmatch(manufacturer, x[1]) and fnmatch.fnmatch(model, x[2]):
                print("Found!!")
                print(x)
                inst = x[3]
                found = True
                default = True                                                  # default driver being used
                break

    return found, inst, default


def inst_setup_single(mode, addr):
    """ initialize single equipment (not combo/multiple equipment) """

    if mode.find("NONE") > -1:
        inst = Instrument()                                                     # if "no instrument" mode, use base Instrument class
        inst.open_instrument(['SIMULATION'])                                    # open "SIMULATION" mode

    else:
        # addr should be a list of string(s), if a string is passed in, create a single element list from that string
        if not isinstance(addr, list):
            addr = [addr]

        # query IDN to get equipment Manufacturer/Model
        idn = query_idn(addr[0])
        print("IDN = %s" % idn)
        manufacturer = idn[0]
        model = idn[1]

        # search for driver based on IDN
        (found, inst, default) = find_driver(mode, manufacturer, model)

        if found:
            if addr[0] != "SIMULATION":                                         # else measurement mode uses equipment
                # print WARNING if manufacturer is found but model is not recognized
                if default:
                    print("#######################  !! WARNING !!  #######################")
                    print("##                                                           ##")
                    print("Unable to find %s driver for mfg/model: %s / %s" % (mode, manufacturer, model))
                    print("Using class: " + str(type(inst)))
                    print("##                                                           ##")
                    print("##   Attempting to use DEFAULT driver. If driver works, add  ##")
                    print("##   your equipment model to the White List of recognized    ##")
                    print("##   equipment to remove this WARNING message.               ##")
                    print("###############################################################")
                    print("")
                    six.moves.input("Press ENTER to continue...")
                    print("")
                print("%s CONNECTED: '%s %s'" % (mode, manufacturer, model))

            inst.open_instrument(addr)                                          # open the driver at the specified address
        else:
            print("Driver not found for %s make/model: %s %s" % (mode, manufacturer, model))
            inst = Instrument()
            inst.open_instrument(['SIMULATION'])                                # use simulation mode if driver is not found

    return inst


def inst_setup(mode, addr):
    """ initialize equipment (either combo or single) """
    if mode == 'SG+SA':
        inst_sg = inst_setup_single('SG', [addr[0]])                            # init Sig Gen setup with addr[0]
        inst_sa = inst_setup_single('SA', [addr[1]])                            # init Spec Analyzer setup with addr[1]
        # print "inst_sg.addr = " + str(inst_sg.addr)
        # print "inst_sa.addr = " + str(inst_sg.addr)
        inst = SGSA_Combo(inst_sg, inst_sa)                                     # return SGSA combo object
    else:
        inst = inst_setup_single(mode, addr)                                    # return single equipment setup
    return inst


############################################
# Instrument driver list
############################################

# specific known and tested instrument drivers
driver_list = [
    ['SA',      'KEYSIGHT*',    'N9010*',   SA_Keysight_EXA()],
    ['SA',      'ROHDE*',       'FSW*',     SA_RohdeSchwarz_FSW()],

    ['VNA',     'KEYSIGHT*',    'E8361*',   VNA_Keysight_PNA()],            # Keysight PNA (obsolete)
    ['VNA',     'KEYSIGHT*',    'N524*',    VNA_Keysight_PNA()],            # Keysight PNA-X
    ['VNA',     'KEYSIGHT*',    'N522*',    VNA_Keysight_PNA()],            # Keysight PNA
    ['VNA',     'KEYSIGHT*',    'N523*',    VNA_Keysight_PNA()],            # Keysight PNA-L
    ['VNA',     'KEYSIGHT*',    'M980*',    VNA_Keysight_PNA()],            # Keysight PXI Network Analyzer
    ['VNA',     'ANRITSU*',     'MS464*',   VNA_Anritsu()],                 # Anritsu VectorStar VNA
    ['VNA',     'ANRITSU*',     'MS461*',   VNA_Anritsu()],                 # Anritsu ShockLine VNA
    ['VNA',     'ANRITSU*',     'MS463*',   VNA_Anritsu()],                 # Anritsu ShockLine VNA
    ['VNA',     'ANRITSU*',     'MS465*',   VNA_Anritsu()],                 # Anritsu ShockLine VNA
    ['VNA',     'ANRITSU*',     'ME7868*',  VNA_Anritsu()],                 # Anritsu ShockLine Modular 2-port VNA
    ['VNA',     'ROHDE*',       'ZVA*',     VNA_RohdeSchwarz_ZVA()],        # Rohde & Schwarz ZVA
    ['VNA',     'ROHDE*',       'ZVK*',     VNA_RohdeSchwarz_ZVK()],        # Rohde & Schwarz ZVK
    ['VNA',     'CMT*',         'S*',       VNA_CopperMountain()],          # Copper Mountain VNA
    ['VNA',     'CMT*',         'M*',       VNA_CopperMountain()],          # Copper Mountain VNA
    ['VNA',     'CMT*',         'SC*',      VNA_CopperMountain()],          # Copper Mountain VNA
    ['VNA',     'CMT*',         'C*',       VNA_CopperMountain()],          # Copper Mountain VNA
    ['VNA',     'CMT*',         'PLANAR*',  VNA_CopperMountain()],          # Copper Mountain VNA

    ['SG',      'AGILENT*',     'N5183*',   SG_Keysight_MXG()],
]

# default instrument drivers
driver_default_list = [
    ['SA',      'KEYSIGHT*',    '*',        SA_Keysight_Generic()],
    ['SA',      'AGILENT*',     '*',        SA_Keysight_Generic()],
    ['SA',      'ROHDE*',       '*',        SA_RohdeSchwarz_FSW()],
    ['SA',      '*',            '*',        SA_Generic()],

    ['VNA',     'KEYSIGHT*',    '*',        VNA_Keysight_PNA()],
    ['VNA',     'AGILENT*',     '*',        VNA_Keysight_PNA()],
    ['VNA',     'ROHDE*',       '*',        VNA_RohdeSchwarz_ZVA()],
    ['VNA',     'ANRITSU*',     '*',        VNA_Anritsu()],
    ['VNA',     'CMT*',         '*',        VNA_CopperMountain()],
    ['VNA',     '*',            '*',        VNA_Generic()],

    ['SG',      'KEYSIGHT*',    '*',        SG_Keysight_MXG()],
    ['SG',      'AGILENT*',     '*',        SG_Keysight_MXG()],
    ['SG',      '*',            '*',        SG_Generic()],
]
