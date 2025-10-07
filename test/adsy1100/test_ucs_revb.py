import pytest
import time
import os
import logging

import nebula

import pandas as pd

from bench.keysight import E36233A, N9040B
from bench.rs import SMA100A

import adi
import iio
import numpy as np
import matplotlib.pyplot as plt
import test.rf.spec as spec

from .helpers import check_files_exist

# Adjust log levels
logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.WARNING)

max_use_cases_to_test = 5
device_hostname = "b0adsy1100"

image_folder = os.path.join(os.path.dirname(__file__), "images")
if not os.path.exists(image_folder):
    os.makedirs(image_folder)
log_folder = os.path.join(os.path.dirname(__file__), "boot_logs")
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

boot_files_folder = os.path.join(os.path.dirname(__file__), "revb_ref")
boot_subfolder_on_target = "pytest"

configs = [
    {
        "name": "20gsps",
        # "BOOT.BIN": "BOOT.BIN",
        # "Kernel": "Image",
        # "devicetree": "devicetree.dtb",
        "selmap_overlay": "vu11p-ad9084-vpx.dtbo",
        "selmap_bin": "vu11p_204C_M4_L8_NP16.bin",
        "boot_script": "selmap_dtbo.sh",
        "extras": [
            {"src": "204C_M4_L8_NP16_2p5_4x2.bin", "dst": "/lib/firmware/"},
            # {"src": "app_signed_encrypted_B/flash_image_0x01030000.bin", "dst": "/lib/firmware/app_signed_encrypted_B/"},
            # {"src": "app_signed_encrypted_B/flash_image_0x02000000.bin", "dst": "/lib/firmware/app_signed_encrypted_B/"},
            # {"src": "app_signed_encrypted_B/flash_image_0x20000000.bin", "dst": "/lib/firmware/app_signed_encrypted_B/"},
            # {"src": "app_signed_encrypted_B/flash_image_0x21000000.bin", "dst": "/lib/firmware/app_signed_encrypted_B/"},
            # {"src": "app_signed_encrypted_prod_B/flash_image_0x01030000.bin", "dst": "/lib/firmware/app_signed_encrypted_prod_B/"},
            # {"src": "app_signed_encrypted_prod_B/flash_image_0x02000000.bin", "dst": "/lib/firmware/app_signed_encrypted_prod_B/"},
            # {"src": "app_signed_encrypted_prod_B/flash_image_0x20000000.bin", "dst": "/lib/firmware/app_signed_encrypted_prod_B/"},
            # {"src": "app_signed_encrypted_prod_B/flash_image_0x21000000.bin", "dst": "/lib/firmware/app_signed_encrypted_prod_B/"},
            # {"src": "APOLLO_FW_CPU0_B.bin", "dst": "/lib/firmware/"},
            # {"src": "APOLLO_FW_CPU0.bin", "dst": "/lib/firmware/"},
            # {"src": "APOLLO_FW_CPU1_B.bin", "dst": "/lib/firmware/"},
            # {"src": "APOLLO_FW_CPU1.bin", "dst": "/lib/firmware/"}
        ],
    },
]

check_files_exist(configs, boot_files_folder)


# config_file_folder = os.path.dirname(__file__)
# config_file_zu4eg = os.path.join(config_file_folder, "nebula_zu4eg.yaml")
config_file_zu4eg = "/ci/nebula_zu4eg.yaml"

def measure_power(power_supply):
    v1 = power_supply.ch1.voltage
    c1 = power_supply.ch1.current_draw
    v2 = power_supply.ch2.voltage
    c2 = power_supply.ch2.current_draw

    results = {"v1": v1, "c1": c1, "p1": v1 * c1, "v2": v2, "c2": c2, "p2": v2 * c2}
    return results


def do_flush(neb_uart):
    # Flush to marker
    neb_uart._write_data("uname")
    found = neb_uart._read_until_done_multi(done_strings=["Linux"], max_time=10000)
    if not found or not found[0]:
        raise Exception("UART not working")


# @pytest.fixture(scope="module")
@pytest.fixture(scope="session")
def power_supply(parse_instruments):
    if "E36233A" not in parse_instruments.keys():
        pytest.skip("E36233A not found. Skipping test")
    address = parse_instruments["E36233A"]
    powerSupply = E36233A(address)
    powerSupply.connect()

    powerSupply.first_boot_powered = False
    # powerSupply.first_boot_powered = True

    # Turn system off initially
    powerSupply.ch1.output_enabled = False
    # powerSupply.ch2.output_enabled = False
    time.sleep(5)

    yield powerSupply

    logger.info("Powering down supply")
    time.sleep(5)
    powerSupply.ch1.output_enabled = False
    time.sleep(2)

