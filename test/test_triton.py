
import adi
# import test.dma_tests
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


logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.INFO)





hardware = ["Triton"]
classname = "adi.Triton"
iio_uri = "ip:192.168.2.1"



##########################################
# Dictionaries for Tests
##########################################

params = dict(
    loopback_test_1=dict(
                        tx_main_nco_frequencies=[8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000, 8000000000],
                        rx_main_nco_frequencies=[-4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000, -4800000000],
                        tx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_dsa_gain = 0,
    ),
    loopback_test_2=dict(
                        tx_main_nco_frequencies=[10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000],
                        rx_main_nco_frequencies=[-2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000],
                        tx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_dsa_gain = 0,
    ),
    loopback_test_3=dict(
                        tx_main_nco_frequencies=[12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000, 12000000000],
                        rx_main_nco_frequencies=[-800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000, -800000000],
                        tx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_dsa_gain = 0,
    ),
    filter_test_1=dict(
                        tx_main_nco_frequencies=[10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000],
                        rx_main_nco_frequencies=[-2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000],
                        tx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_dsa_gain = 0,
    ),
    filter_test_2=dict(
                        tx_main_nco_frequencies=[10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000],
                        rx_main_nco_frequencies=[-2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000],
                        tx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_dsa_gain = 0,
    ),
    dac_adc_loopback_30dB_attenuation=dict(
                        tx_main_nco_frequencies=[10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000],
                        rx_main_nco_frequencies=[-2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000],
                        tx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_dsa_gain = -30,
    ),
    sfdr_test=dict(
                        tx_main_nco_frequencies=[10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000, 10000000000],
                        rx_main_nco_frequencies=[-2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000, -2800000000],
                        tx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_frequencies=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_main_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        tx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_channel_nco_phases=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        rx_dsa_gain = 0,
    ),
)

##########################################
# DC Power Test - Preboot
#########################################

# @pytest.fixture(scope="module", autouse=True)
# def test_power_on():
#     rm = pyvisa.ResourceManager()
#     x = rm.list_resources()
#     inst = rm.open_resource('TCPIP::192.168.3.6::INSTR')    
    
#     inst.write("SOUR:VOLT 12")
#     inst.write("SOUR:CURR 30") # Change as needed
#     inst.write('OUTPut ON')

# def test_current_preboot():
#     rm = pyvisa.ResourceManager()
#     x = rm.list_resources()
#     inst = rm.open_resource('TCPIP::192.168.3.6::INSTR')

#     # inst.write("OUTP:PAIR PAR")
#     # inst.write("INST CH1")
#     # inst.write("SOUR:VOLT 12")
#     # inst.write("SOUR:CURR 30") # Change as needed
#     # inst.write('OUTPut ON')
#     print(inst.query("MEASure:CURR?"))

#     # error_message = inst.query('SYSTem:ERRor?')
#     # print("Error Message:", error_message)

#     current_value = float(inst.query("MEASure:CURR?"))

#     assert current_value > 2
#     assert current_value < 4.5

# def test_voltage_preboot():
#     rm = pyvisa.ResourceManager()
#     rm.list_resources()
#     inst = rm.open_resource('TCPIP::192.168.3.6::INSTR')

#     # inst.write("OUTP:PAIR PAR")
#     # inst.write("INST CH1")
#     # inst.write("SOUR:VOLT 12")
#     # inst.write("SOUR:CURR 30")  # Change as needed
#     # inst.write('OUTPut ON')
#     print(inst.query("MEASure:VOLT?"))

#     voltage_value = float(inst.query("MEASure:VOLT?"))

#     assert voltage_value > 11.8
#     assert voltage_value < 12.2


# # ##########################################
# # # Automated bootup 
# # ##########################################

# @pytest.fixture(scope="module", autouse=True)
# # @pytest.fixture(scope="module")
def test_bootup():
    import os
    import subprocess 

    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(dir_path)
    boot_path = os.path.join(dir_path, 'vcu118_quad_ad9084_2023-09-28')
    tcl_script_path = os.path.join(boot_path, 'run_me.tcl')

    # Path to Vivado Lab executable
    vivado_lab_executable = r"/tools/Xilinx/Vivado_Lab/2023.2/bin/xsdb"

    # Open Xilinx xsdb tool and
    # source run.tcl
    bitstream = os.path.join(boot_path, "system_top_26p4.bit")
    strip = os.path.join(boot_path, "simpleImage_26p4.strip" )
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
    time.sleep(140)  ## Wait for bootup
    print(dir(results))
    print(results)

    

# # #########################################
# # # DC Power Test - Postboot
# # #########################################

# def test_current_postboot():
#     rm = pyvisa.ResourceManager()
#     rm.list_resources()
#     inst = rm.open_resource('TCPIP::192.168.3.6::INSTR')

