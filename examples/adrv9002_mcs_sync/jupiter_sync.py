import numpy as np

import matplotlib.pyplot as plt
import matplotlib.animation as animation
#import code
#code.interact(local=locals())
from adrv9002_multi_wrapper import adrv9002_multi_wrapper

# class ReturnableThread(Thread):
#     # This class is a subclass of Thread that allows the thread to return a value.
#     def __init__(self, target):
#         Thread.__init__(self)
#         self.target = target
#         self.result = None

#     def run(self) -> None:
#         self.result = self.target()

# # Set up logging to only show adrv9002_multi logs
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("adi.adrv9002_multi")
# logger.setLevel(logging.DEBUG)
# logger = logging.getLogger("paramiko")
# logger.setLevel(logging.CRITICAL)

# REBOOT = False

# set_dds_upto_dev = (
#     10  # can be used to remove setting DDS to move faster through the testing process
# )

synchrona_ip = "10.48.65.182"
device_ips = [ "10.48.65.190", "10.48.65.166"]#, "191.168.0.4", "191.168.0.5"]
device_ips = [f"ip:{ip}" for ip in device_ips]

# if (len(device_ips) == 1):
#     internal_mcs=True
# else:
#     internal_mcs=False

sdrs = adrv9002_multi_wrapper(
    primary_uri=device_ips[0],
    secondary_uris=device_ips[1:],
    sync_uri=f"ip:{synchrona_ip}",
    enable_ssh=True,
    sshargs={"username": "root", "password": "analog"},
)

# # Reboot all systems
# if REBOOT:
#     print("Rebooting all systems")
#     for dev in [sdrs.primary_ssh] + sdrs.secondaries_ssh:
#         dev._run("reboot")

#     sys.exit(0)

################################################################################
# 1 Configure SDRs
frequency_tx1 = 30000  # 15.360 kHz sinewave to be transmitted
frequency_tx2 = frequency_tx1 * 5 # 153600 Hz = 153.36KHz
num_periods_tx1 = 10
num_periods_tx2 = num_periods_tx1 * 5
amplitude = 2**14 # maximum is (2**15) - 1
lo_freq = 5836000000# Hz

sample_rate_tx1 = sdrs.primary.tx0_sample_rate
print("sample rate ch Tx1: ", sample_rate_tx1)
sample_rate_rx1 = sdrs.primary.rx0_sample_rate
sample_rate_rx2 = sdrs.primary.rx1_sample_rate
print("sample rate ch Rx1: ", sample_rate_rx1)
print("sample rate ch Rx2: ", sample_rate_rx2)
num_samps_tx1 = int((num_periods_tx1*sample_rate_rx1)/frequency_tx1) # number of samples per call to tx() and rx()
num_periods_rx1 = 4
num_samps_rx1 = int((num_periods_rx1*sample_rate_rx1)/frequency_tx1)
print("num_samps_rx1: " + str(num_samps_rx1))

sdrs.gain_control_mode = "spi"

for dev in [sdrs.primary] + sdrs.secondaries:
    # Configuration for all jupiters
    dev.rx_enabled_channels = [0, 1]
    dev.rx_ensm_mode_chan0 = "rf_enabled"
    dev.rx_ensm_mode_chan1 = "rf_enabled"
    dev.rx_buffer_size = num_samps_rx1
    dev.rx_hardwaregain_chan0 = 31
    dev.rx_hardwaregain_chan1 = 31
    dev.rx0_lo = lo_freq
    dev.rx1_lo = lo_freq


for dev in [sdrs.primary]:
    # Configuration for prymary jupiter tx
    dev.tx_enabled_channels = [0]
    dev.tx_cyclic_buffer = True
    dev.tx_hardwaregain_chan0 = 0
    dev.tx_hardwaregain_chan1 = -30
    dev.tx0_lo = lo_freq
    dev._tx_buffer_size = num_samps_tx1

################################################################################
# 2 Prepare data transfer sync

print("Mute DAC data sources")
for dev in [sdrs.primary] + sdrs.secondaries:
    for chan in range(4):
        dev._txdac.reg_write(0x80000418 + chan*0x40, 0x3)

# Calculate time values for Tx1
t1 = np.arange(num_samps_tx1) / sample_rate_tx1
# Generate sinusoidal waveform
phase_shift = -np.pi/2  # Shift by -90 degrees
tx1_samples = amplitude * (np.cos(2 * np.pi * frequency_tx1 * t1 + phase_shift) + 1j*np.sin(2 * np.pi * frequency_tx1 * t1 + phase_shift))

# Calculate Tx1 spectrum in dBFS
tx1_samples_fft = tx1_samples * np.hanning(num_samps_tx1)
ampl_tx = (np.abs(np.fft.fftshift(np.fft.fft(tx1_samples_fft))))
fft_tx1_vals_iq_dbFS = 10*np.log10(np.real(ampl_tx)**2 + np.imag(ampl_tx)**2) + 20*np.log10(2/2**(16-1))\
                                         - 20*np.log10(len(ampl_tx))
