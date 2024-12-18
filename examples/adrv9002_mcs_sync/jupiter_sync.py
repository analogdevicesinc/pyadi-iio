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

LOOPBACK_TEST = 1
CALIBRATE = 1
REBOOT = False

set_dds_upto_dev = (
    10  # can be used to remove setting DDS to move faster through the testing process
)

synchrona_ip = "10.48.65.214"
device_ips = ["10.48.65.158", "10.48.65.239", "10.48.65.235", "10.48.65.240"]
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
    sshargs={"username": "root", "password": "analog1"},
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
temp = sdrs.temperature
print(f"Temperatures: {temp}")


################################################################################

print("Configure DDSs")
tone_freq = 500e3
tone_scale = 0.4
sdrs.primary.dds_single_tone(tone_freq, tone_scale)
for dev in sdrs.secondaries:
    dev.dds_single_tone(tone_freq, tone_scale)

print("ARM rx DMA and DDS cores")

print("Set MCS request as trigger source")
# mcs req as trig source
# 0- internal(1) or external(0) MCS pulses
# 1- internal(1) or external(0) mcs req
# 2- manual mcs requst flag(must be toggled)
# 3- mcs requests drives mcs(1) or trigger transfer(0)
for dev in [sdrs.primary_ssh] + sdrs.secondaries_ssh:
    val, e = dev._run("busybox devmem 0x84A0500c 32")
    print(f"0x84A0500c: {val}")
    val = int(val, 16)
    dev._run(f"busybox devmem 0x84A0500c 32 {val & 0xf7}")

print("Mute DAC data sources")
for dev in [sdrs.primary] + sdrs.secondaries:
    for chan in range(4):
        dev._txdac.reg_write(0x80000418 + chan*0x40, 0x3)
    dev._ctrl.debug_attrs['tx0_ssi_test_mode_loopback_en'] = '0'
    dev._ctrl.debug_attrs['tx1_ssi_test_mode_loopback_en'] = '0'
    if LOOPBACK_TEST == 1:
        dev._ctrl.debug_attrs['tx0_ssi_test_mode'] = '1'
        dev._ctrl.debug_attrs['tx1_ssi_test_mode'] = '1'

print("ARM DMA")
for dev in [sdrs.primary] + sdrs.secondaries:
    dev._rxadc.reg_write(0x80000048, 0x2)
    dev._txdac.reg_write(0x80000044, 0x2)

print("Enable DAC data sources")
for dev in [sdrs.primary] + sdrs.secondaries:
    for chan in range(4):
        dev._txdac.reg_write(0x80000418 + chan*0x40, 0x0)

print("Capture data")
for dev in [sdrs.primary] + sdrs.secondaries:
    dev.rx_enabled_channels = [0, 1]
    dev.rx_buffer_size = 2**16

data = {}
for dev in [sdrs.primary] + sdrs.secondaries:
    data[dev.uri] = dev.rx()

sleep(1)

print("Issue Sync pulse")
sdrs.sync.sysref_request = 1

# Plot data and save to figure
import matplotlib.pyplot as plt
plt.figure()

# Plot add devices and channels
for dev in data:
    iq_data = data[dev]
    real = iq_data.real
    imag = iq_data.imag
    plt.plot(real, label=f"{dev} real")
    # plt.plot(imag, label=f"{dev} imag")

plt.legend()
# Save to file
plt.savefig("sync.png")


