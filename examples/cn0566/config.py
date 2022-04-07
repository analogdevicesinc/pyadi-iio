# standard config files for the beamformer setups
# This is for use with Pluto (and either 1 or 2 ADAR1000 boards)


sdr_address = "ip:192.168.2.1"  # This is the default Pluto address (You can check/change this in the config.txt file on the Pluto "usb drive")
SignalFreq = 10.525e9
Rx_freq = int(2.2e9)
LO_freq = (
    SignalFreq + Rx_freq
)  # Frequency to program the ADF4159's VCO to.  It is the external LO of the LTC555x mixers
Tx_freq = Rx_freq
SampleRate = (1024 * 3) * 1e3
buffer_size = 1024  # small buffers make the scan faster -- and we're primarily just looking at peak power
Rx_gain = 1
Tx_gain = -10
Averages = 1
if True:
    Rx1_cal = 30.9
    Rx2_cal = 25.3
    Rx3_cal = -8.4
    Rx4_cal = 0
    Rx5_cal = 16.9
    Rx6_cal = 14.1
    Rx7_cal = 16.9
    Rx8_cal = 33.8
else:
    Rx1_cal = 0  # you can put phase cal values here (to compensate for phase mismatches in the lines, etc.)
    Rx2_cal = 0
    Rx3_cal = 0
    Rx4_cal = 0
    Rx5_cal = 0
    Rx6_cal = 0
    Rx7_cal = 0
    Rx8_cal = 0

refresh_time = 100  # refresh time in ms.  Auto beam sweep will update at this rate.  Too fast makes it hard to adjust the GUI values when sweeping is active
d = 0.014  # element to element spacing of the antenna
use_tx = False  # Enable TX path if True (if false, HB100 source)

start_lab = "Lab 1: Steering Angle"
#  Lab choices are:
#           "Lab 1: Steering Angle",
#           "Lab 2: Array Factor",
#           "Lab 3: Tapering",
#           "Lab 4: Grating Lobes",
#           "Lab 5: Beam Squint",
#           "Lab 6: Quantization",
#           "Lab 7: Hybrid Control",
#           "Lab 8: Monopulse Tracking",
#           "Enable All"
