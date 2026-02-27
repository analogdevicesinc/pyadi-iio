import paramiko
import time
import argparse
import logging as log

from importlib.resources import files, as_file
from pathlib import Path

import adi

unit_ip='10.48.65.211'
dtbo_location = "vu11p/vu11p-ad9084-vpx-uc47-reva.dtbo"
bin_location = "vu11p/vu11p_uc47.bin"


pdu3_ip = '10.48.65.238'

def _set_logging_level(verbose: bool = False, debug: bool = False):
    """Configure logging level based on flags.
    
    :param verbose: Enable INFO level logging
    :param debug: Enable DEBUG level logging (overrides verbose)
    """
    if debug:
        log_level = log.DEBUG
    elif verbose:
        log_level = log.INFO
    else:
        log_level = log.WARNING

    log.basicConfig(level=log_level)
    
def _module_login():
    #Helper function to login to the module once power is active

    #Creates a client and returns it upon connection success. 

    #Need to add a counter and error if fails to connect after X times

    # ################ Attempt to log in to root@192.168.2.1 ################
    login_successful = False

    # Initialize client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())   

    while (not login_successful):
        # Establish an SSH connection to the card
        try:
            client.connect(hostname=unit_ip, port=22, username='root', password='root') 
            login_successful = True     # Login Succeeded       
        except:
            continue                    # Try the while loop again

    log.info("SSH connection established.\n")

    return client

def _SSH_execute_command(session: paramiko.SSHClient, cmd: str):
    """Takes in a client session and command, returns the resulting output and/or error (if applicable)

    :param session: SSH session with Washington connection
    :type session: paramiko.SSHClient
    :param command: command to execute over SSH
    :type command: string

    :return: resulting output from SSH command
    :rtype: str    
    """
    # Execute command over SSH
    _, stdout, stderr = session.exec_command(cmd)
    stdout.channel.recv_exit_status()         # Verifies command execution is completed before proceeding

    # Check for error; if there is an error, print the result to the terminal
    error_result = stderr.read().decode('utf-8')
    if error_result:
        log.warning(f"'{cmd}' command has the following error - {error_result}")   

    # Reads the resulting output and returns
    return stdout.read().decode('utf-8')

def _interpret_dmesg_readback(dmesg_result: str):
    """Interprets the current dmesg results and returns 2 items
    - # of enabled JESD lanes
    - names of failed JESD lanes

    :param dmesg_result: dmesg output for interpretation
    :type dmesg_result: string

    :return: [count of the enabled JESD lanes, names of failed JESD lanes]
    :rtype: tuple(int, list(str)) 
    """
    # Split the string by each line
    split_by_line = dmesg_result.split('\n')

    important_lines = []
    failing_jesd_lanes = []
    active_jesd_lane_cnt = 0

    for line in split_by_line:
        try:
            # Verify a given line has JESD & Rx or Tx information
            if ("rx" in line.split(' ')[4] or "tx" in line.split(' ')[4] and "jesd" in line.split(' ')[4]):
                important_lines.append(line)
        except:
            # If there is an error, continue since this line cannot be one that has JESD information that is needed
            continue

    # Loop over each important line
    for line_2 in important_lines:
        # if case to verify that a given jesd channel is active
        if ('width 8/8' in line_2):
            active_jesd_lane_cnt += 1                                   # increment the counter for the number of active JESD lanes
        # if case to check if a given jesd channel has a failure
        elif ('status failed (WAIT_BS)' in line_2):
            failing_jesd_lanes.append(line_2.split(' ')[4][:-1])        # append the name of the JESD lane(s) with at least one failure

    return active_jesd_lane_cnt, failing_jesd_lanes    

def _module_boot_check(client):
    # Initialize tracker for the number of JESD lanes that are active
    active_JESD_cnt = 0
    failed_boot = False
    loop_cnt = 0

    # Check that all 4 JESD lanes are displayed in dmesg before continuing
    # while (active_JESD_cnt != 1):
    while (active_JESD_cnt != 4 and not failed_boot):
        loop_cnt += 1
        log.debug(f"Checking dmesg for JESD lane initialization... Attempt #{loop_cnt}")
        # Add short delay between each dmesg read
        time.sleep(1)

        # Run dmesg command
        full_dmesg = _SSH_execute_command(client, "dmesg") 
        active_JESD_cnt, bad_JESD_lanes = _interpret_dmesg_readback(full_dmesg)
        log.debug(f"Number of active JESD lanes: {active_JESD_cnt}")
        log.debug(f"Failed JESD lanes: {bad_JESD_lanes}")

        if "CF_AXI_DDS_DDS MASTER" in full_dmesg.split('\n')[-1] and loop_cnt >= 30:
            failed_boot = True

    # If a failing JESD lane exist
    if (bool(len(bad_JESD_lanes))):
        log.warning(f"Not all JESD lanes initialized correctly. JESD lanes with issues - {';   '.join(bad_JESD_lanes)}\n") 

    return failed_boot

