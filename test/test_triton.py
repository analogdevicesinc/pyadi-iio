import adi
import test.dma_tests
import pytest
import test
import matplotlib.pyplot as plt
import numpy as np
from test.test_ad9084 import scale_field
from test.scpi import find_instrument
import subprocess
import pyvisa
import time
import test.instruments as instruments
from scipy import signal
import logging
import os
import genalyzer as gn
from adi import dds



logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.INFO)


# Hardware setup
hardware = ["Triton"]
classname = "adi.Triton"
iio_uri = "ip:192.168.2.1"

# # Prompt user to enter serial number
serialnumber = input("\n\n=== Device Setup ===\nEnter the serial number:\n> ")

@pytest.fixture(scope="session")
def serial_number_fixture():
    return serialnumber

# Make directory name with serial number
directory = os.path.expanduser(f'testResults/SN{serialnumber}')
os.makedirs(directory, exist_ok=True)


##########################################
# Dictionaries for Tests
#########################################

def make_test_params(tx_freq, rx_freq, dsa_gain=0):
    return dict(
        tx_main_nco_frequencies=[tx_freq] * 16,
        rx_main_nco_frequencies=[rx_freq] * 16,
        tx_channel_nco_frequencies=[0] * 16,
        rx_channel_nco_frequencies=[0] * 16,
        tx_main_nco_phases=[0] * 16,
        rx_main_nco_phases=[0] * 16,
        tx_channel_nco_phases=[0] * 16,
        rx_channel_nco_phases=[0] * 16,
        rx_dsa0_gain=dsa_gain,
        rx_dsa1_gain=dsa_gain,
        rx_dsa2_gain=dsa_gain,
        rx_dsa3_gain=dsa_gain,
    )

params = dict(
    loopback_test_8000MHz=make_test_params(8000000000, -4800000000),
    loopback_test_8500MHz=make_test_params(8500000000, -4300000000),
    loopback_test_9000MHz=make_test_params(9000000000, -3800000000),
    loopback_test_9500MHz=make_test_params(9500000000, -3300000000),
    loopback_test_10000MHz=make_test_params(10000000000, -2800000000),
    loopback_test_10500MHz=make_test_params(10500000000, -2300000000),
    loopback_test_11000MHz=make_test_params(11000000000, -1800000000),
    loopback_test_11500MHz=make_test_params(11500000000, -1300000000),
    loopback_test_12000MHz=make_test_params(12000000000, -800000000),
    filter_test_1=make_test_params(10000000000, -2800000000),
    filter_test_2=make_test_params(10000000000, -2800000000),
    dac_adc_loopback_30dB_attenuation=make_test_params(10000000000, -2800000000, dsa_gain=-30),
    sfdr_test=make_test_params(10000000000, -2800000000),
    nsd_test=make_test_params(10000000000, -2800000000),
)


# # ##########################################
# # # Automated bootup 
# # # ##########################################

@pytest.fixture(scope="module", autouse=True)
# @pytest.fixture(scope="module")
def test_bootup():
    import os
    import subprocess 

    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(dir_path)
    boot_path = os.path.join(dir_path, 'vcu118_quad_ad9084_revB-2024-12-12_hsci')
    tcl_script_path = os.path.join(boot_path, 'run.tcl')

    # Path to Vivado Lab executable
    vivado_lab_executable = r"/tools/Xilinx/Vivado_Lab/2023.2/bin/xsdb"

    # Open Xilinx xsdb tool and
    # source run.tcl
    bitstream = os.path.join(boot_path, "system_top.bit")
    strip = os.path.join(boot_path, "simpleImage.vcu118_quad_ad9084_revB.strip" )
    script = f"""
    connect
    fpga -f "{bitstream.replace(os.sep, '/')}"
    after 1000
    target 3
    dow "{strip.replace(os.sep, '/')}"
    after 1000
    con
    disconnect
    """
    with open(tcl_script_path, 'w') as f:
        f.write(script)

    # Command to run Vivado Lab with the Tcl script
    command = [vivado_lab_executable, '-eval', 'source', tcl_script_path]
    print(command)

    # Run the command
    subprocess.run(command)

    results = subprocess.run(command)
    time.sleep(260)  ## Wait for bootup
    print(dir(results))
    print(results)



# ##########################################
# # Ethernet connection test
# ##########################################

def test_iio_attr(iio_uri):
    print("iio_uri", iio_uri)

# #########################################
# # DDS Loopback Test 
# #########################################

# Create data array of peak values
all_tone_peak_values = []

@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], ids=lambda x: f"channel:{x}")
@pytest.mark.parametrize(
    "param_set, frequency, scale, peak_min, hpf_value, lpf_value",
    [
        (params["loopback_test_8000MHz"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_8500MHz"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_9000MHz"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_9500MHz"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_10000MHz"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_10500MHz"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_11000MHz"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_11500MHz"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_12000MHz"], 50000000, 0.9, -25, 5, 15),
        (params["filter_test_1"], 50000000, 0.9, -20, 5, 15),
        (params["filter_test_2"], 50000000, 0.9, -30, 11, 9),
        (params["dac_adc_loopback_30dB_attenuation"], 50000000, 0.9, -50, 5, 15),
    ]
)

