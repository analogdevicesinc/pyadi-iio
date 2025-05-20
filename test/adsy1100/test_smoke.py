import pytest
import time
import os

import nebula

from bench.keysight import E36233A, N9040B
from bench.rs import SMA100A

import adi


configs = [
    {
        "name": "12gsps",
        "BOOT.BIN": "BOOT.BIN",
        "Kernel": "Image",
        "devicetree": "devicetree.dtb",
        "selmap_overlay": "tfc_12gsps/vu11p.dtbo",
        "selmap_bin": "vu11p.bin",
        "extras": [
            {"src": "tfc_12gsps/id00_uc07_tfc_12gsps.bin", "dst": "/lib/firmware/"}
        ],
    },
    {
        "name": "16gsps",
        "BOOT.BIN": "BOOT.BIN",
        "Kernel": "Image",
        "devicetree": "devicetree.dtb",
        "selmap_overlay": "tfc_16gsps/vu11p.dtbo",
        "selmap_bin": "vu11p.bin",
        "extras": [
            {"src": "tfc_16gsps/id00_uc07_tfc_16gsps.bin", "dst": "/lib/firmware/"}
        ],
    },
    {
        "name": "20gsps",
        "BOOT.BIN": "BOOT.BIN",
        "Kernel": "Image",
        "devicetree": "devicetree.dtb",
        "selmap_overlay": "tfc_20gsps/vu11p.dtbo",
        "selmap_bin": "vu11p.bin",
        "extras": [
            {"src": "tfc_20gsps/id00_uc07_tfc_20gsps.bin", "dst": "/lib/firmware/"}
        ],
    },
]

boot_files_folder = os.path.join(os.path.dirname(__file__), "bootfiles", "b0_main")

# Check if the boot files are present
for cfg in configs:
    path = os.path.join(boot_files_folder)
    for key in cfg:
        if key != "name" and key != "extras":
            assert os.path.isfile(
                os.path.join(path, cfg[key])
            ), f"File {key} not found at {os.path.join(path, cfg[key])}"
        if key == "extras":
            for extra in cfg[key]:
                assert os.path.isfile(
                    os.path.join(path, extra["src"])
                ), f"File {extra['src']} not found at {os.path.join(path, extra['src'])}"

config_file_folder = os.path.dirname(__file__)
config_file_zu4eg = os.path.join(config_file_folder, "nebula_zu4eg.yaml")


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


@pytest.fixture(scope="module")
def power_supply(parse_instruments):
    if "E36233A" not in parse_instruments.keys():
        pytest.skip("E36233A not found. Skipping test")
    address = parse_instruments["E36233A"]
    powerSupply = E36233A(address)
    powerSupply.connect()

    return powerSupply