def __jesd_state_check(client):
    failed_boot = True
    state = ""
    max_retries = 18 #3 minutes of retries with 10 second delay between retries
    
    for attempt in range(max_retries):
        try:
            _SSH_execute_command(client, "systemctl restart iiod")
            
            dev = adi.ad9084(uri=f"ip:{unit_ip}")
            adc_fsm = dev.ctx.find_device("axi-ad9084-rx-hpc")
            state = adc_fsm.attrs["jesd204_fsm_state"].value
                    
            if state == "opt_post_running_stage":
                failed_boot = False
                break
        
            log.info(f"Attempt {attempt + 1}/{max_retries}: state is '{state}', waiting...")
            time.sleep(10)
        except Exception as e:
            log.info(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
            else:
                log.error(f"All {max_retries} attempts failed")
                raise

    return failed_boot

def _get_buffer(dev, side, chan):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if side == 'a':
                dev.rx_enabled_channels = [chan]
                iq_data = dev.rx()
                dev.rx_destroy_buffer()    
            else:
                dev.rx2_enabled_channels = [chan]
                iq_data = dev.rx2()
                dev.rx2_destroy_buffer()
            return iq_data
        except Exception as e:
            log.warning(f"get_buffer() attempt {attempt + 1}/{max_retries} failed: {e}")
            log.warning(f"Retrying get_buffer() {side} {chan}...")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                log.error(f"get_buffer() failed after {max_retries} attempts")
                raise

def ADSY1100_load_firmware():
    client = _module_login()
    
    ################ Run Startup Commands ################ 
    log.info("Running startup commands...\n")    
    _SSH_execute_command(client, f"cd /boot/;./selmap_dtbo.sh -d {dtbo_location} -b {bin_location}")  

    # Status print
    log.info(".sh file successfully executed. Validating startup worked correctly...\n")

#     failed_boot = _module_boot_check(client)
    failed_boot = __jesd_state_check(client)
    
    # Status print
    log.info("Module started successfully.\n")

    ################ Restart IIO Daemon ################    
    log.info("Restarting iio daemon...\n")     
    time.sleep(5)   
    _SSH_execute_command(client, "systemctl restart iiod")

    ################ Clean Up Clock Spurs ################ 
    log.info("Cleaning up Clock Spurs...\n")
    _SSH_execute_command(client, "iio_reg ltc6952 0x03 0x3F")
 
    if failed_boot:
        log.warning("Firmware sequence failed. Trying again...")
    else:
        print("ADSY1100 firmware sequence completed successfully.")
  
    client.close()

def ADSY1100_check_buffer():
    buffer_pass = True
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            if not unit_ip:
                log.info("No unit IP provided, connecting locally.")
                dev = adi.ad9084(uri="local:")
            else:
                log.info(f"Connected to device at IP: {unit_ip}")
                dev = adi.ad9084(uri=f"ip:{unit_ip}")
            break
        except Exception as e:
            log.warning(f"adi.ad9084(uri=f\"ip:{unit_ip}\") attempt {attempt + 1}/{max_retries} failed: {e}")
            log.warning("Retrying connection to device...")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                log.error(f"adi.ad9084(uri=f\"ip:{unit_ip}\") failed after {max_retries} attempts")
                return False                 
    
    dev.rx_buffer_size = 2**12
    dev.rx2_buffer_size = 2**12
 
    for side in ['a','b']:
        for chan in range(2):
            log.info(f"Testing {side} {chan}")
            
            iq_data = _get_buffer(dev, side, chan)
            log.debug(iq_data)
            
            if isinstance(iq_data, list):
                iq_data = iq_data[chan]

            if len(iq_data) == 0:
                log.error(f"No data received on {side} {chan}\n")
                buffer_pass = False
                continue
        
    return buffer_pass

def ADSY1100_reboot():
    client = _module_login()
    ################ Run Reboot Command ################
    print("Running Reboot Command...\n")
    _SSH_execute_command(client, "reboot")

    client.close()

def ADSY1100_power_cycle():
    # Helper function to power cycle the module using the PDU
    # Note: This function is not currently being used in the test, but can be used for future iterations if needed

    # Create SSH client and connect to PDU
    print("Running Power Cycle Command...\n")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            nuc5 = paramiko.SSHClient()
            nuc5.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            nuc5.connect(hostname='10.48.65.151', port=22, username='nuc5', password='Analog123!')
            
            # Power off the module
            _SSH_execute_command(nuc5, f"python3 /home/nuc5/nebula/nebula/cyberpower.py {pdu3_ip} 8 delayedReboot;")
            nuc5.close()
            break
        except Exception as e:
            log.warning(f"Power cycle attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                log.error(f"Power cycle failed after {max_retries} attempts")
                raise
    

# def save_dmesg(ADSY1100_SSH_Client: paramiko.SSHClient, data_path):
#     """
#     TODO
#     """
#     dmesg = _SSH_execute_command(ADSY1100_SSH_Client, "dmesg")
#     with open(f"{data_path}\\demsg_log_{time.strftime("%m%d%Y_%H%M%S", time.localtime())}.txt", "w") as file:
#         file.write(dmesg)

# def save_kernel(ADSY1100_SSH_Client: paramiko.SSHClient, data_path):
#     """
#     TODO
#     """
#     kernel = _SSH_execute_command(ADSY1100_SSH_Client, "journalctl -b --no-pager -k -p 7 -o short-precise --all")
#     with open(f"{data_path}\\kernel_log_{time.strftime("%m%d%Y_%H%M%S", time.localtime())}.txt", "w") as file:
#         file.write(kernel)
   
if __name__ == "__main__":
        
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output (INFO level)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output (DEBUG level)')
    args = parser.parse_args()
    
    _set_logging_level(verbose=args.verbose, debug=args.debug)
    print("Starting ADSY1100 DMA Buffer Test...\n")
    
    buffer_check = ADSY1100_check_buffer()
    if buffer_check:
        print(f"Test {i+1} passed.")
    else:
        log.error(f"Test {i+1} failed.")

    # iteration_count = 20
    # for i in range(iteration_count):
    #     print(f"Starting iteration {i+1}/{iteration_count}...")
 
    #     ADSY1100_load_firmware()
        
    #     buffer_check = ADSY1100_check_buffer()
    #     if buffer_check:
    #         print(f"Test {i+1} passed.")
    #     else:
    #         log.error(f"Test {i+1} failed.")

    #     # ADSY1100_reboot()
    #     ADSY1100_power_cycle()
    #     time.sleep(10)
        
    print("Action Complete")
