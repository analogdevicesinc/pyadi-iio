# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import sys
import adi
import matplotlib.pyplot as plt
import numpy as np
import time

from numpy.lib.format import write_array

class Hammerhead_setup():

    def __init__(self, uri):

        #Set up AD9213
        self.ad9213_transport = adi.ad9213(uri,device_name="axi-adrv9213-rx-hpc")
        self.ad9213_phy       = adi.ad9213(uri,device_name="ad9213")

        #Set up AD4080
        self.ad4080      = adi.ad4080(uri)
        self.ad4080_phy  = adi.ad4080(uri,device_name="ad4080")

        #Set ADC buffer sizes
        self.ad9213_transport.rx_buffer_size = 2048
        self.ad4080.rx_buffer_size = 2048

        #Set AD9213 DC couping and calibration registers
        self.ad9213_phy.ad9213_register_write(0x1617,0x1)
        self.ad9213_phy.ad9213_register_write(0x1601,0x1)
        print("DC-coupling reg (1617):", self.ad9213_phy.ad9213_register_read(0x1617))
        print("Cal freeze reg (1601):", self.ad9213_phy.ad9213_register_read(0x1601))

        # Set up high-speed path switches
        self.gpio_controller = adi.one_bit_adc_dac(uri, name="one-bit-adc-dac")
        setattr(self.gpio_controller, "gpio_adrf5203_ctrl0", 0) # defaults to high atten path
        setattr(self.gpio_controller, "gpio_adrf5203_ctrl1", 1) # low atten path -> SW0_ctrl = 1, SW1_ctrl = SW2_ctrl = 0
        setattr(self.gpio_controller, "gpio_adrf5203_ctrl2", 1)

  	# Set up adl558_en
        setattr(self.gpio_controller, "gpio_adl5580_en", 1)

        # Set up LTC2664
        self.ltc2664 = adi.ltc2664(uri)
        setattr(self.gpio_controller, "gpio_ltc2664_clr", 1)
        self.vdc_initial = 0 #mV

        #Set ADA4945 high and low clamp voltages
        self.vclamp_high = 2500
        self.vclamp_low = 500

        self.ltc2664.voltage0.volt = self.vdc_initial
        self.ltc2664.voltage1.volt = self.vclamp_high
        self.ltc2664.voltage2.volt = self.vclamp_low

        # Enable ADA4945 (driver amp to AD4080)
        setattr(self.gpio_controller, "gpio_ada4945_disable", 1)

        # Set precision path switch to 50ohm input
        setattr(self.gpio_controller, "gpio_adg5419_ctrl", 1)