@pytest.fixture
def nebula_boot_adsy1100_ethernet(request, power_supply, record_property):

    config = request.param

    show_uart_log = True
    skip_boot = False

    # Start UART
    neb_manager = nebula.manager(
        configfilename=config_file_zu4eg, board_name="zu4eg-washington"
    )
    neb_manager.monitor[0].log_filename = "zu4eg_uart.log"
    neb_manager.monitor[0]._read_until_stop()  # Flush
    neb_manager.monitor[0].start_log(logappend=True)
    neb_manager.monitor[0].print_to_console = show_uart_log
    time.sleep(2)

    if not skip_boot:

        # Power cycle to power down VU11P and Apollo
        print("Power cycling")
        power_supply.ch1.output_enabled = False
        power_supply.ch2.output_enabled = False
        time.sleep(5)
        power_supply.ch1.output_enabled = True
        power_supply.ch2.output_enabled = True

        # wait for linux to boot
        # neb_manager.monitor[0].print_to_console = True
        results = neb_manager.monitor[0]._read_until_done_multi(
            done_strings=["Linux version", "root@analog"],
            max_time=200,
        )

        neb_manager.network_check()

        # Copy common files
        for key in config:
            
            if key != "name" and key != "extras":
                contains_folder = config[key][1:].find("/") != -1
                if contains_folder:
                    folder = config[key][:-config[key][::-1].find("/")]
                    print(f"Creating folder {folder}")
                    neb_manager.net.run_ssh_command(f"mkdir -p /boot/{folder}")

                neb_manager.net.copy_file_to_remote(
                    os.path.join(boot_files_folder, config[key]),
                    f"/boot/{config[key]}",
                )
            if key == "extras":
                for extra in config[key]:
                    contains_folder = extra["dst"][1:].find("/") != -1
                    if contains_folder:
                        folder = extra["dst"][:-extra["dst"][::-1].find("/")]
                        print(f"Creating folder {folder}")
                        neb_manager.net.run_ssh_command(f"mkdir -p /boot/{folder}")

                    neb_manager.net.copy_file_to_remote(
                        os.path.join(boot_files_folder, extra["src"]),
                        extra["dst"],
                    )

        # Reboot
        neb_manager.net.reboot_board(bypass_sleep=True)

        # Wait for Linux login
        neb_manager.monitor[0].print_to_console = show_uart_log
        results = neb_manager.monitor[0]._read_until_done_multi(
            done_strings=["Linux version", "root@analog"],
            max_time=200,
        )

        # Check Ethernet
        if len(results) == 0:
            print("Kernel not started")
            neb_manager.monitor[0].stop_log()
            raise Exception("Kernel not started")
        if len(results) == 2 and not results[1]:
            neb_manager.monitor[0].stop_log()
            raise Exception("Kernel failed to reach login state")

        time.sleep(5)

        # Make UART accessible for tests/fixtures
        neb_manager.monitor[0].stop_log()
        time.sleep(1)
        neb_manager.monitor[0]._read_until_stop()  # Flush
        # Flush to marker
        do_flush(neb_manager.monitor[0])

        neb_manager.network_check()

        # Take power measurement
        pre_measure = measure_power(power_supply)
        record_property("pre_measure", pre_measure)

        # Load selmap overlay
        dtbo = config["selmap_overlay"]
        bin = config["selmap_bin"]
        cmd = f"cd /boot && chmod +x selmap_dtbo.sh && ./selmap_dtbo.sh -d {dtbo} -b {bin}"

        # Wait for Apollo and JESD links
        finished_str = "axi-jesd204-tx 880d0000.axi-jesd204-tx-b: AXI-JESD204-TX"
        neb_manager.monitor[0]._write_data(cmd)
        print("Waiting for selmap to boot")
        neb_manager.monitor[0].start_log(logappend=True)
        neb_manager.monitor[0].print_to_console = show_uart_log
        results = neb_manager.monitor[0]._read_until_done_multi(
            done_strings=[finished_str],
            max_time=200,
        )
        if len(results) == 0:
            print("JESD not started")
            neb_manager.monitor[0].stop_log()
            raise Exception("JESD not started")


        # Cleanup UART
        neb_manager.monitor[0].stop_log()
        time.sleep(1)
        neb_manager.monitor[0]._read_until_stop()  # Flush
        # Flush to marker
        do_flush(neb_manager.monitor[0])

        # Restart IIOD service
        neb_manager.net.run_ssh_command("service iiod restart", show_log=False)



    # Done
    return request.param, neb_manager


@pytest.mark.dependency()
@pytest.mark.parametrize("nebula_boot_adsy1100_ethernet", configs, indirect=True)
def test_boot(nebula_boot_adsy1100_ethernet, power_supply, record_property):

    params, neb_manager = nebula_boot_adsy1100_ethernet

    # Check power
    post_measure = measure_power(power_supply)
    record_property("post_measure", post_measure)

    # Check JESD204 links in data mode
    jesd = adi.jesd(address=neb_manager.net.dutip, username="root", password=neb_manager.net.dutpassword)
    links_details = jesd.get_all_link_statuses()
    links_top_level = jesd.get_all_statuses()
    drivers = links_top_level.keys()

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

    # Get dmesg
    dmesg = neb_manager.net.run_ssh_command("dmesg", show_log=False)
    dmesg = dmesg.stdout
    filename = f"test_boot_{params['name']}_dmesg.log"
    with open(filename, "w") as f:
        f.write(dmesg)

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

    for side in ['a','b']:
        for chan in range(2):
            print(f"Testing {params['name']} {side} {chan}")
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
                continue

            # Create FFT plot and save
            print("Creating FFT plot")
            from test.rf.spec import spec_est
            plt = spec_est(iq_data, fs=dev.rx_sample_rate, ref=2**15, plot=True, show_plot=False)
            plt.savefig(f"test_boot_{params['name']}_{side}_{chan}_fft.png")
            plt.close()
            del plt
