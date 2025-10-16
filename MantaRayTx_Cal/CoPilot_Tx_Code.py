#Copilot generated code:

import pyvisa
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Initialize VISA resource manager
rm = pyvisa.ResourceManager()

# Connect to instruments
cxa = rm.open_resource('TCPIP0::A-N9000A-30136.local::hislip0::INSTR')
psg = rm.open_resource('TCPIP0::192.169.10.24::inst0::INSTR')

# Set parameters
centerFreq_MHz = 10000
TonePower = -48
IQ_BW = 10
ResBW = 15e3
DigIFBW = 10
numChannels = 4
minCodeValue = 0.00055

# Configure signal generator
psg.write(f'FREQ {centerFreq_MHz}MHz')
psg.write(f'POW {TonePower}dBm')

# Query current frequency
currentFreq_Hz = float(psg.query('FREQ?'))
currentFreq_MHz = currentFreq_Hz / 1e6

# Configure spectrum analyzer
cxa.write(':INST:SEL "IQAnalyzer"')
cxa.write('*RST')
cxa.write(':INIT:CONT ON')
cxa.write(f':SENS:WAV:SPAN {IQ_BW}MHz')
cxa.write(f':SENS:WAV:BAND:RES {ResBW}Hz')
cxa.write(f':SENS:FREQ:CENT {centerFreq_MHz}MHz')
cxa.write(f':SENS:WAV:BAND {DigIFBW}MHz')
cxa.write(':TRIG:SEQ:RFB:SLOP POS')
cxa.write(':TRIG:SEQ:RFB:DEL -1')
cxa.write(':TRIG:SEQ:RFB:LEV -55')
cxa.write(':TRIG:SEQ:RFB:STAT 0')
cxa.write(':INIT:IMM')
cxa.write(':DISP:WAV:Y:SCAL:RLEV 25')
cxa.write(':DISP:WAV:X:SCAL:SPAN 4000')

# Query current power
currentPower_dBm = float(psg.query('POW?'))

# Turn on signal generator and acquire IQ data
psg.write('OUTP ON')
iq_data_str = cxa.query(':READ:WAV:IQ:DATA?')
psg.write('OUTP OFF')

# Convert IQ data string to complex numpy array
iq_data = np.array([complex(val) for val in iq_data_str.strip().split(',')])

# Separate I and Q components
I = np.real(iq_data)
Q = np.imag(iq_data)

# Plot I and Q waveforms
plt.figure()
plt.subplot(2, 1, 1)
plt.plot(np.abs(I))
plt.title('I component')
plt.subplot(2, 1, 2)
plt.plot(np.abs(Q))
plt.title('Q component')
plt.tight_layout()
plt.show()

# Find peaks above threshold
RealPk, _ = find_peaks(np.abs(I), height=minCodeValue)
ImagPk, _ = find_peaks(np.abs(Q), height=minCodeValue)

# Select waveform for calibration
ProcessArray = I if len(RealPk) >= len(ImagPk) else Q

# Determine pulse start location
if (np.abs(I[0]) > minCodeValue or np.abs(Q[0]) > minCodeValue or
    np.abs(I[150]) > minCodeValue or np.abs(Q[150]) > minCodeValue):
    signal_mask = np.abs(I) > minCodeValue
    diff_mask = np.diff(signal_mask.astype(int))
    initialCross = np.where(diff_mask == 1)[0]
    nextCross = np.where(diff_mask == -1)[0]
    separation = nextCross[:len(initialCross)] - initialCross
    maxLoc = np.argmax(separation)
    channel0Start = int(nextCross[maxLoc])
else:
    signal_mask = np.abs(ProcessArray) > minCodeValue
    diff_mask = np.diff(signal_mask.astype(int))
    initialCross = np.where(diff_mask == 1)[0]
    channel0Start = int(initialCross[0])

# Align data
timeZeroAlignedFirstRx = np.roll(iq_data, -channel0Start)
timeZeroAligned = np.roll(iq_data, -channel0Start)

# Plot aligned samples
plt.figure()
plt.plot(np.abs(timeZeroAligned))
plt.title('Zero Aligned Samples')
plt.show()

# Calculate phase offsets
phaseValues = np.zeros((numChannels, 1))
for i in range(numChannels):
    sample_index = 15 + i * 150
    phaseValues[i, 0] = np.angle(timeZeroAlignedFirstRx[sample_index]) * 180 / np.pi

print("Phase Offsets (degrees):")
print(phaseValues)
