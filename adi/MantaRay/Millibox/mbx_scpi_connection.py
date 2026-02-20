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

import pyvisa                                                                   # use pyVISA for instrument control
import socket                                                                   # raw TCPIP Socket connection


############################################
# Instrument drivers using SCPI commands
############################################

def list_resources():
    """ list all VISA resources """
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()                                             # find list of potential instruments
    resources = list(resources)
    return resources


class SCPIConnection(object):
    """ Abstract class for SCPI connection methods """

    def open_resource(self, addr):
        raise NotImplementedError("open_resource() not implemented")

    def close(self):
        raise NotImplementedError("close() not implemented")

    def write(self, cmd):
        raise NotImplementedError("write() not implemented")

    def read(self):
        raise NotImplementedError("read() not implemented")

    def query(self, cmd):
        raise NotImplementedError("query() not implemented")

    def set_timeout(self, timeout_sec):
        raise NotImplementedError("set_timeout() not implemented")

    def get_timeout(self):
        raise NotImplementedError("get_timeout() not implemented")


class tcpip_socket(SCPIConnection):
    """ Raw TCPIP Socket connection """

    def __init__(self):
        self.session = []
        self.timeout_sec = 2
        self.write_termination = '\n'
        self.read_termination = '\n'

    def open_resource(self, addr):
        self.session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip_port = str(addr).split("::")
        try:
            self.session.connect((ip_port[1], int(ip_port[2])))
            self.session.settimeout(self.timeout_sec)
            port_open = True
        except:
            port_open = False
        return port_open

    def close(self):
        self.session.close()

    def write(self, cmd):
        self.session.send("%s%s" % (str.encode(cmd).strip(), self.write_termination))

    def read(self):
        read1 = self.session.recv(1).decode()
        if read1 == '#':
            read2 = self.read_block_data()
            read_val = read1 + read2
        else:
            read2 = self.read_line()
            read_val = read1 + read2
        return read_val

    def read_line(self):
        read_val = ''
        done = False
        while not done:
            read1 = self.session.recv(1024).decode()
            read_val = read_val + read1
            done = (len(read_val) > 0 and read_val[-1] == self.read_termination)
        return read_val

    def read_block_data(self):

        read_digits_ok = False
        while not read_digits_ok:
            read_digits = self.session.recv(1).decode()
            # print("read_digits = '%s'" % read_digits)
            read_digits_len = len(read_digits)
            if read_digits_len == 1 and read_digits.isdigit():
                read_digits_ok = True
                digits = int(read_digits)

        digits_left = digits
        read_blocksize = ''
        read_blocksize_ok = False
        while not read_blocksize_ok:
            read = self.session.recv(digits_left).decode()
            read_blocksize = read_blocksize + read
            # print("read_blocksize = '%s'" % read_blocksize)
            read_blocksize_len = len(read_blocksize)
            if read_blocksize_len == digits and read_blocksize.isdigit():
                read_blocksize_ok = True
                blocksize = int(read_blocksize)
            elif read_blocksize_len < digits:
                digits_left = digits - read_blocksize_len
            else:
                read_blocksize = ''

        bits_left = blocksize
        result = ''
        get_all_ok = False
        while not get_all_ok:
            read = self.session.recv(bits_left).decode()
            result = result + read
            # print("result = '%s'" % result)
            if len(result) == blocksize:
                get_all_ok = True
            else:
                bits_left = blocksize - len(result)

        last_bit = self.session.recv(1).decode()
        result = result + last_bit

        result_all = read_digits + read_blocksize + result

        return result_all

    def query(self, cmd):
        self.write(cmd)
        return self.read()

    def set_timeout(self, timeout_sec):
        self.timeout_sec = timeout_sec
        self.session.settimeout(self.timeout_sec)

    def get_timeout(self):
        self.timeout_sec = self.session.gettimeout()
        return self.timeout_sec


class visa_connection(SCPIConnection):
    """ VISA connection for VXI-11 or Raw Socket protocols """

    def __init__(self):
        self.session = None
        self.isRawSocket = False
        self.timeout_sec = 2

    def open_resource(self, addr):
        rm = pyvisa.ResourceManager()
        port_open = False
        if addr.upper().find('INSTR') > -1:
            try:
                self.session = rm.open_resource(addr)
                self.session.timeout = self.timeout_sec * 1000
                self.session.write_termination = ''
                self.session.read_termination = ''
                self.isRawSocket = False
                port_open = True
            except:
                print("Failed to initialize VISA VXI-11 session")
                port_open = False
        elif addr.upper().find('SOCKET') > -1:
            try:
                self.session = rm.open_resource(addr)
                self.session.timeout = self.timeout_sec * 1000
                self.session.write_termination = '\n'
                self.session.read_termination = '\n'
                self.isRawSocket = True
                port_open = True
            except:
                print("Failed to initialize VISA SOCKET session")
                port_open = False
        return port_open

    def close(self):
        self.session.close()

    def write(self, cmd):
        self.session.write(cmd)

    def read(self):
        response = ''
        try:
            if not self.isRawSocket:
                response = self.session.read()
            else:
                read1 = self.session.read_bytes(1).decode()
                if read1 == "#":
                    read2 = self.read_block_data()
                    response = read1 + read2
                else:
                    read2 = self.read_line()
                    response = read1 + read2
        except:
            print("Failed to read")
        return response

    def read_line(self):
        response = self.session.read() + self.session.read_termination
        return response

    def read_block_data(self):
        response = ''
        if self.isRawSocket:
            noDigitsStr = self.session.read_bytes(1).decode()
            noDigits = int(noDigitsStr)

            dataSizeStr = self.session.read_bytes(noDigits).decode()
            dataSize = int(dataSizeStr)

            actualDataStr = self.session.read_bytes(dataSize + 1).decode()

            response = noDigitsStr + dataSizeStr + actualDataStr
        else:
            print("read_block_data() is only used for TCPIP Socket connections")
        return response

    def query(self, cmd):
        self.write(cmd)
        return self.read()

    def set_timeout(self, timeout_sec):
        self.timeout_sec = timeout_sec
        self.session.timeout = self.timeout_sec * 1000

    def get_timeout(self):
        self.timeout_sec = self.session.timeout / 1000.0
        return self.timeout_sec
