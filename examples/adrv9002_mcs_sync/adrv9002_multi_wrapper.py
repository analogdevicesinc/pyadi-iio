from adi.adrv9002_multi import adrv9002_multi

import sys
import logging
from time import sleep
from threading import Thread
import numpy as np
import pickle

import time

class ReturnableThread(Thread):
    # This class is a subclass of Thread that allows the thread to return a value.
    def __init__(self, target):
        Thread.__init__(self)
        self.target = target
        self.result = None

    def run(self) -> None:
        self.result = self.target()

class adrv9002_multi_calibration(adrv9002_multi):
    def __init__(self, 
                 primary_uri="ip:analog.local", 
                 secondary_uris=[], 
                 sync_uri="ip:synchrona.local", 
                 enable_ssh=False, 
                 sshargs=None):
        # Call parent constructor
        super().__init__(primary_uri=primary_uri,
                         secondary_uris=secondary_uris,
                         sync_uri=sync_uri,
                         enable_ssh=enable_ssh,
                         sshargs=sshargs)

        # Your custom initialization
        self.data = {}
        self.captureThread = {}

        # Set up logging to only show adrv9002_multi logs
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("adi.adrv9002_multi")
        logger.setLevel(logging.DEBUG)
        logger = logging.getLogger("paramiko")
        logger.setLevel(logging.CRITICAL)

        REBOOT = False

        if (([primary_uri] + secondary_uris) == 1):
            internal_mcs=True
        else:
            internal_mcs=False

        if REBOOT:
            print("Rebooting all systems")
            for dev in [self.primary_ssh] + self.secondaries_ssh:
                dev._run("reboot")

            sys.exit(0)

        ################################################################################
        # 1 Prepare MCS

        # ADRV9002 stuff
        print("Loading profiles")
        self.write_profile("MCS_30_72_pin_en.json")

        # For one system, the MCS sync is done automatically by the kernel driver
        # after a profile is loaded.
        # The "one system only" info is defined in the devicetree, loaded at boot.
        if internal_mcs:
                print ("MSC not required")
        else:


            self.primary.ctx.set_timeout(30000)
            for sdr in self.secondaries:
                sdr._ctx.set_timeout(30000)

            # The linux driver exposes the "multi_chip_sync" attribute, which is a bit
            # more special. To know that the MCS was done successfully, one has to wait
            # for the multi_chip_sync attribute setting process to end successfully.
            # The attribute setting of multi_chip_sync only ends after MCS procedure is
            # completed or timeout occurs.
            # For the MCS sync to end, the adrv9002 needs to receive the 6 MCS pulse train.
            # In other words, we need to configure(put in MCS state) each adrv9002
            # in a separate thread, send the 6 MCS pulse train and wait for all started
            # threads that have put the adrv9002 devices in MCS state to end in success.

            mcs_threads = {}
            for dev in self._devices:
                mcs_threads[dev.uri] = ReturnableThread(target=lambda: dev._set_iio_dev_attr('multi_chip_sync', '1'))
                mcs_threads[dev.uri].start()

            sleep(1)
            print("Waiting for 6 pulses")

            ############################################################################
            # 2 Issue sync pulse

            # MCS request
            for t in range(6):
                try:
                    print("Requesting sysref")
                    self.sync.sysref_request = 1
                    break
                except Exception as e:
                    if t == 5:
                        raise Exception("Failed to request sysref")
                    print(e)
                    sleep(0.1)

            # Wait for mcs done
            for dev in self._devices:
                while mcs_threads[dev.uri].is_alive():
                    print ("Waiting for MCS done on" + dev.uri)
                    sleep(0.5)

            print("Mute DAC data sources")
            for dev in [self.primary] + self.secondaries:
                for chan in range(4):
                    dev._txdac.reg_write(0x80000418 + chan*0x40, 0x3)

        print("Custom ADRV9002 system initialized")

    def custom_method(self):
        # Example of adding new functionality
        print("Running a custom method on all devices...")
        for dev in [self.primary] + self.secondaries:
            print(f"Device URI: {dev.uri}")

    def _run(self, cmd):
        # Optionally override _run to customize SSH behavior
        print("Running overridden _run method")
        return super()._run(cmd)

    def rx_wrapper(self):
        # Example of adding new functionality
        start_time = time.time()
        print("")
        print("ARM RX transfer path")
        for dev in [self.primary] + self.secondaries:
            dev._rxadc.reg_write(0x80000048, 0x2)
            #dev._txdac.reg_write(0x80000044, 0x2)

