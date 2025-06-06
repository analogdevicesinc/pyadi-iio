import os
import time
import nebula

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



def nebula_boot_adsy1100_ethernet_func(request, ps, rp):

    config = request.param
    power_supply = ps
    record_property = rp

    show_uart_log = False
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
        if not power_supply.first_boot_powered:
            # power_supply.first_boot_powered = True
            print("Power cycling for first boot")
            power_supply.ch1.output_enabled = False
            power_supply.ch2.output_enabled = False
            time.sleep(5)
            power_supply.ch1.output_enabled = True
            power_supply.ch2.output_enabled = True

            # wait for linux to boot
            # neb_manager.monitor[0].print_to_console = True
            results = neb_manager.monitor[0]._read_until_done_multi(
                done_strings=["Linux version", f"root@{hostname}"],
                max_time=200,
            )
            print("Results after power cycle:", results)

        neb_manager.network_check()

        # Copy common files
        for key in config:
            time.sleep(1)
            
            if key != "name" and key != "extras":

                boot_root_files = ['BOOT.BIN', 'devicetree.dtb', 'Image']
                filename = os.path.basename(config[key])
                
                if filename not in boot_root_files:
                    print("Not a boot root file. Placing in /boot/jenkins")
                    print(f"Copying {key} to /boot/jenkins/{filename}")
                    neb_manager.net.run_ssh_command(f"mkdir -p /boot/jenkins/")
                    neb_manager.net.copy_file_to_remote(
                        os.path.join(config[key]),
                        f"/boot/jenkins/{filename}",
                    )
                else:
                    print(f"Copying {key} to /boot/{filename}")
                    neb_manager.net.copy_file_to_remote(
                        os.path.join(config[key]),
                        f"/boot/{filename}",
                    )
                # contains_folder = config[key][1:].find("/") != -1
                # if contains_folder:
                #     folder = config[key][:-config[key][::-1].find("/")]
                #     print(f"Creating folder {folder}")
                #     neb_manager.net.run_ssh_command(f"mkdir -p /boot/{folder}")

                # neb_manager.net.copy_file_to_remote(
                #     os.path.join(config[key]),
                #     f"/boot/{config[key]}",
                # )
            if key == "extras":
                for extra in config[key]:
                    # contains_folder = extra["dst"][1:].find("/") != -1
                    # if contains_folder:
                    #     folder = extra["dst"][:-extra["dst"][::-1].find("/")]
                    #     print(f"Creating folder {folder}")
                    #     neb_manager.net.run_ssh_command(f"mkdir -p /boot/{folder}")

                    print(f"Copying {extra['src']} to {extra['dst']}")

                    neb_manager.net.copy_file_to_remote(
                        os.path.join(extra["src"]),
                        extra["dst"],
                    )

        # Reboot
        neb_manager.monitor[0]._write_data("reboot")
        #neb_manager.net.reboot_board(bypass_sleep=True)

        # Wait for Linux login
        neb_manager.monitor[0].print_to_console = show_uart_log
        results = neb_manager.monitor[0]._read_until_done_multi(
            done_strings=["Linux version", f"root@{hostname}"],
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
        #do_flush(neb_manager.monitor[0])

        neb_manager.network_check()

        # Take power measurement
        pre_measure = measure_power(power_supply)
        record_property("pre_measure", pre_measure)

        # Load selmap overlay
        dtbo = config["selmap_overlay"]
        dtbo = os.path.join("/boot/jenkins", os.path.basename(dtbo))
        bin = config["selmap_bin"]
        bin = os.path.join("/boot/jenkins", os.path.basename(bin))
        cmd = f"cd /boot && chmod +x selmap_dtbo.sh && ./selmap_dtbo.sh -d {dtbo} -b {bin}"

        # Wait for Apollo and JESD links
        # finished_str = "axi-jesd204-tx 880d0000.axi-jesd204-tx-b: AXI-JESD204-TX"
        neb_manager.monitor[0].print_to_console = True
        neb_manager.monitor[0].start_log(logappend=True)
        #neb_manager.monitor[0].print_to_console = show_uart_log
        finished_str = "axi-jesd204-tx-b: AXI-JESD204-TX"
        neb_manager.monitor[0]._write_data(cmd)
        print("Waiting for selmap to boot")
        results = neb_manager.monitor[0]._read_until_done_multi(
            done_strings=[finished_str],
            max_time=300,
        )
        #if len(results) == 0:
        #    print("JESD not started")
        #    neb_manager.monitor[0].stop_log()
        #    raise Exception("JESD not started")


        # Cleanup UART
        neb_manager.monitor[0].stop_log()
        time.sleep(1)
        neb_manager.monitor[0]._read_until_stop()  # Flush
        # Flush to marker
        #do_flush(neb_manager.monitor[0])

        # Restart IIOD service
        neb_manager.net.run_ssh_command("service iiod restart", show_log=False)

    # Check power
    post_measure = measure_power(power_supply)
    record_property("post_measure", post_measure)

    # Done
    return request.param, neb_manager