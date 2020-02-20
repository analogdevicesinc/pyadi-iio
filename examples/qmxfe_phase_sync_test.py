import adi
import time
import sys
from datetime import datetime
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np
import scipy.io as sio
from scipy.io import loadmat
import matplotlib
#matplotlib.use("Qt5Agg")

def measure_phase_and_delay(chan0, chan1, window=None):
    assert len(chan0) == len(chan1)
    if window==None:
        window = len(chan0)
    phases = []
    delays = []
    indx = 0
    sections = len(chan0)//window
    for sec in range(sections):
        chan0_tmp = chan0[indx:indx+window]
        chan1_tmp = chan1[indx:indx+window]
        indx = indx+window+1
        cor = np.correlate(chan0_tmp, chan1_tmp, "full")
        # plt.plot(np.real(cor))
        # plt.plot(np.imag(cor))
        # plt.plot(np.abs(cor))
        # plt.show()
        i = np.argmax(np.abs(cor))
        m = cor[i]
        sample_delay = len(chan0_tmp) - i - 1
        phases.append(np.angle(m)*180/np.pi)
        delays.append(sample_delay)
    return (np.mean(phases), np.mean(delays))

def measure_phase(chan0, chan1):
    assert len(chan0) == len(chan1)
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error

def sub_phases(x, y):
    return ([e1-e2 for (e1, e2) in zip(x, y)])

def measure_and_adjust_phase_offset(chan0, chan1, phase_correction):
    assert len(chan0) == len(chan1)
    (p, s) = measure_phase_and_delay(chan0, chan1)
    #print("Across Chips Sample delay: ",s)
    #print("Phase delay: ",p,"(Degrees)")
    #print(phase_correction)
    return (sub_phases(phase_correction, [int(p*1000)]*4), s)

def multichip_sync_all(value):
    global dev
    dev.multichip_sync_a = value
    dev.multichip_sync_b = value
    dev.multichip_sync_c = value
    dev.multichip_sync_d = value

def multichip_sync_all_rev(value):
    global dev
    dev.multichip_sync_d = value
    dev.multichip_sync_c = value
    dev.multichip_sync_b = value
    dev.multichip_sync_a = value

def write_reg_all(reg, val):
    global dev
    dev._rxadc3.reg_write(reg, val)
    dev._rxadc2.reg_write(reg, val)
    dev._rxadc1.reg_write(reg, val)
    dev._rxadc0.reg_write(reg, val)

def relink_resync_all():
    global dev
    write_reg_all(0x205, 0)
    multichip_sync_all(0)
    multichip_sync_all(2)
    multichip_sync_all(1)
    multichip_sync_all_rev(3)
    multichip_sync_all(4)
    multichip_sync_all(5)
    time.sleep(2)

def regdump_hmc7043():
    for i in range(0x153):
        print (hex(i)+", "+hex(dev._clock_chip.reg_read(i)))

def regdump_adf4371():
    for i in range(0x7d):
        print (hex(i)+", "+hex(dev._pll0.reg_read(i)))

param_1= sys.argv[1]
print("--Connecting to device ip:", param_1)
dev = adi.QuadMxFE(uri=str('ip:'+param_1))

#dev._clock_chip.attrs['reset_dividers_request'].value="1"

# Configure properties
print("--Setting up chip")

# Set NCOs
dev.rx_channel_nco_frequencies_chip_a = [0]*4
dev.rx_channel_nco_frequencies_chip_b = [0]*4
dev.rx_channel_nco_frequencies_chip_c = [0]*4
dev.rx_channel_nco_frequencies_chip_d = [0]*4

dev.tx_channel_nco_frequencies_chip_a = [0]*4
dev.tx_channel_nco_frequencies_chip_b = [0]*4
dev.tx_channel_nco_frequencies_chip_c = [0]*4
dev.tx_channel_nco_frequencies_chip_d = [0]*4

dev.tx_main_nco_frequencies_chip_a = [3000000000]*4
dev.tx_main_nco_frequencies_chip_b = [3000000000]*4
dev.tx_main_nco_frequencies_chip_c = [3000000000]*4
dev.tx_main_nco_frequencies_chip_d = [3000000000]*4

dev.rx_channel_nco_phases_chip_a = [0]*4
dev.rx_channel_nco_phases_chip_b = [0]*4
dev.rx_channel_nco_phases_chip_c = [0]*4
dev.rx_channel_nco_phases_chip_d = [0]*4

dev.external_hardwaregain = -20

dev.rx_enabled_channels = [0, 4, 8, 12]
dev.tx_enabled_channels = [31]
dev.rx_buffer_size = 2**15

nf = loadmat('/home/michael/devel/pyadi-iio/noise.mat')
noise = nf['dataC']
m = np.max(np.abs(noise))
noise = noise/m * 2**15 * 0.9
# Force singleton shape
noise = noise.reshape(len(noise))

dev.tx_cyclic_buffer = True
dev.tx(noise)

