import adi
import numpy as np
from time import sleep
import logging
import sys
import matplotlib.pyplot as plt
#import code
#code.interact(local=locals())
from threading import Thread

class ReturnableThread(Thread):
    # This class is a subclass of Thread that allows the thread to return a value.
    def __init__(self, target):
        Thread.__init__(self)
        self.target = target
        self.result = None

    def run(self) -> None:
        self.result = self.target()

# Set up logging to only show adrv9002_multi logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adi.adrv9002_multi")
logger.setLevel(logging.DEBUG)
logger = logging.getLogger("paramiko")
logger.setLevel(logging.CRITICAL)

REBOOT = False

set_dds_upto_dev = (
    10  # can be used to remove setting DDS to move faster through the testing process
)

synchrona_ip = "191.168.0.1"
device_ips = [ "191.168.0.2", "191.168.0.3", "191.168.0.4", "191.168.0.5"]
device_ips = [f"ip:{ip}" for ip in device_ips]

if (len(device_ips) == 1):
    internal_mcs=True
else:
    internal_mcs=False

sdrs = adi.adrv9002_multi(
    primary_uri=device_ips[0],
    secondary_uris=device_ips[1:],
    sync_uri=f"ip:{synchrona_ip}",
    enable_ssh=True,
    sshargs={"username": "root", "password": "analog"},
)

# Reboot all systems
if REBOOT:
    print("Rebooting all systems")
    for dev in [sdrs.primary_ssh] + sdrs.secondaries_ssh:
        dev._run("reboot")

    sys.exit(0)
################################################################################
# 1 Prepare MCS

# ADRV9002 stuff
print("Loading profiles")
sdrs.write_profile("MCS_30_72_pin_en.json")

# For one system, the MCS sync is done automatically by the kernel driver
# after a profile is loaded.
# The "one system only" info is defined in the devicetree, loaded at boot.
if internal_mcs:
        print ("MSC not required")
else:


    sdrs.primary.ctx.set_timeout(30000)
    for sdr in sdrs.secondaries:
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
    for dev in sdrs._devices:
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
            sdrs.sync.sysref_request = 1
            break
        except Exception as e:
            if t == 5:
                raise Exception("Failed to request sysref")
            print(e)
            sleep(0.1)

    # Wait for mcs done
    for dev in sdrs._devices:
        while mcs_threads[dev.uri].is_alive():
            print ("Waiting for MCS done on" + dev.uri)
            sleep(0.5)

################################################################################
# 3 Prepare data transfer sync

print("ARM rx DMA and DDS cores")

print("Mute DAC data sources")
for dev in [sdrs.primary] + sdrs.secondaries:
    for chan in range(4):
        dev._txdac.reg_write(0x80000418 + chan*0x40, 0x3)

print("ARM RX/TX transfer paths")
for dev in [sdrs.primary] + sdrs.secondaries:
    dev._rxadc.reg_write(0x80000048, 0x2)
    dev._txdac.reg_write(0x80000044, 0x2)

print("Configure DDSs")
tone_freq = 500e3
tone_scale = 0.4
sdrs.primary.dds_single_tone(tone_freq, tone_scale)
for dev in sdrs.secondaries:
    dev.dds_single_tone(tone_freq, tone_scale)

print("Set DDS as DAC data source")
for dev in [sdrs.primary] + sdrs.secondaries:
    for chan in range(4):
        dev._txdac.reg_write(0x80000418 + chan*0x40, 0x0)

print("Enable Rx channels and define buffer size")
for dev in [sdrs.primary] + sdrs.secondaries:
    dev.rx_enabled_channels = [0, 1]
    dev.rx_buffer_size = 2**10

# create a buffer for data capture (after RX channel is armed)
data = {}
captureThread = {}
for dev in [sdrs.primary] + sdrs.secondaries:
    # Start a new thread
    captureThread[dev.uri] = ReturnableThread(target=lambda: dev.rx())
    captureThread[dev.uri].start()

sleep(1)

print("Issue Sync pulse")
sdrs.sync.sysref_request = 1

print("Capture data")
# Wait for the threads to finish
for dev in [sdrs.primary] + sdrs.secondaries:
    while captureThread[dev.uri].result is None:
        sleep(0.1)
    # in data is stored all RF data captured from all systems
    data[dev.uri] = captureThread[dev.uri].result

# Plot data and save to figure
plt.figure()

# 2RX2TX MIMO moden
n_ch = 2;

x=[]
for i in range(0,2**10):
    x.append(i)
jupiter_n=0
for dev in data:
    # data[ip] contains the data channels I0, Q0, I1, and Q1
    iq0iq1_data = data[dev]
    for i in range(n_ch):
        real_datai = iq0iq1_data[i].imag
        real_dataq = iq0iq1_data[i].real
        plt.plot(x, real_datai, label=f"{dev} real Q{i}")
    jupiter_n=jupiter_n+1

plt.legend()
# Save to file
plt.savefig("sync.png")
plt.show()
