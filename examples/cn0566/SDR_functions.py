# SDR_functions.py 
# These are Pluto control functions

import time
import sys
import numpy as np

import adi
from ADAR_pyadi_functions import *   #import the ADAR1000 write functions (like ADAR_init and writeBeam functions)

def SDR_LO_init(rpi_address = None, LO_freq = 12000000000):   #program the ADF4159 to be the LO of the external LTC555x mixers
    pll = adi.adf4159(uri=rpi_address)
    output_freq = int(LO_freq)
    pll.frequency = int(output_freq/4) # Output frequency divided by 4
    BW = 500e6 / 4
    num_steps = 1000
    pll.freq_dev_range = int(BW) # frequency deviation range in Hz.  This is the total freq deviation of the complete freq ramp
    pll.freq_dev_step = int(BW/num_steps) # frequency deviation step in Hz.  This is fDEV, in Hz.  Can be positive or negative
    pll.freq_dev_time = int(1e3) # total time (in us) of the complete frequency ramp
    pll.ramp_mode = "disabled"     # ramp_mode can be:  "disabled", "continuous_sawtooth", "continuous_triangular", "single_sawtooth_burst", "single_ramp_burst"
    pll.delay_word = 4095     # 12 bit delay word.  4095*PFD = 40.95 us.  For sawtooth ramps, this is also the length of the Ramp_complete signal
    pll.delay_clk = 'PFD'     # can be 'PFD' or 'PFD*CLK1'
    pll.delay_start_en = 0         # delay start
    pll.ramp_delay_en = 0          # delay between ramps.  
    pll.trig_delay_en = 0          # triangle delay
    pll.sing_ful_tri = 0           # full triangle enable/disable -- this is used with the single_ramp_burst mode 
    pll.tx_trig_en = 0             # start a ramp with TXdata
    #pll.clk1_value = 100
    #pll.phase_value = 3
    pll.enable = 0                 # 0 = PLL enable.  Write this last to update all the registers

def SDR_init(sdr_address, NumRx, SampleRate, TX_freq, RX_freq, Rx_gain, Tx_gain):
    '''Setup contexts'''
    if NumRx==1:  # 1 Rx, so this is Pluto
        #sdr=adi.Pluto()     #This finds pluto over usb.  But communicating with its ip address gives us more flexibility
        sdr=adi.Pluto(uri=sdr_address)      #This finds the device at that ip address
    if NumRx==2:  # 2 Rx, so this is the ADRV9361-SOM or Pluto Rev C (with 2 Rx and 2 Tx enabled)
        sdr = adi.ad9361(uri=sdr_address)
        sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "1"  # move to fdd mode.  see https://github.com/analogdevicesinc/pyadi-iio/blob/ensm-example/examples/ad9361_advanced_ensm.py
        sdr._ctrl.debug_attrs["adi,ensm-enable-txnrx-control-enable"].value = "0"       # Disable pin control so spi can move the states
        sdr._ctrl.debug_attrs["initialize"].value = "1"
        sdr.rx_enabled_channels = [0, 1]   # enable Rx1 (voltage0) and Rx2 (voltage1)
        sdr.gain_control_mode_chan0 = 'manual'      #We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
        sdr.gain_control_mode_chan1 = 'manual'      #We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
    sdr._rxadc.set_kernel_buffers_count(1)   #Default is 4 Rx buffers are stored, but we want to change and immediately measure the result, so buffers=1
    rx = sdr._ctrl.find_channel('voltage0') 
    rx.attrs['quadrature_tracking_en'].value = '1'   # set to '1' to enable quadrature tracking
    sdr.sample_rate = int(SampleRate)
    sdr.rx_lo = int(RX_freq)
    #sdr.filter = "/home/pi/Documents/PlutoFilters/samprate_40p0.ftr"  #pyadi-iio auto applies filters based on sample rate
    #sdr.rx_rf_bandwidth = int(40e6)
    #sdr.tx_rf_bandwidth = int(1e6)
    sdr.rx_buffer_size = int(1*256)  # small buffers make the scan faster -- and we're primarily just looking at peak power
    sdr.tx_lo = int(TX_freq)
    sdr.tx_cyclic_buffer = False
    #sdr.tx_buffer_size = int(2**16)
    if NumRx==1:
        sdr.tx_hardwaregain_chan0 = int(Tx_gain)  # this is a negative number between 0 and -88
        sdr.gain_control_mode_chan0 = "manual"                #We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
        sdr.rx_hardwaregain_chan0 = int(Rx_gain)
    if NumRx==2:
        sdr.tx_hardwaregain_chan0 = int(-80)   # We don't use Tx1, so just make it is off or attenuated
        sdr.tx_hardwaregain_chan1 = int(Tx_gain)
        sdr.rx_hardwaregain_chan0 = int(Rx_gain)
        sdr.rx_hardwaregain_chan1 = int(Rx_gain)
    if True:   # use either DDS or sdr.tx(iq) to generate the Tx waveform.  But don't do both!  
        sdr.dds_enabled = [1, 1, 1, 1, 1, 1, 1, 1]                  #DDS generator enable state
        sdr.dds_frequencies = [0.5e6, 0, 0.5e6, 0, 0.5e6, 0, 0.5e6, 0]      #Frequencies of DDSs in Hz
        sdr.dds_scales = [0.1, 0, 0.1, 0, 1, 0, 1, 0]                   #Scale of DDS signal generators Ranges [0,1]
    if False:
        signal_freq = 0.5e6
        fs = int(SampleRate)
        N = 1000
        fc = int(signal_freq / (fs / N)) * (fs / N)
        ts = 1 / float(fs)
        t = np.arange(0, N * ts, ts)
        i = np.cos(2 * np.pi * t * fc) * 2 ** 15
        q = np.sin(2 * np.pi * t * fc) * 2 ** 15
        iq = 0.9 * (i + 1j * q)
        sdr.tx([iq*0.1, iq])
    return sdr

def SDR_setRx(sdr, NumRx, RX_freq, Rx_gain):
    sdr.rx_lo = int(RX_freq)
    sdr.tx_lo = int(RX_freq)
    if NumRx==1:
        sdr.rx_hardwaregain_chan0 = int(Rx_gain)
    if NumRx==2:
        sdr.rx_hardwaregain_chan0 = int(Rx_gain)
        sdr.rx_hardwaregain_chan1 = int(Rx_gain)

def SDR_getData(sdr):
    data=sdr.rx()          #read a buffer of data from Pluto using pyadi-iio library (adi.py)
    return data

def SDR_TxBuffer_Destroy(sdr):
    if sdr.tx_cyclic_buffer == True:
        sdr.tx_destroy_buffer()

def SDR_get_dBFS(sdr, Averages, num_Rx):
    # Get signal level from Pluto and return dBFS measurement
    total=0
    for count in range (0, Averages):
        data_raw=SDR_getData(sdr)
        data = data_raw
        NumSamples = len(data)          #number of samples
        win = np.blackman(NumSamples)
        y = data * win
        sp = np.absolute(np.fft.fft(y))
        sp = sp[1:-1]
        sp = np.fft.fftshift(sp)
        s_mag = np.abs(sp) * 2 / np.sum(win)    # Scale FFT by window and /2 since we are using half the FFT spectrum
        s_mag = np.maximum(s_mag, 10**(-15))
        s_dbfs = 20*np.log10(s_mag/(2**12))     # Pluto is a 12 bit ADC, so use that to convert to dBFS
        total=total+max(s_dbfs)   # sum up all the loops, then we'll average
    PeakValue=total/Averages
    return PeakValue