#     # inst.write("OUTP:PAIR PAR")
#     # inst.write("INST CH1")
#     # inst.write("SOUR:VOLT 12")
#     # inst.write("SOUR:CURR 30") # Change as needed
#     # inst.write('OUTPut ON')
#     print(inst.query("MEASure:CURR?"))

#     current_value = float(inst.query("MEASure:CURR?"))

#     assert current_value > 14
#     assert current_value < 18\

# def test_voltage_postboot():
#     rm = pyvisa.ResourceManager()
#     rm.list_resources()
#     inst = rm.open_resource('TCPIP::192.168.3.6::INSTR')

#     # inst.write("OUTP:PAIR PAR")
#     # inst.write("INST CH1")
#     # inst.write("SOUR:VOLT 12")
#     # inst.write("SOUR:CURR 30") # Change as needed
#     # inst.write('OUTPut ON')
#     print(inst.query("MEASure:VOLT?"))

#     voltage_value = float(inst.query("MEASure:VOLT?"))

#     assert voltage_value > 11.8
#     assert voltage_value < 12.2

#     inst.write("OUTP:PAIR PAR")
#     inst.write("INST CH1")
#     inst.write("SOUR:VOLT 12")
#     inst.write("SOUR:CURR 30") # Change as needed
#     inst.write('OUTPut ON')




# ##########################################
# # Ethernet connection test
# ##########################################

def test_iio_attr(iio_uri):
    print("iio_uri", iio_uri)

# #########################################
# # DDS Loopback Test 
# #########################################
# Prompt user to enter serial number
serial_number = input("Enter the serial number being tested: ")

# @pytest.fixture(scope="session")
def serial_number_fixture():
    return serial_number

directory = f'C:/ADI/Triton/pyadi-iio/testResults/SN{serial_number}'
os.makedirs(directory)

all_tone_peak_values = []