# Main hammerhead class with important functions
class Hammerhead():

    #Default IP will get overwriten
    def __init__(self, uri="ip:192.168.2.1"):

        self.board       = Hammerhead_setup(uri)
        self.ad4080_phy  = adi.ad4080(uri, device_name="ad4080")
        #self.run_cal(0)


    def set_atten_path(self, atten_path):
        if atten_path == 1: #high attenuation path
            setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl0", 0)
            setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl1", 1)
            setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl2", 1)
        if atten_path == 0: #low attenuation path
            setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl0", 1)
            setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl1", 0)
            setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl2", 0)


    def set_dac_offset(self, voltage):
        #set DAC ch0 (ADL5580 VINM) to voltage (in mV)
        self.board.ltc2664.voltage0.volt = voltage


    def capture_data_ad9213(self, nsamples):
        self.board.ad9213_transport.rx_buffer_size = nsamples #assign buffer size to # of desired samples
        data = self.board.ad9213_transport.rx()
        self.board.ad9213_transport.rx_destroy_buffer()
        return data

    def capture_data_ad4080(self, nsamples):
        self.board.ad4080.rx_buffer_size = nsamples
        data = self.board.ad4080.rx()
        self.board.ad4080.rx_destroy_buffer()
        return data

    def plot_data_ad9213(self, data):
        x = np.arange(0, len(data))
        fig, (ch1) = plt.subplots(1, 1)

        fig.suptitle("AD9213 Data")
        ch1.plot(x*(10**(-4)), data)
        ch1.set_ylabel("AD9213 (LSBs)")
        ch1.set_xlabel(r"Time ($\mu$s)")
        ch1.set_ylim([-2048, 2048])

        #The use can save the plot of AD9213 data, such as a PDF file, using the plt.savefig method, as in the next line
        #plt.savefig('AD9213_plot.pdf', format='pdf', bbox_inches='tight')
        #print('\nThis plot has been saved as AD9213_plot.pdf in the current path.')
        print('\nIf the user is interested in saving the plot as a file, please remove # to un-comment line#111 of ADMX6001_multiClass-pCal.py.')
        plt.show(block=False)
        plt.pause(3)
        plt.close(fig)


    def plot_data_ad4080(self, data):
        x = np.arange(0, len(data))
        fig, (ch1) = plt.subplots(1, 1)

        fig.suptitle("AD4080 Data")
        ch1.plot(x*(1/31.25e6)*10**(6), data)
        ch1.set_ylabel("AD4080 (LSBs)")
        ch1.set_xlabel(r"Time ($\mu$s)")
        # ch1.set_ylim([-524288, 524288])

        # The use can save the plot of AD4080 data, such as a PDF file, using the plt.savefig method, as in the next line
        #plt.savefig('AD4080_plot.pdf', format='pdf', bbox_inches='tight')
        #print('\nThis plot has been saved as AD4080_plot.pdf in the current path.')
        print('\nIf the user is interested in saving the plot as a file, please remove # to un-comment line#130 of ADMX6001_multiClass-pCal.py.')

        plt.show(block=False)
        plt.pause(3)
        plt.close(fig)


    def run_cal(self, offset):
        # Calibrate to a specified DC voltage (will center this voltage at the AD9213 zero code)
        print("Beginning calibration...")
        self.set_dac_offset(offset)
        # set switch path to terminate input of ADL5580 driver amp
        setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl0", 1)
        setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl1", 1)
        setattr(self.board.gpio_controller, "gpio_adrf5203_ctrl2", 1)
        time.sleep(1)
        self.board.ad9213_phy.ad9213_register_write(0x1601, 0x0)
        time.sleep(3)
        self.board.ad9213_phy.ad9213_register_write(0x1601, 0x1)
        time.sleep(1)
        print("Calibration complete")


    # AD4080 Calibration code.
    # With an input signal present.
    def AD4080_CAl(self):
        print("adc cal code")
        self.ad4080_phy.ad4080_register_write(0x15, 0x50)
        data = self.board.ad4080.rx()
        expected_output = -342570
        arr = np.array([0x51, 0x61, 0x71, 0x81, 0x91, 0x01, 0x11, 0x21, 0x31, 0x41])
        print("starting value=")
        print(data)
        print(self.ad4080_phy.ad4080_register_read(0x16))

        if data[1] != expected_output:
            index = 0

            while data[1] != expected_output and index < len(arr):
                val = arr[index]
                self.board.ad4080.rx_destroy_buffer()
                self.ad4080_phy.ad4080_register_write(0x16, val)
                time.sleep(1)
                print("cal values=")
                print(self.ad4080_phy.ad4080_register_read(0x16))
                data = self.board.ad4080.rx()
                time.sleep(1)
                print(data)

                if data[1] == expected_output:

                    print("new data=")
                    print(data)
                    print("0x16 set to")
                    print(self.ad4080_phy.ad4080_register_read(0x16))
                    time.sleep(1)
                    self.ad4080_phy.ad4080_register_write(0x15, 0x40)
                    time.sleep(1)
                    print("\nAD4080 Calibrated")
                    break
                index += 1

        else:
            self.ad4080_phy.ad4080_register_write(0x15, 0x40)
            print("\nAD4080 Already Calibrated")

        input('\nPress any key to continue ...')
        # Exit calibration mode
        time.sleep(5)
        self.ad4080_phy.ad4080_register_write(0x15, 0x40)