def test_Triton_dds_loopback(
    test_dds_loopback,
    iio_uri,
    classname,
    param_set,
    channel,
    frequency,
    scale,
    peak_min,
    hpf_value,
    lpf_value,
):
    global all_tone_peak_values
    
    for i in range(10):
        try:
            dev = adi.Triton("ip:192.168.2.1", calibration_board_attached=True)
            iio_uri = "ip:192.168.2.1"
            ## Set low pass and high pass filter values
            dev.hpf_ctrl = hpf_value
            dev.lpf_ctrl = lpf_value
            ## Set cal board loopback state
            dev.gpio_ctrl_ind = 0
            dev.gpio_5045_v1 = 1                     
            dev.gpio_5045_v2 = 0
            dev.gpio_ctrl_rx_combined = 0
            ## Param set and DDS test
            param_set = scale_field(param_set, iio_uri)
            all_tone_peak_values = test_dds_loopback(
                iio_uri, classname, param_set, channel, frequency, scale, peak_min, use_obs=False, use_rx2=False, tone_peak_values=all_tone_peak_values
                )
            break
        except:
            print("retrying")
            import time
            time.sleep(5)
    else:
        raise Exception("number of retries exceeded")



    ######            ######
    ###### Data Plots ######
    ######            ######

    if len(all_tone_peak_values) == 144:
        freq_axis_values = [8000, 8500, 9000, 9500, 10000, 10500, 11000, 11500, 12000]
    
        plt.figure()

        for ch in range(16):
            ch_values = [all_tone_peak_values[ch + 16 * i] for i in range(9)]
            plt.plot(freq_axis_values, ch_values, label=f'CH{ch}')
    
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Magnitude (dBFS)')
        plt.title('Loopback Test')
        plt.legend(loc='lower right')  # You can also use 'upper right', 'lower left', etc.
        plt.grid(True)
        plt.savefig(f'testResults/SN{serialnumber}/Loopback_Sweep_SN{serialnumber}.png')


    if len(all_tone_peak_values) == 160:
        channels = list(range(16))  # Channels 0 through 15
        values = all_tone_peak_values[48:64]  # Slice values directly
        plt.figure()
        plt.plot(channels, values)
        plt.xlabel('Channel')
        plt.ylabel('Magnitude (dBFS)')
        plt.title('Filter Test: Channel Magnitudes at 10 GHz')
        plt.grid(True)
        plt.savefig(f'testResults/SN{serialnumber}/Filter_Test_1_SN{serialnumber}.png')

    if len(all_tone_peak_values) == 176:
        channels = list(range(16))  # Channels 0–15
        values = all_tone_peak_values[64:80]  # Grab values for those channels
        plt.figure()
        plt.plot(channels, values)
        plt.xlabel('Channel')
        plt.ylabel('Magnitude (dBFS)')
        plt.title('Filter Test: Channel Magnitudes at 10 GHz')
        plt.grid(True)
        plt.savefig(f'testResults/SN{serialnumber}/Filter_Test_2_SN{serialnumber}.png')

    if len(all_tone_peak_values) == 192:
        channels = list(range(16))  # Channels 0–15
        values = all_tone_peak_values[80:96]  # Slice values directly
        plt.figure()
        plt.plot(channels, values)
        plt.xlabel('Channel')
        plt.ylabel('Magnitude (dBFS)')
        plt.title('DSA Test: Channel Magnitudes at 10 GHz')
        plt.grid(True)
        plt.savefig(f'testResults/SN{serialnumber}/DSA_Test_SN{serialnumber}.png')


    assert all_tone_peak_values


# #########################################
# # SFDR Test 
# #########################################

all_sfdr_values = []

@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], ids=lambda x: f"channel:{x}")
@pytest.mark.parametrize(
    "param_set, hpf_value, lpf_value",
    [
        (params["sfdr_test"], 5, 15),   
    ],
)
@pytest.mark.parametrize("sfdr_min", [50])
def test_Triton_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min, hpf_value, lpf_value):
    global all_sfdr_values

    for i in range(10):
        try:
            dev = adi.Triton("ip:192.168.2.1", calibration_board_attached=True)
            ## Set low pass and high pass filter values
            dev.hpf_ctrl = hpf_value
            dev.lpf_ctrl = lpf_value 
            ## SFDR test
            iio_uri = "ip:192.168.2.1"
            dev.dds_single_tone(100000000, scale=0, channel=channel)
            all_sfdr_values = test_sfdr(iio_uri, classname, channel, param_set, sfdr_min, sfdr_values=all_sfdr_values)
            break
        except:
            print("retrying")
            import time
            time.sleep(5)
    else:
        raise Exception("number of retries exceeded")
   
    if len(all_sfdr_values) == 16:
        channels = list(range(16))  # Channels 0–15
        values = all_sfdr_values
        plt.figure()
        plt.plot(channels, values)
        plt.xlabel('Channel')
        plt.ylabel('SFDR (dB)')
        plt.title('SFDR Test')
        plt.savefig(f'testResults/SN{serialnumber}/SFDR_Test_SN{serialnumber}.png')




# #########################################
# # NSD Test
# #########################################
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], ids=lambda x: f"channel:{x}")
@pytest.mark.parametrize(
    "param_set",
    [
        (params["nsd_test"]),   
    ]
)
@pytest.mark.parametrize("nsd_min", [-140])
@pytest.mark.parametrize("frequency", [100e6])

def test_Triton_NSD(test_nsd, iio_uri, classname, channel, param_set, nsd_min, frequency):

    for i in range(10):
        try:
            iio_uri = "ip:192.168.2.1"
            dev = adi.Triton("ip:192.168.2.1", calibration_board_attached=True)
            ## Set cal board loopback state
            dev.gpio_ctrl_ind = 0
            dev.gpio_5045_v1 = 1                     
            dev.gpio_5045_v2 = 0
            dev.gpio_ctrl_rx_combined = 0
            dev.dds_single_tone(frequency, scale=0, channel=channel)
            test_nsd(iio_uri, serialnumber, classname, channel, param_set, nsd_min, frequency)
            dev = adi.Triton("ip:192.168.2.1", calibration_board_attached=True)
            break
        except:
            print("retrying")
            import time
            time.sleep(5)
    else:
        raise Exception("number of retries exceeded")
            









