import pytest
import time
import logging

import adi

DEBUG = False

# Disable Paramiko logging
logging.getLogger("paramiko").setLevel(logging.WARNING)

from .profiles_testing.stage3.generate_pytest_tests import get_test_boot_files_from_archive
from .helpers import nebula_boot_adsy1100_ethernet_func

configs = get_test_boot_files_from_archive()

@pytest.fixture(scope="module", params=configs)
def nebula_boot_adsy1100_ethernet(request, power_supply, record_testsuite_property):
    param, neb_manager = nebula_boot_adsy1100_ethernet_func(request, power_supply, record_testsuite_property)

    return param, neb_manager



def test_jesd_links(nebula_boot_adsy1100_ethernet, record_property):

    params, neb_manager = nebula_boot_adsy1100_ethernet

    print(f"Testing JESD204 links on {params['name']}")
    if DEBUG: return

    # Check JESD204 links in data mode
    try:
        jesd = adi.jesd(address=neb_manager.net.dutip, username="root", password=neb_manager.net.dutpassword)
        links_details = jesd.get_all_link_statuses()
        links_top_level = jesd.get_all_statuses()
        drivers = links_top_level.keys()
    except Exception as e:
        print(f"Failed to get JESD204 link status: {e}")
        drivers = []
        links_details = {}
        links_top_level = {}
        return

    for driver in drivers:
        print(f"Driver: {driver}")
        for key in links_top_level[driver]:
            print(f"{key}: {links_top_level[driver][key]}")
            record_property(f"{driver}_{key}", links_top_level[driver][key])

        print("\n")

        if driver not in links_details:
            continue

        for key in links_details[driver]:
            print(f"{key}: {links_details[driver][key]}")
            record_property(f"{driver}_{key}", links_details[driver][key])

        print("--------------")




@pytest.mark.parametrize("side", ['a', 'b'])
@pytest.mark.parametrize("channel", [0, 1])
def test_rf(nebula_boot_adsy1100_ethernet, side, channel, record_property):
    
    params, neb_manager = nebula_boot_adsy1100_ethernet

    print(f"Testing RF channel {channel} side {side} on {params['name']}")
    if DEBUG: return

    # Check RF
    dev = adi.ad9084(uri=f"ip:{neb_manager.net.dutip}")
    nco_freq = float(dev.rx_sample_rate) * 0.1
    N = len(dev.rx_channel_nco_frequencies)
    dev.rx_channel_nco_frequencies = [0] * N

    N = len(dev.tx_channel_nco_frequencies)
    dev.tx_channel_nco_frequencies = [0] * N

    N = len(dev.rx_main_nco_frequencies)
    dev.rx_main_nco_frequencies = [0] * N

    N = len(dev.tx_main_nco_frequencies)
    dev.tx_main_nco_frequencies = [0] * N

    dev.rx_buffer_size = 2**12
    dev.rx2_buffer_size = 2**12

    chan = channel

    print(f"Testing {params['name']} {side} {chan}")

    print(f"Setting NCO frequency to {nco_freq} Hz")
    if side == 'a':
        dev.dds_single_tone(
            channel=chan,
            frequency=nco_freq,
            scale=0.8,
        )
    else:
        dev.dds2_single_tone(
            channel=chan,
            frequency=nco_freq,
            scale=0.8,
        )
    time.sleep(3)

    print(f"Receiving data on {params['name']} {side} {chan}")

    if side == 'a':
        if chan == 1:
            dev.rx_enabled_channels = [0,1]
        else:
            dev.rx_enabled_channels = [chan]

        for _ in range(8):
            iq_data = dev.rx()
    else:
        if chan == 1:
            dev.rx2_enabled_channels = [0,1]
        else:
            dev.rx2_enabled_channels = [chan]

        for _ in range(8):
            iq_data = dev.rx2()

    print(iq_data)
    if isinstance(iq_data, list):
        iq_data = iq_data[chan]

    if len(iq_data) == 0:
        print(f"No data received on {params['name']} {side} {chan}")
        raise RuntimeError(f"No data received on {params['name']} {side} {chan}")

    # Create FFT plot and save
    print("Creating FFT plot")
    from test.rf.spec import spec_est
    plt = spec_est(iq_data, fs=dev.rx_sample_rate, ref=2**15, plot=True, show_plot=False)
    filename = f"test_boot_{params['name']}_{side}_{chan}_fft.png"
    plt.savefig(filename)
    record_property("fft_plot_filename", filename)
    plt.close()
    del plt    

def test_dmesg_errors(nebula_boot_adsy1100_ethernet, record_property):

    params, neb_manager = nebula_boot_adsy1100_ethernet

    print(f"Testing dmesg errors on {params['name']}")
    if DEBUG: return
    
    # Get dmesg
    dmesg = neb_manager.net.run_ssh_command("dmesg", show_log=False)
    dmesg = dmesg.stdout
    filename = f"test_boot_{params['name']}_dmesg.log"
    with open(filename, "w") as f:
        f.write(dmesg)
    record_property("dmesg_filename", filename)