f1 = np.linspace(sample_rate_tx1/-2, sample_rate_tx1/2, len(fft_tx1_vals_iq_dbFS))

################################################################################
# 3 Transmit data continuously with primary device
sdrs.tx_primary(tx1_samples)

################################################################################
# 4 Receive and plot data continuously

# Globals
data = {}
captureThread = {}
line = {}
figure_drawn = False
running = True
n_ch = 2
x = list(range(num_samps_rx1))  # Precomputed X axis

ph_err_ch0_minus_ch1_array = [0.0]*20
ph_err_ch0_minus_ch2_array = [0.0]*20
ph_err_ch0_minus_ch3_array = [0.0]*20
ph_err_list_names = ["ph_diff_ch0_dev1_minus_ch1_dev1", "ph_diff_ch0_dev1_minus_ch0_dev2", "ph_diff_ch0_dev1_minus_ch1_dev2"]
x_ph_err = list(range(20))

def on_close(event):
    global running
    running = False
    #sdr.tx_destroy_buffer()
    print("Plot closed, stopping capture.")

# Create the figure and axes
#fig, ax = plt.subplots()
fig, (ax, ax2) = plt.subplots(nrows=2, sharex=False, figsize=(10, 8))
fig.canvas.mpl_connect("close_event", on_close)

# Full screen plot
manager = plt.get_current_fig_manager()
try:
    manager.window.attributes('-zoomed', True)
except AttributeError:
    try:
        manager.window.showMaximized()
    except:
        print("Fullscreen not supported.")
        

for dev in [sdrs.primary] + sdrs.secondaries:
    for i in range(n_ch):
        line[(dev.uri, i)], = ax.plot(x, [0]*num_samps_rx1, label=f"{dev.uri} I ch{i}")
        
# Configure plot
ax.set_xlabel("No. Sample")
ax.set_ylabel("Amplitude [LSB]")
ax.grid(which='both', alpha=0.5)
ax.grid(which='minor', alpha=0.2)
ax.grid(which='major', alpha=0.5)
ax.legend(loc="upper left")        

for list_name in ph_err_list_names:
    line[list_name], = ax2.plot(x_ph_err, [0]*20, label=f"{list_name}")

ax2.set_ylabel("Phase Error [deg]")
ax2.set_xlabel("Measurement Index")
ax2.grid(True)
ax2.legend(loc="upper right")

plt.legend(loc="upper left")
plt.tight_layout()

def measure_phase_degrees(chan0, chan1):
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error

# FuncAnimation update function
def update(frame):
    global data
    if not running:
        return list(line.values())

    print("Update plots")
    # Update plots
    #print(sdrs.rx_custom())
    iq0iq1_data = sdrs.rx_wrapper()
    print(iq0iq1_data)

    a = 0
    for dev in [sdrs.primary] + sdrs.secondaries:
        for i in range(n_ch):
            line[(dev.uri, i)].set_ydata(np.real(iq0iq1_data[a]))
            a = a+1
    ax.relim()
    ax.autoscale_view()
    
    ph_err_ch0_minus_ch1 = measure_phase_degrees(iq0iq1_data[0], iq0iq1_data[1])
    ph_err_ch0_minus_ch2 = measure_phase_degrees(iq0iq1_data[0], iq0iq1_data[2])
    ph_err_ch0_minus_ch3 = measure_phase_degrees(iq0iq1_data[0], iq0iq1_data[3])

    ph_err_ch0_minus_ch1_array.insert(0, ph_err_ch0_minus_ch1) # add element at the beggining of array
    ph_err_ch0_minus_ch2_array.insert(0, ph_err_ch0_minus_ch2)
    ph_err_ch0_minus_ch3_array.insert(0, ph_err_ch0_minus_ch3)
    if (len(ph_err_ch0_minus_ch1_array) >= 20):
        ph_err_ch0_minus_ch1_array.pop()
        ph_err_ch0_minus_ch2_array.pop()
        ph_err_ch0_minus_ch3_array.pop()
    
    line["ph_diff_ch0_dev1_minus_ch1_dev1"].set_ydata(ph_err_ch0_minus_ch1_array)
    line["ph_diff_ch0_dev1_minus_ch0_dev2"].set_ydata(ph_err_ch0_minus_ch2_array)
    line["ph_diff_ch0_dev1_minus_ch1_dev2"].set_ydata(ph_err_ch0_minus_ch3_array)

    ax2.relim()
    ax2.autoscale_view()

    return list(line.values())
    #return list(line.values()) + [ph_line1, ph_line2, ph_line3]

# Create animation (update every 2 seconds)
ani = animation.FuncAnimation(fig, update, interval=500, blit=False)

# Show plot
plt.show()