# @pytest.fixture
@pytest.fixture(params=configs, scope="session")
def nebula_boot_adsy1100_ethernet(request, power_supply):

    config = request.param

    show_uart_log = False
    skip_boot = False
    monitor_for_jesd_done = "NET" # or "UART"

    # Start UART
    neb_manager = nebula.manager(
        configfilename=config_file_zu4eg, board_name="zu4eg-washington"
    )
    neb_manager.monitor[0].log_filename = os.path.join(log_folder, "zu4eg_uart.log")
    neb_manager.monitor[0]._read_until_stop()  # Flush
    neb_manager.monitor[0].start_log(logappend=True)
    neb_manager.monitor[0].print_to_console = show_uart_log
    neb_manager.monitor[0]._attemp_login("root", "root")
    neb_manager.monitor[0]._read_until_stop()  # Flush

    time.sleep(2)

    if not skip_boot:

        # Power cycle to power down VU11P and Apollo
        if not power_supply.first_boot_powered:
            power_supply.first_boot_powered = True
            logger.info("Power cycling for first boot")
            power_supply.ch1.output_enabled = True
            # # power_supply.ch2.output_enabled = True

            # wait for linux to boot
            # neb_manager.monitor[0].print_to_console = True
            results = neb_manager.monitor[0]._read_until_done_multi(
                done_strings=["Linux version", f"{device_hostname}"],
                max_time=200,
            )

        neb_manager.network_check()

        assert boot_subfolder_on_target != ""
        assert boot_subfolder_on_target is not None
        logger.info(f"Creating test folder in boot: {boot_subfolder_on_target}")
        neb_manager.net.run_ssh_command(f"rm -rf /boot/{boot_subfolder_on_target} || true")
        neb_manager.net.run_ssh_command(f"mkdir -p /boot/{boot_subfolder_on_target}")
        

        # Copy common files
        for key in config:
            
            if key != "name" and key != "extras":
                contains_folder = config[key][1:].find("/") != -1
                if contains_folder:
                    folder = config[key][:-config[key][::-1].find("/")]
                    logger.info(f"Creating folder {folder}")
                    neb_manager.net.run_ssh_command(f"mkdir -p /boot/{boot_subfolder_on_target}/{folder}")

                if key in ["BOOT.BIN", "Kernel", "devicetree"]:
                    neb_manager.net.copy_file_to_remote(
                        os.path.join(boot_files_folder, config[key]),
                        f"/boot/{config[key]}",
                    )
                else:
                    neb_manager.net.copy_file_to_remote(
                        os.path.join(boot_files_folder, config[key]),
                        f"/boot/{boot_subfolder_on_target}/{config[key]}",
                    )
                    
            if key == "extras":
                for extra in config[key]:
                    contains_folder = extra["dst"][1:].find("/") != -1

                    if contains_folder:
                        loc = extra["dst"].rfind('/')
                        folder = extra["dst"][:loc]
                        logger.info(f"Extras: Creating folder '{folder}'")
                        assert folder != ""
                        neb_manager.net.run_ssh_command(f"mkdir -p '{folder}'")

                    neb_manager.net.copy_file_to_remote(
                        os.path.join(boot_files_folder, extra["src"]),
                        extra["dst"],
                    )

        # Reboot
        neb_manager.monitor[0]._write_data("reboot -f")
        #neb_manager.net.reboot_board(bypass_sleep=True)

        # Wait for Linux login
        neb_manager.monitor[0].print_to_console = show_uart_log
        results = neb_manager.monitor[0]._read_until_done_multi(
            #done_strings=["Linux version", f"root@{device_hostname}"],
            done_strings=["Linux version", f"Login"],
            max_time=60,
        )

        # Check Ethernet
        if len(results) == 0:
            logger.error("Kernel not started")
            neb_manager.monitor[0].stop_log()
            raise Exception("Kernel not started")
        if len(results) == 2 and not results[1]:
            neb_manager.monitor[0].stop_log()
            raise Exception("Kernel failed to reach login state")

        time.sleep(5)

        neb_manager.monitor[0]._attemp_login("root", "root")
        neb_manager.monitor[0]._read_until_stop()  # Flush

        time.sleep(2)

        # Make UART accessible for tests/fixtures
        neb_manager.monitor[0].stop_log()
        time.sleep(1)
        neb_manager.monitor[0]._read_until_stop()  # Flush
        # Flush to marker
        #do_flush(neb_manager.monitor[0])

        neb_manager.network_check()

        # Take power measurement
        pre_measure = measure_power(power_supply)
        # record_property("pre_measure", pre_measure)

        # Load selmap overlay
        dtbo = config["selmap_overlay"]
        bin = config["selmap_bin"]
        cmd = f"cd /boot/{boot_subfolder_on_target} && chmod +x selmap_dtbo.sh && ./selmap_dtbo.sh -d {dtbo} -b {bin}"

        # Wait for Apollo and JESD links
        # finished_str = "axi-jesd204-tx 880d0000.axi-jesd204-tx-b: AXI-JESD204-TX"
        neb_manager.monitor[0].print_to_console = True
        neb_manager.monitor[0].start_log(logappend=True)
        #neb_manager.monitor[0].print_to_console = show_uart_log
        finished_str = "axi-jesd204-tx-b: AXI-JESD204-TX"
        neb_manager.monitor[0]._write_data(cmd)
        logger.info("Waiting for selmap to boot")
        if monitor_for_jesd_done == "UART":
            results = neb_manager.monitor[0]._read_until_done_multi(
                done_strings=[finished_str],
                max_time=300,
            )
            if len(results) == 0:
                logger.error("JESD not started")
                neb_manager.monitor[0].stop_log()
                raise Exception("JESD not started")
        elif monitor_for_jesd_done == "NET":        
            if not neb_manager.net.monitor_dmesg(finished_str, max_timeout_seconds=300):
                logger.error("JESD not started")
                neb_manager.monitor[0].stop_log()
                raise Exception("JESD not started")

        # Cleanup UART
        neb_manager.monitor[0].stop_log()
        time.sleep(1)
        neb_manager.monitor[0]._read_until_stop()  # Flush
        # Flush to marker
        #do_flush(neb_manager.monitor[0])

        # Restart IIOD service
        neb_manager.net.run_ssh_command("service iiod restart", show_log=False)



    # Done
    return request.param, neb_manager

