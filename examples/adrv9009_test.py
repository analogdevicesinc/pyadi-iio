import time
 
import adi
import matplotlib.pyplot as plt
import numpy as np
# from scipy import signal
 
#create radio
TaliseSDR = adi.adrv9009_zu11eg(uri="ip:analog.local")
 
#Configure properties
TaliseSDR.rx_enabled_channels = [0, 1, 2, 3]        #Enable all channels for Rx
TaliseSDR.tx_enabled_channels = [0, 1, 2, 3]        #Enable all channels for Tx
#TaliseSDR.rx_sample_rate = 245760000               #Set Rx sample rate
TaliseSDR.trx_lo = 2400000000                       #Set LO to 2.4GHz
TaliseSDR.trx_lo_chip_b = 2400000000                
 
TaliseSDR.tx_hardwaregain_chan0 = -20               #Set tx gain/ attenuation
TaliseSDR.tx_hardwaregain_chan1 = -10
TaliseSDR.tx_hardwaregain_chan0_chip_b = -10
TaliseSDR.tx_hardwaregain_chan1_chip_b = -10
 
TaliseSDR.gain_control_mode_chan0 = "manual"        #Set gain control mode for Rx channels
TaliseSDR.gain_control_mode_chan1 = "manual"        
TaliseSDR.gain_control_mode_chan0_chip_b = "manual"
TaliseSDR.gain_control_mode_chan1_chip_b = "manual"
 
TaliseSDR.rx_hardwaregain_chan0 = 10                #Set Rx hardware gain
TaliseSDR.rx_hardwaregain_chan1 = 10                #Comment out for slow attack mode
TaliseSDR.rx_hardwaregain_chan0_chip_b = 10
TaliseSDR.rx_hardwaregain_chan1_chip_b = 10
 
#Read configured properties
print("TRX LO %s" % (TaliseSDR.trx_lo))
print("TRX LO %s" % (TaliseSDR.trx_lo_chip_b))
 
#print("tx channel gain %s" % (TaliseSDR.tx_hardwaregain_chan0))
#print("tx channel gain %s" % (TaliseSDR.tx_hardwaregain_chan1))
#print("tx channel gain %s" % (TaliseSDR.tx_hardwaregain_chan0_chip_b))
#print("tx channel gain %s" % (TaliseSDR.tx_hardwaregain_chan1_chip_b))
 
#Enable DDS tones
TaliseSDR.dds_enabled = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] #all must be enabled
TaliseSDR.dds_frequencies = [20000000, 0, 20000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
TaliseSDR.dds_scales = [0.5, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
TaliseSDR.dds_phases = [0, 0, 90000, 0, 0, 0, 90000, 0, 0, 0, 0, 0, 0, 0, 0, 0]
 
#Receiver side capture
def measure_phase(chan0, chan1):
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error
 
fsr = int(TaliseSDR.rx_sample_rate)
print("sample rate %s" % (TaliseSDR.rx_sample_rate))
for r in range(20):
    x = TaliseSDR.rx()
    print(measure_phase(x[0], x[1]))
    print(measure_phase(x[0], x[2]))
    f, Pxx_den = signal.periodogram(x[0], fsr)
    f2, Pxx_den2 = signal.periodogram(x[1], fsr)
    f3, Pxx_den3 = signal.periodogram(x[2], fsr)
    f4, Pxx_den4 = signal.periodogram(x[3], fsr)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.semilogy(f2, Pxx_den2)
    plt.semilogy(f3, Pxx_den3)
    plt.semilogy(f4, Pxx_den4)
    plt.ylim([1e-7, 1e4])
    signal.get_window(float, )
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)
 
plt.show()