#         print(f"Elapsed Time: {elapsed_time} seconds")
        print("Request capture")
        for dev in [self.primary] + self.secondaries:
            # Start a new thread
            self.captureThread[dev.uri] = ReturnableThread(target=lambda: dev.rx())
            self.captureThread[dev.uri].start()

        sleep(0.1)  # Allow buffers to arm
        print("Issue SYNC pulse")
        self.sync.sysref_request = 1

        print("Save data captured data")
        # Wait for threads to finish
        iq0iq1_data = []
        for dev in [self.primary] + self.secondaries:
            while self.captureThread[dev.uri].result is None:
                sleep(0.05)
            # in data is stored all RF data captured from all systems
            self.data[dev.uri] = self.captureThread[dev.uri].result
            iq0iq1_data.extend(self.data[dev.uri])
            
        iq0iq1_data = np.array(iq0iq1_data)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed Time: {elapsed_time} seconds")

        return iq0iq1_data
    
    def tx_primary(self, data):
        # tx only from primary device
        for dev in [self.primary]:
            dev.tx(data)

    # rx_ensm_mode_chan0
    @property
    def rx_ensm_mode_chan0(self):
        return self.primary.rx_ensm_mode_chan0

    @rx_ensm_mode_chan0.setter
    def rx_ensm_mode_chan0(self, value):
        self.primary.rx_ensm_mode_chan0 = value

    # rx_ensm_mode_chan1
    @property
    def rx_ensm_mode_chan1(self):
        return self.primary.rx_ensm_mode_chan1

    @rx_ensm_mode_chan1.setter
    def rx_ensm_mode_chan1(self, value):
        self.primary.rx_ensm_mode_chan1 = value

    # rx_ensm_mode_chan2
    @property
    def rx_ensm_mode_chan2(self):
        return self.secondaries[0].rx_ensm_mode_chan0

    @rx_ensm_mode_chan2.setter
    def rx_ensm_mode_chan2(self, value):
        self.secondaries[0].rx_ensm_mode_chan0 = value

    # rx_ensm_mode_chan3
    @property
    def rx_ensm_mode_chan3(self):
        return self.secondaries[0].rx_ensm_mode_chan1

    @rx_ensm_mode_chan3.setter
    def rx_ensm_mode_chan3(self, value):
        self.secondaries[0].rx_ensm_mode_chan1 = value

    #######################################################
    # Enable Rx channels
    @property
    def rx_enabled_channels_wrapper(self) -> list[int]:
        # Get unions from each device, force them to int and add +2 to each value in second device
        en_channels_dev_primary = [int(v) for v in self.primary.rx_enabled_channels]
        en_channels_dev_secondary = [int(v) for v in self.secondaries[0].rx_enabled_channels]
        en_channels_dev_secondary = [int(v) + 2 for v in en_channels_dev_secondary]
        return (en_channels_dev_primary + en_channels_dev_secondary)

    @rx_enabled_channels_wrapper.setter
    def rx_enabled_channels_wrapper(self, value: list[int]):
#         en_channels_dev_primary = [n for n in value if n in (0, 1)] # 0 to 1
#         en_channels_dev_secondary = [n for n in value if n in (2, 3)] # 2 to 3
#         en_channels_dev_secondary = [int(v) - 2 for v in en_channels_dev_secondary] # subtract 2
#         self.primary.rx_enabled_channels = en_channels_dev_primary
#         
        self.primary.rx_enabled_channels = [0, 1]
        self.secondaries[0].rx_enabled_channels = [0, 1]

    #######################################################
    # Enable Tx channels
    @property
    def tx_enabled_channels_wrapper(self) -> list[int]:
        # Get unions from each device, force them to int and add +2 to each value in second device
        en_channels_dev_primary = [int(v) for v in self.primary.tx_enabled_channels]
        en_channels_dev_secondary = [int(v) for v in self.secondaries[0].tx_enabled_channels]
        en_channels_dev_secondary = [int(v) + 2 for v in en_channels_dev_secondary]
        return (en_channels_dev_primary + en_channels_dev_secondary)

    @tx_enabled_channels_wrapper.setter
    def tx_enabled_channels_wrapper(self, value: list[int]):
