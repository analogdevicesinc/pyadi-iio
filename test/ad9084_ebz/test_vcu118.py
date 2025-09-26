import pytest
import time
import os
import logging

import nebula

import pandas as pd

# from bench.keysight import E36233A, N9040B
# from bench.rs import SMA100A

import adi
import iio
import numpy as np
import matplotlib.pyplot as plt
import test.rf.spec as spec

# from .helpers import check_files_exist

# Adjust log levels
logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.WARNING)

max_use_cases_to_test = 5
device_hostname = "b0vcu118"

image_folder = os.path.join(os.path.dirname(__file__), "images")
if not os.path.exists(image_folder):
    os.makedirs(image_folder)
log_folder = os.path.join(os.path.dirname(__file__), "boot_logs")
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

boot_files_folder = os.environ.get("AD9084_EBZ_BOOT_FOLDER", "revb_ref")
boot_files_folder = os.path.join(os.path.dirname(__file__), boot_files_folder)
boot_subfolder_on_target = "pytest"

config_file_zu4eg = "/ci/nebula-vcu118.yaml"

BITSTREAM_FILE = os.environ.get("AD9084_EBZ_BITSTREAM_FILE", "system_top.bit")
STRIP_FILE = os.environ.get("AD9084_EBZ_STRIP_FILE", "simpleImage.ad9084_vcu118.strip")

configs = [
    {
        "name": "20gsps",
        "bitstream": os.path.join(boot_files_folder, BITSTREAM_FILE),
        "strip": os.path.join(boot_files_folder, STRIP_FILE),
    },
]

# check_files_exist(configs, boot_files_folder)


@pytest.fixture(params=configs, scope="session")
def nebula_boot_vcu118_ethernet(request):

    config = request.param

    show_uart_log = True
    # skip_boot = False
    # monitor_for_jesd_done = "NET" # or "UART"

    # Start UART
    neb_manager = nebula.manager(
        configfilename=config_file_zu4eg, board_name="vesync_test"
    )
    neb_manager.monitor[0].log_filename = os.path.join(log_folder, "zu4eg_uart.log")
    neb_manager.monitor[0]._read_until_stop()  # Flush
    neb_manager.monitor[0].start_log(logappend=True)
    neb_manager.monitor[0].print_to_console = show_uart_log
    # neb_manager.monitor[0]._attemp_login("root", "analog")
    neb_manager.monitor[0]._read_until_stop()  # Flush

    # Power cycle
    neb_manager.power.power_down_board()
    time.sleep(2)
    neb_manager.power.power_up_board()

    # Flash and boot
    neb_manager.jtag.microblaze_boot_linux(config["bitstream"], config["strip"])

    # Wait for board to boot
    neb_manager.monitor[0].print_to_console = show_uart_log
    results = neb_manager.monitor[0]._read_until_done_multi(
        # done_strings=["Linux version", f"root@{device_hostname}"],
        done_strings=["Linux version", f"ogin"],
        max_time=180,
    )
    if results[0] and results[1]:
        print("Board booted")
    else:
        neb_manager.power.power_down_board()
        neb_manager.monitor[0].stop_log()
        raise RuntimeError("Board did not boot")

    # Get IP address
    logger.info("Logging in")
    neb_manager.monitor[0]._attemp_login("root", "analog")
    neb_manager.monitor[0]._read_until_stop()  # Flush
    neb_manager.monitor[0].request_ip_dhcp_microblaze()
    ip_addr = neb_manager.monitor[0].get_ip_address_microblaze()
    neb_manager.net.dutip = ip_addr
    # neb_manager.monitor[0]._write_data("ifconfig eth0 down && ifconfig eth0 up\n")
    # neb_manager.monitor[0]._read_until_stop()  # Flush
    # neb_manager.monitor[0]._write_data("ifconfig eth0\n")
    time.sleep(2)
    # eth0_info = neb_manager.monitor[0]._read_until_stop()
    yield neb_manager, config

    neb_manager.power.power_down_board()
    neb_manager.monitor[0].stop_log()


class TestOverBootFiles:
    def test_ad9084_jesd(self, nebula_boot_vcu118_ethernet, record_property, caplog):

        neb_manager, params = nebula_boot_vcu118_ethernet

        print("HERE")
        dmesg = neb_manager.net.run_ssh_command("dmesg", show_log=False)
        dmesg = dmesg.stdout
        print(dmesg)
        filename = f"test_boot_{params['name']}_dmesg.log"
        filename = os.path.join(log_folder, filename)
        with open(filename, "w") as f:
            f.write(dmesg)
        record_property("dmesg_filename", filename)
        # save to caplog
        caplog.set_level("INFO")
        logger.info(dmesg)

    def test_uart(self, nebula_boot_vcu118_ethernet, caplog):
        neb_manager, params = nebula_boot_vcu118_ethernet

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

    def test_spi_read_adf4382(self, nebula_boot_vcu118_ethernet, caplog):

        caplog.set_level("INFO")

        neb_manager, params = nebula_boot_vcu118_ethernet

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

    def test_verify_jesd_in_data(
        self, nebula_boot_vcu118_ethernet, record_property, caplog
    ):

        neb_manager, params = nebula_boot_vcu118_ethernet

        # Check JESD204 links in data mode
        jesd = adi.jesd(
            address=neb_manager.net.dutip,
            username="root",
            password=neb_manager.net.dutpassword,
        )
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
