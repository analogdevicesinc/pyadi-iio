import adi
import pytest
import test
import numpy as np
import pyvisa

import pyfirmata
import time

# def test_arduino_control():
#     board = pyfirmata.Arduino("COM10", baudrate=57600)

#     board.digital[6].write(1)
#     board.digital[7].write(1)
#     time.sleep(10)

#     value_6 = board.digital[6].read()
#     value_7 = board.digital[7].read()

#     assert value_6 == 1
#     assert value_7 == 1

def set_adjacent_loopback():

    board.digital[4].write(0)
    board.digital[5].write(1)
    board.digital[6].write(0)
    board.digital[7].write(0)
    

def set_combined_loopback():

    board.digital[4].write(1)
    board.digital[5].write(1)
    board.digital[6].write(1)
    board.digital[7].write(0)
    
# Connect to Arduino Uno    
board = pyfirmata.Arduino("COM10", baudrate=57600)

# # Establish VISA control of spectrum analyzer and signal generator
rm = pyvisa.ResourceManager()
x = rm.list_resources()
# # # Spectrum Analyzer
Keysight_N9000A = rm.open_resource('TCPIP0::169.254.41.207::hislip0::INSTR')
HMCT2220 = rm.open_resource('GPIB::00::INSTR')

HMCT2220.write('SOUR:POW 0')


# set_adjacent_loopback()

# Keysight_N9000A.write(':CALC:MARK:MAX')
# Keysight_N9000A.write(':CALC:MARK:Y?')
# peak_power = Keysight_N9000A.read()
# print("Peak power:", peak_power)

# set_combined_loopback()
# time.sleep(5)

# Keysight_N9000A.write(':CALC:MARK:MAX')
# Keysight_N9000A.write(':CALC:MARK:Y?')
# peak_power = Keysight_N9000A.read()
# print("Peak power:", peak_power)

# def test_adjacent_loopback():
#     set_adjacent_loopback()
#     Keysight_N9000A.write(':INIT:CONT OFF')  # Disable continuous sweep
#     Keysight_N9000A.write(':INIT:IMM')       # Initiate a single sweep
#     Keysight_N9000A.write(':CALC:MARK:MAX')
#     Keysight_N9000A.write(':CALC:MARK:Y?')
#     peak_power = Keysight_N9000A.read()
#     print(peak_power)

#     assert int(float(peak_power)) > -30