#         en_channels_dev_primary = [n for n in value if n in (0, 1)] # 0 to 1
#         en_channels_dev_secondary = [n for n in value if n in (2, 3)] # 2 to 3
#         en_channels_dev_secondary = [int(v) - 2 for v in en_channels_dev_secondary] # subtract 2
#         self.primary.tx_enabled_channels = en_channels_dev_primary
#         self.secondaries[0].tx_enabled_channels = en_channels_dev_secondary
        self.primary.tx_enabled_channels = [0]
        self.secondaries[0].tx_enabled_channels = []

    #######################################################
    # Buffer size
    @property
    def rx_buffer_size_wrapper(self):
        return self.primary.rx_buffer_size

    @rx_buffer_size_wrapper.setter
    def rx_buffer_size_wrapper(self, value):
        for dev in [self.primary] + self.secondaries:
            dev.rx_buffer_size = value

    #######################################################
    # Tx Buffer size
    @property
    def tx_buffer_size_wrapper(self):
        return self.primary._tx_buffer_size

    @tx_buffer_size_wrapper.setter
    def tx_buffer_size_wrapper(self, value):
        for dev in [self.primary] + self.secondaries:
            dev._tx_buffer_size = value

    #######################################################
    # RX Hardware Gain
    # Channel 0
    @property
    def rx_hardwaregain_chan0(self):
        return self.primary.rx_hardwaregain_chan0

    @rx_hardwaregain_chan0.setter
    def rx_hardwaregain_chan0(self, value):
        self.primary.rx_hardwaregain_chan0 = value

    # Channel 1
    @property
    def rx_hardwaregain_chan1(self):
        return self.primary.rx_hardwaregain_chan1

    @rx_hardwaregain_chan1.setter
    def rx_hardwaregain_chan1(self, value):
        self.primary.rx_hardwaregain_chan1 = value

    # Channel 2
    @property
    def rx_hardwaregain_chan2(self):
        return self.secondaries[0].rx_hardwaregain_chan0

    @rx_hardwaregain_chan2.setter
    def rx_hardwaregain_chan2(self, value):
        self.secondaries[0].rx_hardwaregain_chan0 = value

    # Channel 3
    @property
    def rx_hardwaregain_chan3(self):
        return self.secondaries[0].rx_hardwaregain_chan1

    @rx_hardwaregain_chan3.setter
    def rx_hardwaregain_chan3(self, value):
        self.secondaries[0].rx_hardwaregain_chan1 = value

    #######################################################
    # TX Hardware Gain
    # Channel 0
    @property
    def tx_hardwaregain_chan0(self):
        return self.primary.tx_hardwaregain_chan0

    @tx_hardwaregain_chan0.setter
    def tx_hardwaregain_chan0(self, value):
        self.primary.tx_hardwaregain_chan0 = value

    # Channel 1
    @property
    def tx_hardwaregain_chan1(self):
        return self.primary.tx_hardwaregain_chan1

    @tx_hardwaregain_chan1.setter
    def tx_hardwaregain_chan1(self, value):
        self.primary.tx_hardwaregain_chan1 = value

    # Channel 2
    @property
    def tx_hardwaregain_chan2(self):
        return self.secondaries[0].tx_hardwaregain_chan0

    @tx_hardwaregain_chan2.setter
    def tx_hardwaregain_chan2(self, value):
        self.secondaries[0].tx_hardwaregain_chan0 = value

    # Channel 3
    @property
    def tx_hardwaregain_chan3(self):
        return self.secondaries[0].tx_hardwaregain_chan1

    @tx_hardwaregain_chan3.setter
    def tx_hardwaregain_chan3(self, value):
        self.secondaries[0].tx_hardwaregain_chan1 = value

    #######################################################
    # Local oscillator frequency [Hz] rx
    # Channel 0
    @property
    def rx0_lo(self):
        return self.primary.rx0_lo

    @rx0_lo.setter
    def rx0_lo(self, value):
        self.primary.rx0_lo = value

    # Channel 1
    @property
    def rx1_lo(self):
        return self.primary.rx1_lo
        
    @rx1_lo.setter
    def rx1_lo(self, value):
        self.primary.rx1_lo = value

    # Channel 2
    @property
    def rx2_lo(self):
        return self.secondaries[0].rx0_lo
        
    @rx2_lo.setter
    def rx2_lo(self, value):
        self.secondaries[0].rx0_lo = value

    # Channel 3
    @property
    def rx3_lo(self):
        return self.secondaries[0].rx1_lo
        
    @rx3_lo.setter
    def rx3_lo(self, value):
        self.secondaries[0].rx1_lo = value

    #######################################################
    # Local oscillator frequency [Hz] Tx
    # Channel 0
    @property
    def tx0_lo(self):
        return self.primary.tx0_lo

    @tx0_lo.setter
    def tx0_lo(self, value):
        self.primary.tx0_lo = value

    # Channel 1
    @property
    def tx1_lo(self):
        return self.primary.tx1_lo
        
    @tx1_lo.setter
    def tx1_lo(self, value):
        self.primary.tx1_lo = value

    # Channel 2
    @property
    def tx2_lo(self):
        return self.secondaries[0].tx0_lo
        
    @tx2_lo.setter
    def tx2_lo(self, value):
        self.secondaries[0].tx0_lo = value

    # Channel 3
    @property
    def tx3_lo(self):
        return self.secondaries[0].tx1_lo
        
    @tx3_lo.setter
    def tx3_lo(self, value):
        self.secondaries[0].tx1_lo = value

    #######################################################
    # Enable tx cyclic buffer
    @property
    def tx_cyclic_buffer_primary(self):    
        return self.primary.tx_cyclic_buffer

    @tx_cyclic_buffer_primary.setter
    def tx_cyclic_buffer_primary(self, value):
        self.primary.tx_cyclic_buffer = value

    #######################################################
    # Rx sample rate
    # Channel 0 
    @property
    def rx0_sample_rate(self):
        return self.primary.rx0_sample_rate

    # Channel 1
    @property
    def rx1_sample_rate(self):
        return self.primary.rx1_sample_rate
    
    # Channel 2
    @property
    def rx2_sample_rate(self):
        return self.secondaries[0].rx0_sample_rate

    # Channel 3
    @property
    def rx3_sample_rate(self):
        return self.secondaries[0].rx1_sample_rate
    
    #######################################################
    # Tx sample rate
    # Channel 0 
    @property
    def tx0_sample_rate(self):
        return self.primary.tx0_sample_rate

    # Channel 1
    @property
    def tx1_sample_rate(self):
        return self.primary.tx1_sample_rate
    
    # Channel 2
    @property
    def tx2_sample_rate(self):
        return self.secondaries[0].tx0_sample_rate

    # Channel 3
    @property
    def tx3_sample_rate(self):
        return self.secondaries[0].tx1_sample_rate
    
    ########################################################
    # Rx gain control mode
    @property
    def gain_control_mode(self):
        """gain_control_mode_chan0: Mode of receive path AGC. Options are:
        spi, pin, automatic"""
        return self.primary.gain_control_mode_chan0

    @gain_control_mode.setter
    def gain_control_mode(self, value):
        for dev in [self.primary] + self.secondaries:
            dev.gain_control_mode_chan0 = value
            dev.gain_control_mode_chan1 = value

    #########################################################
    # Rx destroy buffer wrapper
    def rx_destroy_buffer_wrapper(self):
        """rx_destroy_buffer: Clears RX buffer"""
        for dev in [self.primary] + self.secondaries:
            dev.rx_destroy_buffer()       

    #########################################################
    # Rx destroy buffer wrapper   
    def tx_destroy_buffer_wrapper(self):
        """tx_destroy_buffer: Clears TX buffer"""
        for dev in [self.primary] + self.secondaries:
            dev.tx_destroy_buffer()
