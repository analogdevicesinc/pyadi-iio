# SDR_functions.py
# These are Pluto control functions

import pickle
import sys
import time

import adi
import numpy as np


# MWT: Add uri argument...
def SDR_LO_init(
    uri, LO_freq
):  # program the ADF4159 to be the LO of the external LTC555x mixers
    pll = adi.adf4159(uri)
    output_freq = int(LO_freq)
    pll.frequency = int(output_freq / 4)  # Output frequency divided by 4
    BW = 500e6 / 4
    num_steps = 1000
    pll.freq_dev_range = int(
        BW
    )  # frequency deviation range in Hz.  This is the total freq deviation of the complete freq ramp
    pll.freq_dev_step = int(
        BW / num_steps
    )  # frequency deviation step in Hz.  This is fDEV, in Hz.  Can be positive or negative
    pll.freq_dev_time = int(1e3)  # total time (in us) of the complete frequency ramp
    pll.ramp_mode = "disabled"  # ramp_mode can be:  "disabled", "continuous_sawtooth", "continuous_triangular", "single_sawtooth_burst", "single_ramp_burst"
    pll.delay_word = 4095  # 12 bit delay word.  4095*PFD = 40.95 us.  For sawtooth ramps, this is also the length of the Ramp_complete signal
    pll.delay_clk = "PFD"  # can be 'PFD' or 'PFD*CLK1'
    pll.delay_start_en = 0  # delay start
    pll.ramp_delay_en = 0  # delay between ramps.
    pll.trig_delay_en = 0  # triangle delay
    pll.sing_ful_tri = 0  # full triangle enable/disable -- this is used with the single_ramp_burst mode
    pll.tx_trig_en = 0  # start a ramp with TXdata
    # pll.clk1_value = 100
    # pll.phase_value = 3
    pll.enable = 0  # 0 = PLL enable.  Write this last to update all the registers


def SDR_init(sdr_address, SampleRate, TX_freq, RX_freq, Rx_gain, Tx_gain, buffer_size):
    """Setup contexts"""
    sdr = adi.ad9361(uri=sdr_address)
    sdr._ctrl.debug_attrs[
        "adi,frequency-division-duplex-mode-enable"
    ].value = "1"  # set to fdd mode
    sdr._ctrl.debug_attrs[
        "adi,ensm-enable-txnrx-control-enable"
    ].value = "0"  # Disable pin control so spi can move the states
    sdr._ctrl.debug_attrs["initialize"].value = "1"
    sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
    sdr.gain_control_mode_chan0 = "manual"  # We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
    sdr.gain_control_mode_chan1 = "manual"  # We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
    sdr._rxadc.set_kernel_buffers_count(
        1
    )  # Default is 4 Rx buffers are stored, but we want to change and immediately measure the result, so buffers=1
    rx = sdr._ctrl.find_channel("voltage0")
    rx.attrs[
        "quadrature_tracking_en"
    ].value = "1"  # set to '1' to enable quadrature tracking
    sdr.sample_rate = int(SampleRate)
    sdr.rx_lo = int(RX_freq)
    sdr.rx_buffer_size = int(
        buffer_size
    )  # small buffers make the scan faster -- and we're primarily just looking at peak power
    sdr.tx_lo = int(TX_freq)
    sdr.tx_cyclic_buffer = True
    sdr.tx_hardwaregain_chan0 = int(-80)  # turn off Tx1
    sdr.tx_hardwaregain_chan1 = int(Tx_gain)
    sdr.rx_hardwaregain_chan0 = int(Rx_gain + ccal[0])
    sdr.rx_hardwaregain_chan1 = int(Rx_gain + ccal[1])
    # sdr.filter = "/usr/local/lib/osc/filters/LTE5_MHz.ftr"
    # sdr.rx_rf_bandwidth = int(SampleRate*2)
    # sdr.tx_rf_bandwidth = int(SampleRate*2)
    signal_freq = int(SampleRate / 8)
    if (
        True
    ):  # use either DDS or sdr.tx(iq) to generate the Tx waveform.  But don't do both!
        sdr.dds_enabled = [1, 1, 1, 1, 1, 1, 1, 1]  # DDS generator enable state
        sdr.dds_frequencies = [
            signal_freq,
            0,
            signal_freq,
            0,
            signal_freq,
            0,
            signal_freq,
            0,
        ]  # Frequencies of DDSs in Hz
        sdr.dds_scales = [
            0.5,
            0,
            0.5,
            0,
            0.9,
            0,
            0.9,
            0,
        ]  # Scale of DDS signal generators Ranges [0,1]
    else:
        fs = int(SampleRate)
        N = 1000
        fc = int(signal_freq / (fs / N)) * (fs / N)
        ts = 1 / float(fs)
        t = np.arange(0, N * ts, ts)
        i = np.cos(2 * np.pi * t * fc) * 2 ** 15
        q = np.sin(2 * np.pi * t * fc) * 2 ** 15
        iq = 0.9 * (i + 1j * q)
        sdr.tx([iq, iq])
    return sdr


def SDR_setRx(sdr, Rx1_gain, Rx2_gain):
    sdr.rx_hardwaregain_chan0 = int(Rx1_gain + ccal[0])
    sdr.rx_hardwaregain_chan1 = int(Rx2_gain + ccal[1])


def SDR_setTx(sdr, Tx_gain):
    sdr.tx_hardwaregain_chan0 = int(-80)  # turn off Tx1
    sdr.tx_hardwaregain_chan1 = int(Tx_gain)


def SDR_getData(sdr):
    data = sdr.rx()  # read a buffer of data from Pluto using pyadi-iio library (adi.py)
    return data


def SDR_TxBuffer_Destroy(sdr):
    if sdr.tx_cyclic_buffer == True:
        sdr.tx_destroy_buffer()


def load_channel_cal(filename="channel_cal_val.pkl"):
    """ Load Pluto Rx1 and Rx2 calibrated value, if not calibrated set all channel gain correction to 0.
        parameters:
            filename: type=string
                      Provide path of phase calibration file
    """

    try:
        with open(filename, "rb") as file:
            return pickle.load(file)  # Load channel cal values
    except:
        print("file not found, loading default (no channel gain shift)")
        return [0.0] * 2  # .append(0)  # if it fails load default value i.e. 0


ccal = load_channel_cal()
