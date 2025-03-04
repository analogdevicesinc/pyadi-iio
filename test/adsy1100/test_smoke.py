import pytest
import time
import os

import nebula

configs = [
    {
        "name": "config1",
        "BOOT.BIN": "BOOT.BIN",
        "Kernel": "Image",
        "devicetree": "system.dtb",
        "selmap_overlay": "system.dtbo",
        "selmap_bin": "vu11p.bin",
        "extras": [{"src": "id00_uc07_tfc_12g.bin", "dst": "/lib/firmware/"}],
    },
    {
        "name": "config2",
        "BOOT.BIN": "BOOT.BIN",
        "Kernel": "Image",
        "devicetree": "system.dtb",
        "selmap_overlay": "system.dtbo",
        "selmap_bin": "vu11p.bin",
        "extras": [{"src": "id00_uc07_tfc_12g.bin", "dst": "/lib/firmware/"}],
    },
]

boot_files_folder = os.path.join(os.path.dirname(__file__), "boot_files")

# Check if the boot files are present
# for cfg in configs:
#     path = os.path.join(boot_files_folder, cfg["name"])
#     for key in cfg:
#         if key != "name" and key != "extras":
#             assert os.path.isfile(
#                 os.path.join(path, cfg[key])
#             ), f"File {cfg[key]} not found"
#         if key == "extras":
#             for extra in cfg[key]:
#                 assert os.path.isfile(
#                     os.path.join(path, extra["src"])
#                 ), f"File {extra['src']} not found"

config_file_zu4eg = "nebula_config_zu4eg.yaml"


@pytest.fixture
def nebula_boot_adsy1100_ethernet(request):

    config = request.param

    # Verify power on

    # Start UART
    neb_manager = nebula.manager(
        configfilename=config_file_zu4eg, board_name="zu4eg-washington"
    )
    neb_manager.monitor[0].log_filename = "zu4eg_uart.log"
    neb_manager.monitor[0]._read_until_stop()  # Flush
    neb_manager.monitor[0].start_log(logappend=True)
    time.sleep(2)

    # Copy common files
    for key in config:
        if key != "name" and key != "extras":
            neb_manager.copy_file_to_remote(
                os.path.join(boot_files_folder, config["name"], config[key]),
                f"/boot/{config[key]}",
            )
        if key == "extras":
            for extra in config[key]:
                neb_manager.copy_file_to_remote(
                    os.path.join(boot_files_folder, config["name"], extra["src"]),
                    f"{extra['dst']}{extra['src']}",
                )

    # Reboot
    neb_manager.reboot_board()

    # Wait for Linux login
    neb_manager.monitor[0].print_to_console = True
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

    # Take power measurement

    # Load selmap overlay

    # Done
    return request.param


@pytest.mark.parametrize("nebula_boot_adsy1100_ethernet", configs, indirect=True)
def test_boot(nebula_boot_adsy1100_ethernet):
    print(nebula_boot_adsy1100_ethernet)
    pass