# Collect data
fsr = int(dev.rx_sampling_frequency)

phases_a = []
phases_b = []
phases_c = []
phases_d = []

so_a = []
so_b = []
so_c = []
so_d = []

run_plot = False
count=20

for i in range(count):
    relink_resync_all()
    time.sleep(2)

    for r in range(3):
        # Collect data
        x = dev.rx()

        if (run_plot == True and r == 0):
            phase_b = str(dev.rx_channel_nco_phases_chip_b[0]/1000)+"°"
            phase_c = str(dev.rx_channel_nco_phases_chip_c[0]/1000)+"°"
            phase_d = str(dev.rx_channel_nco_phases_chip_d[0]/1000)+"°"
            plt.xlim(0, 100)
            plt.plot(np.real(x[0]), label='(1) reference', alpha=0.7)
            plt.plot(np.real(x[1]), label="(2) phase "+phase_b, alpha=0.7)
            plt.plot(np.real(x[2]), label="(3) phase "+phase_c, alpha=0.7)
            plt.plot(np.real(x[3]), label="(4) phase "+phase_d, alpha=0.7)
            plt.legend()
            plt.title("Quad MxFE Phase Sync @ "+str(fsr/1000000)+" MSPS")
            plt.show()
            print("FYI: Close figure to do next capture")


        dev.rx_channel_nco_phases_chip_b, s_b = measure_and_adjust_phase_offset(x[0], x[1], dev.rx_channel_nco_phases_chip_b)
        dev.rx_channel_nco_phases_chip_c, s_c = measure_and_adjust_phase_offset(x[0], x[2], dev.rx_channel_nco_phases_chip_c)
        dev.rx_channel_nco_phases_chip_d, s_d = measure_and_adjust_phase_offset(x[0], x[3], dev.rx_channel_nco_phases_chip_d)

        phase_b = str(dev.rx_channel_nco_phases_chip_b[0]/1000)+"°; "+str(int(s_b))
        phase_c = str(dev.rx_channel_nco_phases_chip_c[0]/1000)+"°; "+str(int(s_c))
        phase_d = str(dev.rx_channel_nco_phases_chip_d[0]/1000)+"°; "+str(int(s_d))

        if (r == 2):
            phases_a.insert(i, dev.rx_channel_nco_phases_chip_a[0]/1000)
            phases_b.insert(i, dev.rx_channel_nco_phases_chip_b[0]/1000)
            phases_c.insert(i, dev.rx_channel_nco_phases_chip_c[0]/1000)
            phases_d.insert(i, dev.rx_channel_nco_phases_chip_d[0]/1000)
            so_a.insert(i, 0)
            so_b.insert(i, s_b)
            so_c.insert(i, s_c)
            so_d.insert(i, s_d)

        result = datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"\t"+phase_b+"\t\t"+phase_c+"\t\t"+phase_d+"\n"

        print(result)

        with open("test.txt", "a") as myfile:
            myfile.write(result)

        print(r)

        if (run_plot == True and r == 2):
            plt.xlim(0, 100)
            plt.plot(np.real(x[0]), label='(1) reference', alpha=0.7)
            plt.plot(np.real(x[1]), label="(2) phase "+phase_b, alpha=0.7)
            plt.plot(np.real(x[2]), label="(3) phase "+phase_c, alpha=0.7)
            plt.plot(np.real(x[3]), label="(4) phase "+phase_d, alpha=0.7)
            plt.legend()
            plt.title("Quad MxFE Phase Sync @ "+str(fsr/1000000)+" MSPS")
            plt.show()
            print("FYI: Close figure to do next capture")

        dev.rx_destroy_buffer()

if (True):
    fig, axs = plt.subplots(2)
    plt.xlim(0, count)
    axs[0].plot(phases_a, label="(1) MxFE0 phase", alpha=0.7)
    axs[0].plot(phases_b, label="(2) MxFE1 phase", alpha=0.7)
    axs[0].plot(phases_c, label="(3) MxFE2 phase", alpha=0.7)
    axs[0].plot(phases_d, label="(4) MxFE3 phase", alpha=0.7)

    axs[0].set_ylabel('Phase')
    axs[0].set_xlabel('Resync#')

    axs[1].plot(so_a, label="(1) MxFE0 Samp. Offset", alpha=0.7)
    axs[1].plot(so_b, label="(2) MxFE1 Samp. Offset", alpha=0.7)
    axs[1].plot(so_c, label="(3) MxFE2 Samp. Offset", alpha=0.7)
    axs[1].plot(so_d, label="(4) MxFE3 Samp. Offset", alpha=0.7)

    axs[1].set_ylim([-4, 4])
    axs[1].set_xlabel('Resync#')
    axs[1].set_ylabel('Sample Offset')

    fig.legend()
    fig.suptitle("Quad MxFE Phase Sync @ "+str(fsr/1000000)+" MSPS")
    plt.show()
    print("FYI: Close figure to do next capture")

input("Press Enter to exit...")