class TestOverBootFiles:
    def test_boot(self, nebula_boot_adsy1100_ethernet, power_supply, record_property, caplog):

        params, neb_manager = nebula_boot_adsy1100_ethernet

        # Check power
        post_measure = measure_power(power_supply)
        record_property("post_measure", post_measure)

        # Get dmesg
        dmesg = neb_manager.net.run_ssh_command("dmesg", show_log=False)
        dmesg = dmesg.stdout
        filename = f"test_boot_{params['name']}_dmesg.log"
        filename = os.path.join(log_folder, filename)
        with open(filename, "w") as f:
            f.write(dmesg)
        record_property("dmesg_filename", filename)
        # save to caplog
        caplog.set_level("INFO")
        logger.info(dmesg)

    @pytest.mark.requirement("WASHINGTON-R10")
    # @pytest.mark.parametrize("nebula_boot_adsy1100_ethernet", configs, indirect=True)
    def test_uart(self, nebula_boot_adsy1100_ethernet, caplog):
        params, neb_manager = nebula_boot_adsy1100_ethernet

        # neb_manager.monitor[0]._attemp_login("root", "root")
        neb_manager.monitor[0]._write_data("uname -a")
        data = neb_manager.monitor[0]._read_for_time(period=5)
        logger.info(f"Data: {data}")
        found = False
        caplog.set_level("INFO")
        for chunk in data:
            if isinstance(chunk, list):
                for c in chunk:
                    logger.info(c)
                    if "Linux" in c:
                        found = True
            else:
                logger.info(chunk)
                if "Linux" in chunk:
                    found = True
        assert found, f"Did not get Linux uname response. Got: {data}"


    @pytest.mark.requirement("WASHINGTON-R8")
    def test_1g_ethernet(self, nebula_boot_adsy1100_ethernet, caplog):
        params, neb_manager = nebula_boot_adsy1100_ethernet

        # Check 1G Ethernet
        neb_manager.monitor[0]._write_data("ip -4 addr")
        data = neb_manager.monitor[0]._read_for_time(period=5)
        logger.info(f"Data: {data}")
        found = False
        caplog.set_level("INFO")
        for chunk in data:
            if isinstance(chunk, list):
                for c in chunk:
                    logger.info(c)
                    if "end0" in c and "state UP" in c:
                        found = True
            else:
                logger.info(chunk)
                if "end0" in chunk and "state UP" in chunk:
                    found = True
        assert found, f"Did not find eth0 up. Got: {data}"

        # Test ping
        neb_manager.network_check()


    @pytest.mark.requirement(["WASHINGTON-R16","WASHINGTON-R24"])
    def test_spi_read_ltc6952(self, nebula_boot_adsy1100_ethernet, caplog):

        params, neb_manager = nebula_boot_adsy1100_ethernet

        ip_addr = f"ip:{neb_manager.net.dutip}"
        logger.info(f"Connecting to {ip_addr}")

        ctx = iio.Context(ip_addr)
        assert ctx is not None, "Failed to create IIO context"

        for dev in ctx.devices:
            logger.info(f"Device Name: {dev.name}")
        dev = ctx.find_device("ltc6952")
        assert dev is not None, "Failed to find ltc6952 device"

        val = dev.reg_read(0x38)
        del dev
        del ctx
        # Keep lower 4 bits
        val = val & 0x0F
        caplog.set_level("INFO")
        logger.info(f"LTC6952 Address: {val:#04x}")
        assert val == 0x2, f"Unexpected LTC6952 address: {val:#04x}"

    @pytest.mark.requirement(["WASHINGTON-R16","WASHINGTON-R25"])
    def test_spi_read_adf4382(self, nebula_boot_adsy1100_ethernet, caplog):

        caplog.set_level("INFO")

        params, neb_manager = nebula_boot_adsy1100_ethernet

        ip_addr = f"ip:{neb_manager.net.dutip}"
        logger.info(f"Connecting to {ip_addr}")

        ctx = iio.Context(ip_addr)
        assert ctx is not None, "Failed to create IIO context"

        for dev in ctx.devices:
            logger.info(f"Device Name: {dev.name}")
        dev = ctx.find_device("adf4382")
        assert dev is not None, "Failed to find adf4382 device"

        val = dev.reg_read(0x4)
        logger.info(f"ADF4382 Address 0x04: {val:#04x}")
        assert val == 0x08, f"Unexpected ADF4382 address 0x04: {val:#04x}"

        val = dev.reg_read(0x5)
        logger.info(f"ADF4382 Address 0x05: {val:#04x}")
        assert val == 0x00, f"Unexpected ADF4382 address 0x05: {val:#04x}"

        # Scratch write then read
        dev.reg_write(0x0A, 0x55)
        val = dev.reg_read(0x0A)
        logger.info(f"ADF4382 Address 0x0A: {val:#04x}")
        assert val == 0x55, f"Unexpected ADF4382 address 0x0A: {val:#04x}"

        del dev
        del ctx

    @pytest.mark.requirement(["WASHINGTON-R16","WASHINGTON-R27"])
    def test_verify_jesd_in_data(self, nebula_boot_adsy1100_ethernet, record_property, caplog):
        params, neb_manager = nebula_boot_adsy1100_ethernet


        # Check JESD204 links in data mode
        jesd = adi.jesd(address=neb_manager.net.dutip, username="root", password=neb_manager.net.dutpassword)
        links_details = jesd.get_all_link_statuses()
        links_top_level = jesd.get_all_statuses()
        drivers = links_top_level.keys()

        failed = False
        caplog.set_level("INFO")
        for driver in drivers:
            logger.info(f"Driver: {driver}")
            for key in links_top_level[driver]:
                logger.info(f"{key}: {links_top_level[driver][key]}")
                logger.info(f"{driver} {key}: {links_top_level[driver][key]}")
                record_property(f"{driver}_{key}", links_top_level[driver][key])
                if key == "Link status":
                    val = links_top_level[driver][key]
                    if "DATA" not in val.upper():
                        logger.info(f"ERROR: Driver {driver} not in DATA state: {val}")
                        failed = True
                if key == "Lane rate":
                    val = links_top_level[driver][key]
                    if "20625.000" not in val:
                        logger.info(f"ERROR: Driver {driver} lane rate is 20625.000")
                        failed = True



            logger.info("\n")

            if driver not in links_details:
                continue

            for key in links_details[driver]:
                logger.info(f"{key}: {links_details[driver][key]}")
                record_property(f"{driver}_{key}", links_details[driver][key])

            logger.info("--------------")
            

        del jesd

        assert not failed, "One or more JESD204 links not in DATA state"

    @pytest.mark.requirement(["WASHINGTON-R16","WASHINGTON-R26"])
    @pytest.mark.parametrize("channel", [0 ,1])
    @pytest.mark.parametrize("side", [0, 1])
    def test_channel_mapping(self, channel, side, nebula_boot_adsy1100_ethernet, record_property, gn_plot_manager):
        params, neb_manager = nebula_boot_adsy1100_ethernet

        logger.info(f"Testing side {side} channel {channel}")
        uri = f"ip:{neb_manager.net.dutip}"

        # Check channel mapping
        dev = adi.ad9084(uri)
        rx_channels = dev._rx_channel_names
        tx_channels = dev._tx_channel_names

        logger.info(f"RX Channels: {rx_channels}")
        logger.info(f"TX Channels: {tx_channels}")

        record_property("rx_channels", rx_channels)
        record_property("tx_channels", tx_channels)

        assert len(rx_channels) == 4, f"Unexpected number of RX channels: {len(rx_channels)}"
        assert len(tx_channels) == 4, f"Unexpected number of TX channels: {len(tx_channels)}"

        # Set all NCO frequencies to known values
        N = len(dev.rx_channel_nco_frequencies)
        dev.rx_channel_nco_frequencies = [int(100e6)] * N

        N = len(dev.tx_channel_nco_frequencies)
        dev.tx_channel_nco_frequencies = [int(100e6)] * N

        N = len(dev.rx_main_nco_frequencies)
        dev.rx_main_nco_frequencies = [int(2000e6)] * N

        N = len(dev.tx_main_nco_frequencies)
        dev.tx_main_nco_frequencies = [int(2000e6)] * N

        dev.rx_buffer_size = 2**15
        dev.rx2_buffer_size = 2**15

        nco_freq = dev.rx_sample_rate / 4
        nco_freq = nco_freq + (channel) * 10e6
        nco_freq = nco_freq + (side) * 100e6
        nco_freq = int(nco_freq)
        assert nco_freq < dev.rx_sample_rate / 2, "NCO frequency too high"
        logger.info(f"Setting NCO Frequency: {nco_freq}")
        if side == 0:
            dev.rx_enabled_channels = [channel]
            dev.dds_single_tone(nco_freq, 0.99, channel=channel)
        else:
            dev.rx2_enabled_channels = [channel]
            dev.dds2_single_tone(nco_freq, 0.99, channel=channel)

        time.sleep(3)

        if side == 0:
            for _ in range(10):
                iq_data = dev.rx()
        else:
            for _ in range(10):
                iq_data = dev.rx2()

        logger.info(iq_data)
        assert not isinstance(iq_data, list), "Did not get IQ data"
        logger.info(f"IQ Data Shape: {iq_data.shape}")

        # Add plotly
        import plotly.graph_objects as go
        fig = go.Figure()
        tone_peaks, tone_freqs = spec.spec_est(iq_data, fs=dev.rx_sample_rate, ref=2 ** 15)
        fig.add_trace(go.Scatter(x=tone_freqs, y=tone_peaks, mode="lines"))
        fig.update_layout(
            title="FFT Analysis",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Magnitude (dBFS)",
            height=1000,
        )
        gn_plot_manager.add_plot(fig, "FFT Analysis")

        # Create FFT plot and save
        logger.info("Creating FFT plot")
        plt = spec.spec_est(iq_data, fs=dev.rx_sample_rate, ref=2**15, plot=True, show_plot=False)
        filename = f"test_boot_{side}_{channel}_fft.png"
        filename = os.path.join(image_folder, filename)
        logger.info(f"Saving FFT plot to: {filename}")
        plt.savefig(filename)
        record_property("fft_plot_filename", filename)
        plt.close()
        del plt    

        # Check for tone
        peak_min = -30
        RXFS = dev.rx_sample_rate
        tone_peaks, tone_freqs = spec.spec_est(iq_data, fs=RXFS, ref=2 ** 15)
        indx = np.argmax(tone_peaks)
        diff = np.abs(tone_freqs[indx] - nco_freq)
        s = "Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx])
        s += f" | Expected: {nco_freq} | Diff: {diff}"
        logger.info(s)

        del dev

        assert (nco_freq * 0.1) > diff
        assert tone_peaks[indx] > peak_min
