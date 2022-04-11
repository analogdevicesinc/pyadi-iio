# standard config files for the beamformer setups
# This is for use with Pluto (and either 1 or 2 ADAR1000 boards)

sdr_address = "ip:192.168.2.1"  # This is the default Pluto address (You can check/change this in the config.txt file on the Pluto "usb drive")
SignalFreq = (
    10.525e9  # if hb100_freq_val.pkl is present then this value will be overwritten
)
Rx_freq = int(2.2e9)
Tx_freq = Rx_freq
SampleRate = (3 * 1024) * 1e3
buffer_size = 1024  # small buffers make the scan faster -- and we're primarily just looking at peak power
Rx_gain = 1
Tx_gain = -10
Averages = 1

# these Rx_cal phase adjustments get added to the phase_cal_val.pkl (if present)
# use them to tweak the auto cal adjusments
# or delete phase_cal_val.pkl and use whatever phase adjustments you want here
Rx1_cal = 0
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

start_lab = "Enable All"
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
