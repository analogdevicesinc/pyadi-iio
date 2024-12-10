import adi
import numpy as np
from time import sleep
import logging
import sys

# Set up logging to only show adrv9002_multi logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adi.adrv9002_multi")
logger.setLevel(logging.DEBUG)
logger = logging.getLogger("paramiko")
logger.setLevel(logging.CRITICAL)

INTERNAL_MCS = 0
LOOPBACK_TEST = 1
CALIBRATE = 1
REBOOT = False

set_dds_upto_dev = (
    10  # can be used to remove setting DDS to move faster through the testing process
)

synchrona_ip = "10.48.65.214"
device_ips = ["10.48.65.158", "10.48.65.239", "10.48.65.235", "10.48.65.240"]
device_ips = [f"ip:{ip}" for ip in device_ips]

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

## Sync request
## sync config
# 0- internal(1) or external(0) MCS pulses
# 1- internal(1) or external(0) mcs req
# 2- manual mcs requst flag(must be toggled)
# 3- mcs requests drives mcs(1) or capture(0)
v = 0xb if INTERNAL_MCS == 1 else 0x9
o, e = sdrs._run(f'busybox devmem 0x84A0500c 32 {v}')
print(f"0x84A0500c: {o}")
print(f'Errors: {e}')

# ADRV9002 stuff
print("Loading profiles")
sdrs.write_profile("MCS_30_72_pin_en.json")

sdrs.rx_ensm_mode_chan0 = 'calibrated'
sdrs.rx_ensm_mode_chan1 = 'calibrated'
sdrs.tx_ensm_mode_chan0 = 'calibrated'
sdrs.tx_ensm_mode_chan1 = 'calibrated'

sleep(2)

# ARM MCS
sdrs.primary.ctx.set_timeout(30000)
for sdr in sdrs.secondaries:
    sdr._ctx.set_timeout(30000)
sdrs.mcs = 1

print("Waiting for 6 pulses")
sleep(0.1)


################################################################################
# 2 Issue sync pulse

# MCS request
if INTERNAL_MCS == 1:
    out, e = sdrs.primary_ssh._run("busybox devmem 0x84A0500c 32")
    print(f"0x84A0500c: {out}")
    out = int(out, 16)
    print("toggle internal mcs request flag")
    sdrs.primary_ssh._run(f"busybox devmem 0x84A0500c 32 {out | 0x4}")
    sleep(0.1)
    sdrs.primary_ssh._run(f"busybox devmem 0x84A0500c 32 {out | 0xfb}")
else:
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

temp = sdrs.temperature
print(f"Temperatures: {temp}")


################################################################################
# 3 MCS Post

print("Enabling RF channels")
sdrs.rx_ensm_mode_chan0 = 'rf_enabled'
sdrs.rx_ensm_mode_chan1 = 'rf_enabled'
sdrs.tx_ensm_mode_chan0 = 'rf_enabled'
sdrs.tx_ensm_mode_chan1 = 'rf_enabled'

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