@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], ids=lambda x: f"channel:{x}")
# @pytest.mark.parametrize("channel", [0], ids=lambda x: f"channel:{x}")
@pytest.mark.parametrize(
    "param_set, frequency, scale, peak_min, hpf_value, lpf_value",
    [
        (params["loopback_test_1"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_2"], 50000000, 0.9, -25, 5, 15),
        (params["loopback_test_3"], 50000000, 0.9, -25, 5, 15),
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

    if len(all_tone_peak_values) == 48:
        freq_axis_values = [8000, 10000, 12000]
        ch0_values = [all_tone_peak_values[0], all_tone_peak_values[16], all_tone_peak_values[32]]
        ch1_values = [all_tone_peak_values[1], all_tone_peak_values[17], all_tone_peak_values[33]]
        ch2_values = [all_tone_peak_values[2], all_tone_peak_values[18], all_tone_peak_values[34]]
        ch3_values = [all_tone_peak_values[3], all_tone_peak_values[19], all_tone_peak_values[35]]
        ch4_values = [all_tone_peak_values[4], all_tone_peak_values[20], all_tone_peak_values[36]]
        ch5_values = [all_tone_peak_values[5], all_tone_peak_values[21], all_tone_peak_values[37]]
        ch6_values = [all_tone_peak_values[6], all_tone_peak_values[22], all_tone_peak_values[38]]
        ch7_values = [all_tone_peak_values[7], all_tone_peak_values[23], all_tone_peak_values[39]]
        ch8_values = [all_tone_peak_values[8], all_tone_peak_values[24], all_tone_peak_values[40]]
        ch9_values = [all_tone_peak_values[9], all_tone_peak_values[25], all_tone_peak_values[41]]
        ch10_values = [all_tone_peak_values[10], all_tone_peak_values[26], all_tone_peak_values[42]]
        ch11_values = [all_tone_peak_values[11], all_tone_peak_values[27], all_tone_peak_values[43]]
        ch12_values = [all_tone_peak_values[12], all_tone_peak_values[28], all_tone_peak_values[44]]
        ch13_values = [all_tone_peak_values[13], all_tone_peak_values[29], all_tone_peak_values[45]]
        ch14_values = [all_tone_peak_values[14], all_tone_peak_values[30], all_tone_peak_values[46]]
        ch15_values = [all_tone_peak_values[15], all_tone_peak_values[31], all_tone_peak_values[47]]
        plt.figure()
        plt.plot(freq_axis_values,ch0_values)
        plt.plot(freq_axis_values,ch1_values)
        plt.plot(freq_axis_values,ch2_values)
        plt.plot(freq_axis_values,ch3_values)
        plt.plot(freq_axis_values,ch4_values)
        plt.plot(freq_axis_values,ch5_values)
        plt.plot(freq_axis_values,ch6_values)
        plt.plot(freq_axis_values,ch7_values)
        plt.plot(freq_axis_values,ch8_values)
        plt.plot(freq_axis_values,ch9_values)
        plt.plot(freq_axis_values,ch10_values)
        plt.plot(freq_axis_values,ch11_values)
        plt.plot(freq_axis_values,ch12_values)
        plt.plot(freq_axis_values,ch13_values)
        plt.plot(freq_axis_values,ch14_values)
        plt.plot(freq_axis_values,ch15_values)
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Magnitude(dBFS)')
        plt.title('Loopback Test')
        plt.savefig(f'C:/ADI/Triton/pyadi-iio/testResults/SN{serial_number}/Loopback_Sweep_SN{serial_number}.png')

    if len(all_tone_peak_values) == 64:
        channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        values = [all_tone_peak_values[48],all_tone_peak_values[49],all_tone_peak_values[50], all_tone_peak_values[51], all_tone_peak_values[52], all_tone_peak_values[53], all_tone_peak_values[54], all_tone_peak_values[55], all_tone_peak_values[56], all_tone_peak_values[57], all_tone_peak_values[58], all_tone_peak_values[59], all_tone_peak_values[60], all_tone_peak_values[61], all_tone_peak_values[62], all_tone_peak_values[63]]
        plt.figure()
        plt.plot(channels, values)
        plt.xlabel('Channel')
        plt.ylabel('Magnitude(dBFS)')
        plt.title('Filter Test: Channel Magnitudes at 10 GHz')
        plt.savefig(f'C:/ADI/Triton/pyadi-iio/testResults/SN{serial_number}/Filter_Test_1_SN{serial_number}.png')

    if len(all_tone_peak_values) == 80:
        channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        values = [all_tone_peak_values[64],all_tone_peak_values[65],all_tone_peak_values[66], all_tone_peak_values[67], all_tone_peak_values[68], all_tone_peak_values[69], all_tone_peak_values[70], all_tone_peak_values[71], all_tone_peak_values[72], all_tone_peak_values[73], all_tone_peak_values[74], all_tone_peak_values[75], all_tone_peak_values[76], all_tone_peak_values[77], all_tone_peak_values[78], all_tone_peak_values[79]]
        plt.figure()
        plt.plot(channels, values)
        plt.xlabel('Channel')
        plt.ylabel('Magnitude(dBFS)')
        plt.title('Filter Test: Channel Magnitudes at 10 GHz')
        plt.savefig(f'C:/ADI/Triton/pyadi-iio/testResults/SN{serial_number}/Filter_Test_2_SN{serial_number}.png')

    if len(all_tone_peak_values) == 96:
        channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        values = [all_tone_peak_values[80],all_tone_peak_values[81],all_tone_peak_values[82], all_tone_peak_values[83], all_tone_peak_values[84], all_tone_peak_values[85], all_tone_peak_values[86], all_tone_peak_values[87], all_tone_peak_values[88], all_tone_peak_values[89], all_tone_peak_values[90], all_tone_peak_values[91], all_tone_peak_values[92], all_tone_peak_values[93], all_tone_peak_values[94], all_tone_peak_values[95]]
        plt.figure()
        plt.plot(channels, values)
        plt.xlabel('Channel')
        plt.ylabel('Magnitude(dBFS)')
        plt.title('DSA Test: Channel Magnitudes at 10 GHz')
        plt.savefig(f'C:/ADI/Triton/pyadi-iio/testResults/SN{serial_number}/DSA_Test_SN{serial_number}.png')


    assert all_tone_peak_values

    







# #########################################
# # SFDR Test 
# #########################################

all_sfdr_values = []

@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize("channel", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], ids=lambda x: f"channel:{x}")
# @pytest.mark.parametrize("channel", [0], ids=lambda x: f"channel:{x}")
@pytest.mark.parametrize(
    "param_set, hpf_value, lpf_value",
    [
        (params["sfdr_test"], 5, 15),   
    ],
)
@pytest.mark.parametrize("sfdr_min", [50])
def test_Triton_sfdr(test_sfdr, iio_uri, classname, channel, param_set, sfdr_min, hpf_value, lpf_value):
    global all_sfdr_values
    dev = adi.Triton("ip:192.168.2.1", calibration_board_attached=True)
    ## Set low pass and high pass filter values
    dev.hpf_ctrl = hpf_value
    dev.lpf_ctrl = lpf_value 
    ## SFDR test
    iio_uri = "ip:192.168.2.1"
    all_sfdr_values = test_sfdr(iio_uri, classname, channel, param_set, sfdr_min, sfdr_values=all_sfdr_values)
    
    if len(all_sfdr_values) == 16:
        channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        values = all_sfdr_values
        plt.figure()
        plt.plot(channels, values)
        plt.xlabel('Channel')
        plt.ylabel('SFDR (dB)')
        plt.title('SFDR Test')
        plt.savefig(f'C:/ADI/Triton/pyadi-iio/testResults/SN{serial_number}/SFDR_Test_SN{serial_number}.png')
