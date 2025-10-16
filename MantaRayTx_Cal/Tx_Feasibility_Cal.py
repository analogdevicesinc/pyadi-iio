import adi
import pyvisa
from pyvisa import constants
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
#import additional libraries as needed for instrument code. Testing completed on CXA 
rm = pyvisa.ResourceManager()
import N9000A_Driver as N9000A
import E8267D_Driver as E8267D

CXA = "TCPIP0::192.168.0.77::hislip0::INSTR"
PSG = "TCPIP0::192.168.20.25::inst0::INSTR"

SpecAn = N9000A.N9000A(rm, CXA)
SigGen = E8267D.E8267D(rm, PSG)

######## DEFINE MATLAB PULSESEP and PULSEPERIOD FUNCTIONS ##########

def pulsesep(signal):
    edges = np.where(np.diff(signal.astype(int)) == 1)[0] + 1
    if len(edges) < 2:
        separation = np.array([])
        nextCross = np.array([])
    else:
        separation = np.diff(edges)
        nextCross = edges[1:]
    initialCross = edges[:-1] if len(edges) > 1 else edges
    finalCross = edges[1:] if len(edges) > 1 else edges
    midLev = 0.5
    return separation, initialCross, finalCross, nextCross, midLev

def pulseperiod(signal):
    #Functionally the same as pulse separation for our purposes - if the signal is no longer periodic, will need to add code here to change
    return(pulsesep(signal))

######## END DEFINE MATLAB PULSESEP and PULSEPERIOD FUNCTIONS ##########

SpecAn_Center_Freq = 10e9   #Set to transmit frequency
SpecAn_IQ_BW =  10e6   #Set based upon instrument - testing done at 10MHz (Maximum for CXA used)
SpecAn_Res_BW = 18e3   #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
SpecAn_Dig_IFBW = 10e6   #Set the digital IFBW of Spec An. Tested at 10MHz for both 10 and 20% Duty Cycles
MinCodeVal = 0.00055    #Set to 0.00055 for 20% DC, 0.00031 for 10% DC
NumChannels = 16   #Set to number of channels being used


SpecAn.select_iq_mode()    #Set spec an for complex IQ mode
SpecAn.reset()             #Reset instrument
SpecAn.set_initiate_continuous_sweep('ON') #Set contionuous mode of spec an
SpecAn.set_iq_spec_span(SpecAn_IQ_BW)  #Set IQ bandwidth of instrument
SpecAn.set_iq_spec_bandwidth(SpecAn_Res_BW)    #Set ResBW
SpecAn.set_center_freq(SpecAn_Center_Freq)     #Set SpecAn center frequency
SpecAn.set_iq_mode_bandwidth(SpecAn_Dig_IFBW)  #Set Digital IFBW
SpecAn.bursttrig('POS', -1, 0, -55)    #Set trigger parameters for Spec An. First input is slope, second is delay (uS), third is relative level, last is absolute level
SpecAn.trigger()
SpecAn.wavexscale(0, 4000, 'LEFT', 'OFF')
SpecAn.waveyscale(0, 25, 'CENT', 'ON')

#Set transmitter state to on here

SigGen.set_freq_mhz(SpecAn_Center_Freq/1e6)   #Set Sig Gen frequency to match Spec An
SigGen.set_power_dbm(-48)    #Set Sig Gen power level
SigGen.set_output_state('ON')    #Turn on Sig Gen output
ComplexData = SpecAn.iq_complex_data()
SigGen.set_output_state('OFF')  #Turn off Sig Gen output

#Stop transmitting from Talise

#Separate the I and Q components of the complex data
I = np.real(ComplexData)
Q = np.imag(ComplexData)

#Plot the I and Q waveforms 
plt.figure()
plt.subplot(2, 1, 1)
plt.plot(np.abs(I))
plt.title('I Component')
plt.subplot(2, 1, 2)
plt.plot(np.abs(Q))
plt.title('Q Component')


########### Post Processign Section ############
#Find peaks above threshold
RealPk, _ = find_peaks(np.abs(I), height = MinCodeVal)
ImagPk, _ = find_peaks(np.abs(Q), height = MinCodeVal)

#Select I or Q component of complex data for calibration step
if(len(RealPk) >= len(ImagPk)):
    ProcessArray = I
else:
    ProcessArray = Q

#Align Tx channels 
#Find pulse corresponding to Tx0
if(abs(I[0]) > MinCodeVal or abs(Q[0]) > MinCodeVal or
   abs(I[149]) > MinCodeVal or abs(Q[149]) > MinCodeVal):
    Separation, InitialCross, FinalCross, NextCross, Midlev = pulsesep(
        (np.abs(np.real(ComplexData)) > MinCodeVal).astype(float))
    maxloc = np.argmax(Separation)
    channel0Start = int(np.ceil(NextCross[maxloc]))
else:
    Period, InitialCross, FinalCross, NextCross, Midlev = pulseperiod(
        (np.abs(ProcessArray) > MinCodeVal).astype(float))
    channel0Start = int(np.ceil(InitialCross[0]))

timeZeroAlignedFirstRx = np.roll(ComplexData, -channel0Start)
timeZeroAligned = np.roll(ComplexData, -channel0Start, axis=0)

plt.figure()
plt.plot(np.abs(timeZeroAligned))
plt.title('Zero Aligned Samples')
plt.show()

# Now Determine the Phase Offsets for Each Tx Channel
phaseVals = np.zeros((NumChannels, 1))
for i in range(NumChannels):
    phaseVals[i, 0] = (np.angle(timeZeroAlignedFirstRx[12 + (i*125)]) * (180/np.pi))
print(phaseVals)    