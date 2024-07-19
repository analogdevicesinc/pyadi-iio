
import pytest

import numpy as np
import pyvisa

import pyfirmata
import time


# # Connect to Arduino Uno    
## Note: if first time installing pyfirmata, need to replace "getargspec" with "getfullargspec" in pyfirmata code
# board = pyfirmata.Arduino("/dev/ttyACM0", baudrate=57600)

# # Establish VISA control of spectrum analyzer and signal generator
rm = pyvisa.ResourceManager()
x = rm.list_resources()
HMCT2220 = rm.open_resource('ASRL/dev/ttyACM1::INSTR')
FieldFox = rm.open_resource('TCPIP::192.168.100.23::INSTR')

###################################
### Cal Board Control Functions ###
###################################

def _set_adjacent_loopback():

    board.digital[4].write(0)
    board.digital[5].write(1)
    board.digital[6].write(0)
    board.digital[7].write(0)
    

def _set_combined_loopback():

    board.digital[4].write(1)
    board.digital[5].write(1)
    board.digital[6].write(1)
    board.digital[7].write(0)

def _set_SMA_inout():
    board.digital[4].write(0)
    board.digital[5].write(1)
    board.digital[6].write(1)
    board.digital[7].write(1)

def _set_state(state):
    if state == "adjacent_loopback":
        _set_adjacent_loopback()
    if state == 'combined_loopback':
        _set_combined_loopback()


#######################################
### HMCT2220 SCPI Functions ###
#######################################

# Sets frequency of sig gen in MHz
def _set_frequency_MHz(freq, instr):
    instr.write('FREQ {} MHz'.format(freq))

# Sets power level of sig gen in dBm
def _set_power_level_dBm(power_level, instr):
    instr.write('SOUR:POW {}'.format(power_level))

# Sets output state ON or OFF
def _set_output(state, instr):
    instr.write('OUTP {}'.format(state))

########################################
### FieldFox SCPI Functions ###
########################################
    
def _set_mode(mode, instr):
    instr.write('INST:SEL "{}"'.format(mode))
    
def _set_span_MHz(span, instr):
    instr.write('SENSE:FREQ:SPAN {} MHz'.format(span))

def _set_center_freq_MHz(center_freq, instr):
    instr.write('FREQ:CENT {} MHz'.format(center_freq))

def _res_bandwidth_auto(state, instr):
    instr.write('BAND:AUTO {}'.format(state))

def _set_res_bandwidth(res_bandwidth, instr):
    instr.write('BAND {} MHz'.format(res_bandwidth))

def _set_marker_to_peak(marker_number, instr):
    instr.write('CALC:MARK{}:FUNC:MAX'.format(marker_number))

def _get_peak_power_level(marker_number, instr):
    x = instr.query('CALC:MARK{}:Y?'.format(marker_number))
    return x

def _set_attenuation_level(attenuation, instr):
    instr.write('POW:ATT {}'.format(attenuation))

############################################
### Adjacent and Combined loopback tests ###
############################################

@pytest.mark.parametrize("frequency", [8000, 9000, 10000, 11000, 12000], ids=lambda x: f"Frequency (MHz):{x}")
@pytest.mark.parametrize("cal_board_state", ["adjacent_loopback", "combined_loopback"])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], ids=lambda x: f"channel:{x}")
# @pytest.mark.parametrize("channel", [0])

