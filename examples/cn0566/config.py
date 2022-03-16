# standard config files for the beamformer setups
# This is for use with Pluto (and either 1 or 2 ADAR1000 boards)

SignalFreq = 10.497e9
Rx_freq    = int(2.2e9)
LO_freq    = SignalFreq + Rx_freq       # Frequency to program the ADF4159's VCO to.  It is the external LO of the LTC555x mixers
Tx_freq    = Rx_freq
SampleRate = (1024*2)*1e3
Rx_gain = 1
Tx_gain = 0
Averages = 1
RxGain1 = 127
RxGain2 = 127
RxGain3 = 127
RxGain4 = 127
RxGain5 = 127
RxGain6 = 127
RxGain7 = 127
RxGain8 = 127
Rx1_cal = 0.0 # 47.8125  # you can put phase cal values here (to compensate for phase mismatches in the lines, etc.)
Rx2_cal = 0.0 # 11.25
Rx3_cal = 0.0 # -11.25
Rx4_cal = 0.0 # 0
Rx5_cal = 0.0 # -14.0625
Rx6_cal = 0.0 # -19.6875
Rx7_cal = 0.0 # 30.9375
Rx8_cal = 0.0 # 22.5
refresh_time = 100 # refresh time in ms.  Auto beam sweep will update at this rate.  Too fast makes it hard to adjust the GUI values when sweeping is active
# The ADAR1000 address is set by the address pins on the ADAR1000.  This is set by P10 on the eval board.
# ADDR 00 (BEAM0, 0x00) is set by leaving all jumpers off of P10
# ADDR 01 (BEAM1, 0x20) is set by jumpering pins 4 and 6 on P10
# ADDR 10 (BEAM2, 0x40) is set by jumpering pins 3 and 5 on P10
# ADDR 11 (BEAM3, 0x60) is set by jumpering both 4+6 and 3+5 on P10     
num_ADARs = 2      # Number of ADAR1000's connected -- this can be either 1 or 2. no other values are allowed
num_Rx = 2         # Number of Rx channels (i.e. Pluto this must be 1, but AD9361 SOM this could be 1 or 2)
d = 0.015          # element to element spacing of the antenna