def test_loopback(channel, cal_board_state, frequency):

    if (cal_board_state == "adjacent_loopback" and frequency == 8000):
        input('\n\nConnect signal generator into channel {} input and connect spectrum analyzer into channel {} output.  Press Enter when complete '.format(channel, channel))
        _set_adjacent_loopback()

    if cal_board_state == "combined_loopback":
        _set_combined_loopback()

    # Set up signal generator
    _set_frequency_MHz(frequency, HMCT2220)  # Set frequency of sig gen
    _set_power_level_dBm(15, HMCT2220) # Set sig gen power level to 10 dBm
    _set_output('ON', HMCT2220) # Set sig gen output on

    time.sleep(1) # Buffer time of 1 second

    # Set up spectrum analyzer
    _set_mode('SA', FieldFox)  # Select spectrum analyzer mode for FieldFox
    _set_attenuation_level(0, FieldFox) # Set attenuation level to 0 dB
    _set_center_freq_MHz(10000, FieldFox) # Set center frequency to 10 GHz
    _set_span_MHz(20000, FieldFox) # Set span to 20 GHz
    _set_res_bandwidth(1, FieldFox) # Sets resolution bandwidth to 1 MHz
    time.sleep(1) # Buffer time of 1 second
    _set_marker_to_peak(1, FieldFox) # Sets marker 1 to peak
    peak_power = _get_peak_power_level(1, FieldFox) # Gets the power at marker 1
    print("\n\nPower level (dBm): {}".format(peak_power))



    if cal_board_state == "adjacent_loopback":
        assert int(float(peak_power)) > -20
    if cal_board_state == "combined_loopback":
        assert int(float(peak_power)) > -65

###################################
### Tx Combined SMA Output Test ###
###################################

@pytest.mark.parametrize("frequency", [8000, 9000, 10000, 11000, 12000], ids=lambda x: f"Frequency (MHz):{x}")
def test_tx_combined_out(frequency):

    # Combined Tx Out test
    if (frequency == 8000):
        input('\n\nConnect signal generator into channel 0 input.  Connect spectrum analyzer to the combined Tx out SMA port on top of the board.  Press enter when complete')
        _set_SMA_inout()

    # Set up signal generator
    _set_frequency_MHz(frequency, HMCT2220)  # Set frequency of sig gen
    _set_power_level_dBm(15, HMCT2220) # Set sig gen power level to 10 dBm
    _set_output('ON', HMCT2220) # Set sig gen output on
    time.sleep(1) # Buffer time of 1 second

    # Set up spectrum analyzer
    _set_mode('SA', FieldFox)  # Select spectrum analyzer mode for FieldFox
    _set_attenuation_level(0, FieldFox) # Set attenuation level to 0 dB
    _set_center_freq_MHz(10000, FieldFox) # Set center frequency to 10 GHz
    _set_span_MHz(20000, FieldFox) # Set span to 20 GHz
    _set_res_bandwidth(1, FieldFox) # Sets resolution bandwidth to 1 MHz
    time.sleep(1) # Buffer time of 1 second
    _set_marker_to_peak(1, FieldFox) # Sets marker 1 to peak
    peak_power = _get_peak_power_level(1, FieldFox) # Gets the power at marker 1
    print("\n\nPower level (dBm): {}".format(peak_power))

    assert int(float(peak_power)) > -40


##################################
### Rx Combined SMA Input Test ###
##################################

@pytest.mark.parametrize("frequency", [8000, 9000, 10000, 11000, 12000], ids=lambda x: f"Frequency (MHz):{x}")
def test_rx_combined_in(frequency):

    # Combined Rx In test
    if (frequency == 8000):
        input('\n\nConnect signal generator into Rx SMA input on top of the board.  Connect spectrum analyzer into channel 0 output.  Press enter when complete')
        _set_SMA_inout()    


    # Set up signal generator
    _set_frequency_MHz(frequency, HMCT2220)  # Set frequency of sig gen
    _set_power_level_dBm(15, HMCT2220) # Set sig gen power level to 10 dBm
    _set_output('ON', HMCT2220) # Set sig gen output on
    time.sleep(1) # Buffer time of 1 second

    # Set up spectrum analyzer
    _set_mode('SA', FieldFox)  # Select spectrum analyzer mode for FieldFox
    _set_attenuation_level(0, FieldFox) # Set attenuation level to 0 dB
    _set_center_freq_MHz(10000, FieldFox) # Set center frequency to 10 GHz
    _set_span_MHz(20000, FieldFox) # Set span to 20 GHz
    _set_res_bandwidth(1, FieldFox) # Sets resolution bandwidth to 1 MHz
    time.sleep(1) # Buffer time of 1 second
    _set_marker_to_peak(1, FieldFox) # Sets marker 1 to peak
    peak_power = _get_peak_power_level(1, FieldFox) # Gets the power at marker 1
    print("\n\nPower level (dBm): {}".format(peak_power))

    assert int(float(peak_power)) > -40
