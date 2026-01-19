from time import sleep
import paramiko
import time
import math

def config_ad408x(generic, my_adc, my_pll, my_divider, my_one_bit_adc_dac, fsamp, filt_mode, dec_rate):
    tmsb, n_data_clks, res = resolve_generic(generic)  # Determines the tmsb and n_data_clks from function

    # Calculate adf4350 clock frequency
    f_data_clk = int(fsamp * n_data_clks)  # Multiply by 10x i.e. 10 CLKs per conversion for single lane LVDS

    print("{:<50} {:<20}".format("Requested ADC CNV clock frequency:", fsamp))
    print("{:<50} {:<20}".format("Requested LVDS CLK clock frequency:", f_data_clk))
    # Disable the AD9508 outputs
    my_one_bit_adc_dac.gpio_sync_n = 1  # disabled the ad9508 outputs via gpio before configuring clock changes
    sleep(0.25)

    # Case Statement to determine the ad9508 settings required.
    # As the ad4350 vco has a minimum output of 137.5 MHz, we always
    # keep it in the 200MHz to 400 MHz range, and use the
    # ad9508 dividers to reduce the output  frequency further
    # the statement below determines how many factors of 2 that
    # we need the dividers to increase by to maintain the
    # adf4350 in its operating range
    if 200e6 <= f_data_clk <= 400e6:
        print("Set CNV for: 20MHz to 40MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x26  # this divider range only, requires CLK polarity to be inverted (ad9508 anomaly)
        divider_range = 1   # data_clk is equal to adf4350_clk output
    elif 100e6 <= f_data_clk < 200e6:
        print("Set CNV for: 10MHz to 20MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x16  # normal clock polarity
        divider_range = 2  # data_clk is adf4350_clk output/2 to keep in adf4350s allowed range
    elif 50e6 <= f_data_clk < 100e6:
        print("Set CNV for: 5MHz to 10MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x16  # normal clock polarity
        divider_range = 4  # data_clk is adf4350_clk output/4 to keep in adf4350s allowed range
    elif 25e6 <= f_data_clk < 50e6:
        print("Set CNV for: 2.5MHz to 5MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x16  # normal clock polarity
        divider_range = 8  # data_clk is adf4350_clk output/8 to keep in adf4350s allowed range
    elif 10e6 <= f_data_clk < 25e6:
        print("Set CNV for: 1MHz to 2.5MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x16  # normal clock polarity
        divider_range = 16  # data_clk is adf4350_clk output/16 to keep in adf4350s allowed range
    else:
        print("Entry Was out of Range")
        f_data_clk = int(400e6)
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        print("Set Default CNV for: 20MHz to 40MHz Range")
        pol_data_clk = 0x26
        divider_range = 1  # data_clk is equal to adf4350_clk output

    adf4350_clk = f_data_clk * divider_range  # adjusts adf4350 clock back into  200-400MHz Range
    print("{:<50} {:<20}".format("Setting ADF4350 PLL Frequency to:", adf4350_clk))
    my_pll.frequency_altvolt0 = adf4350_clk  # configure the pll
    print("{:<50} {:<20}".format("ADF4350 PLL Frequency was set to:", my_pll.frequency_altvolt0))
    sleep(0.5)
    my_divider.channel[2].frequency = adf4350_clk / (n_data_clks * divider_range)  # configure CNV divider
    print("{:<50} {:<20}".format("CNV Divider:", (n_data_clks * divider_range)))
    my_divider.channel[3].frequency = (adf4350_clk / divider_range)  # configure CLK divider
    print("{:<50} {:<20}".format("CLK Divider:", divider_range))
    print("{:<50} {:<20}".format("LVDS_CNV_CLK_CNT to Set:", hex(lvds_reg_setting)))
    my_adc.reg_write(0x16, lvds_reg_setting)  # configure LVDS_CNV_CLK_CNT at address 0x16
    print("{:<50} {:<20}".format("LVDS_CNV_CLK_CNT Readback:", my_adc.reg_read(0x16)))
    my_divider.reg_write(0x2B, pol_data_clk)  # configure the polarity of the CLK

    print("{:<50} {:<20}".format("Requested Filter Mode to be set:", filt_mode))
    print("{:<50} {:<20}".format("Requested Dec Rate to set:", dec_rate))
    print("{:<50} {:<20}".format("ADC CNV Frequency:", my_divider.channel[2].frequency))
    print("{:<50} {:<20}".format("ADC LVDS CLK Frequency:", my_divider.channel[3].frequency))

    sleep(0.5)
    # Renable the AD9508 outputs
    my_one_bit_adc_dac.gpio_sync_n = 0
    sleep(0.5)
    # Disable filter to perform LVDS interface synchronization routine
    my_adc.filter_sel = "disabled"
    sleep(0.5)
    # Performs the LVDS interface synchronization routine
    print("Running LVDS interface Synchronize... ")
    my_adc.lvds_sync = "enable"
    print("Complete LVDS interface Synchronize. ")
    sleep(0.25)
    # Configure the Integrated Digital Filter
    my_adc.filter_sel = filt_mode
    sleep(0.25)
    my_adc.sinc_dec_rate = dec_rate
    sleep(0.25)

    # print("ad4080 URI: ", my_adc.uri)
    print("{:<50} {:<20}".format("ad4080 Filter Mode:", str(my_adc.filter_sel)))
    print("{:<50} {:<20}".format("ad4080 Decimation:", my_adc.sinc_dec_rate))
    print("{:<50} {:<20}".format("ad4080 sampling frequency:", my_adc.sampling_frequency))
    return

def config_ad488x(generic, my_adc, my_adc_b, my_pll, my_divider, my_one_bit_adc_dac, fsamp, filt_mode, dec_rate):
    tmsb, n_data_clks, res = resolve_generic(generic)  # Determines the tmsb and n_data_clks from function

    # Calculate adf4350 clock frequency
    f_data_clk = int(fsamp * n_data_clks)  # Multiply by 10x i.e. 10 CLKs per conversion for single lane LVDS

    print("{:<50} {:<20}".format("Requested ADC CNV clock frequency:", fsamp))
    print("{:<50} {:<20}".format("Requested LVDS CLK clock frequency:", f_data_clk))
    # Disable the AD9508 outputs
    my_one_bit_adc_dac.gpio_sync_n = 1  # disabled the ad9508 outputs via gpio before configuring clock changes
    sleep(0.25)

    # Case Statement to determine the ad9508 settings required.
    # As the ad4350 vco has a minimum output of 137.5 MHz, we always
    # keep it in the 200MHz to 400 MHz range, and use the
    # ad9508 dividers to reduce the output  frequency further
    # the statement below determines how many factors of 2 that
    # we need the dividers to increase by to maintain the
    # adf4350 in its operating range
    if 200e6 <= f_data_clk <= 400e6:
        print("Set CNV for: 20MHz to 40MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x26  # this divider range only, requires CLK polarity to be inverted (ad9508 anomaly)
        divider_range = 1   # data_clk is equal to adf4350_clk output
    elif 100e6 <= f_data_clk < 200e6:
        print("Set CNV for: 10MHz to 20MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x26  # normal clock polarity
        divider_range = 2  # data_clk is adf4350_clk output/2 to keep in adf4350s allowed range
    elif 50e6 <= f_data_clk < 100e6:
        print("Set CNV for: 5MHz to 10MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x26  # normal clock polarity
        divider_range = 4  # data_clk is adf4350_clk output/4 to keep in adf4350s allowed range
    elif 25e6 <= f_data_clk < 50e6:
        print("Set CNV for: 2.5MHz to 5MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x26  # normal clock polarity
        divider_range = 8  # data_clk is adf4350_clk output/8 to keep in adf4350s allowed range
    elif 10e6 <= f_data_clk < 25e6:
        print("Set CNV for: 1MHz to 2.5MHz Range")
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        pol_data_clk = 0x26  # normal clock polarity
        divider_range = 16  # data_clk is adf4350_clk output/16 to keep in adf4350s allowed range
    else:
        print("Entry Was out of Range")
        f_data_clk = int(400e6)
        lvds_reg_setting = calc_clk_cnt(f_data_clk, tmsb)  # determine the LVDS_CNV_CLK_CNT setting
        print("Set Default CNV for: 20MHz to 40MHz Range")
        pol_data_clk = 0x26
        divider_range = 1  # data_clk is equal to adf4350_clk output

    adf4350_clk = f_data_clk * divider_range  # adjusts adf4350 clock back into  200-400MHz Range
    print("{:<50} {:<20}".format("Setting ADF4350 PLL Frequency to:", adf4350_clk))
    my_pll.frequency_altvolt0 = adf4350_clk  # configure the pll
    print("{:<50} {:<20}".format("ADF4350 PLL Frequency was set to:", my_pll.frequency_altvolt0))
    sleep(0.5)
    my_divider.channel[0].frequency = adf4350_clk / (n_data_clks * divider_range)  # configure CNV divider
    my_divider.channel[2].frequency = adf4350_clk / (n_data_clks * divider_range)  # configure CNV divider
    print("{:<50} {:<20}".format("CNV Divider:", (n_data_clks * divider_range)))
    my_divider.channel[1].frequency = (adf4350_clk / divider_range)  # configure CLK divider
    my_divider.channel[3].frequency = (adf4350_clk / divider_range)  # configure CLK divider
    print("{:<50} {:<20}".format("CLK Divider:", divider_range))
    print("{:<50} {:<20}".format("LVDS_CNV_CLK_CNT to Set:", hex(lvds_reg_setting)))
    my_adc.reg_write(0x16, lvds_reg_setting)  # ChA configure LVDS_CNV_CLK_CNT at address 0x16
    my_adc_b.reg_write(0x16, lvds_reg_setting)  # ChB configure LVDS_CNV_CLK_CNT at address 0x16
    print("{:<50} {:<20}".format("LVDS_CNV_CLK_CNT Readback:", my_adc.reg_read(0x16)))
    my_divider.reg_write(0x1F, pol_data_clk)  # configure the polarity of the CLK Channel A
    my_divider.reg_write(0x2B, pol_data_clk)  # configure the polarity of the CLK Channel B

    print("{:<50} {:<20}".format("Requested Filter Mode to be set:", filt_mode))
    print("{:<50} {:<20}".format("Requested Dec Rate to set:", dec_rate))
    print("{:<50} {:<20}".format("ADC CNV Frequency:", my_divider.channel[0].frequency))  # Just read back 1 ch
    print("{:<50} {:<20}".format("ADC LVDS CLK Frequency:", my_divider.channel[1].frequency))  # Just read back 1

    sleep(0.5)
    # Renable the AD9508 outputs
    my_one_bit_adc_dac.gpio_sync_n = 0
    sleep(0.5)
    # Disable filter to perform LVDS interface synchronization routine
    my_adc.filter_sel = "disabled"
    my_adc_b.filter_sel = "disabled"
    sleep(0.5)
    # Performs the LVDS interface synchronization routine
    print("Running LVDS interface Synchronize... ")
    my_adc.channel[0].lvds_sync = "enable"
    sleep(0.5)
    my_adc_b.channel[0].lvds_sync = "enable"
    print("Complete LVDS interface Synchronize. ")
    sleep(0.5)

    # Configure the Integrated Digital Filter
    my_adc.filter_sel = filt_mode
    sleep(0.25)
    my_adc_b.filter_sel = filt_mode
    sleep(0.25)
    my_adc.sinc_dec_rate = dec_rate
    sleep(0.25)
    my_adc_b.sinc_dec_rate = dec_rate
    sleep(0.25)

    # print("ad4080 URI: ", my_adc.uri)
    print("{:<50} {:<20}".format("ad488x Filter Mode:", my_adc.filter_sel))
    print("{:<50} {:<20}".format("ad488x Decimation:", my_adc.sinc_dec_rate))
    print("{:<50} {:<20}".format("ad488x sampling frequency:", my_adc.sampling_frequency))
    return

def calc_clk_cnt(f_data_clk, tmsb):
    # This will determine the correct value for the LVDS_CNV_CLK_CNT register
    # The assumes the lower 4 bits are intended to be 0x1, i.e. default setting

    clk = f_data_clk  # This is the data clock period
    tclk = 1 / clk
    lvds_cnv_clk_cnt_num = math.floor((tmsb / tclk) + 1.5)  # Datasheet formula
    lvds_cnv_clk_cnt_reg = (lvds_cnv_clk_cnt_num - 3)  # As per lookup table -3 is correct for ad4080
    if lvds_cnv_clk_cnt_reg < 0:
        lvds_cnv_clk_cnt_reg = 0  # Cannot be less than zero
    lvds_reg_setting = (lvds_cnv_clk_cnt_reg << 4) + 1  # Shift bits into location and make lsb 1
    return lvds_reg_setting

def resolve_generic(generic):

    if generic == "ad4080" or generic == "ad4880":
        tmsb = 18e-9        # Datasheet specification, no gain correction
        n_data_clks = 10    # Data Clocks needed per conversion for Single Lane LVDS,  20 bits, DDR
        resolution = 20     # bits of resolution
    elif generic == "ad4084" or generic == "ad4884":
        tmsb = 18e-9        # Datasheet specification (tbc), no gain correction
        n_data_clks = 8     # Data Clocks needed per conversion for Single Lane LVDS,  16 bits, DDR
        resolution = 16     # bits of resolution
    elif generic == "ad4083" or generic == "ad4883":
        tmsb = 18e-9        # Datasheet specification (tbc), no gain correction
        n_data_clks = 8     # Data Clocks needed per conversion for Single Lane LVDS,  16 bits, DDR
        resolution = 16  # bits of resolution
    elif generic == "ad4086" or generic == "ad4886":
        tmsb = 18e-9        # Datasheet specification (tbc), no gain correction
        n_data_clks = 7     # Data Clocks needed per conversion for Single Lane LVDS,  14 bits, DDR
        resolution = 14  # bits of resolution
    else:
        # defaults to ad4080/ad4880 on error
        tmsb = 18e-9        # Datasheet specification, no gain correction
        n_data_clks = 10    # Data Clocks needed per conversion for Single Lane LVDS,  20 bits, DDR
        resolution = 20  # bits of resolution
    return tmsb, n_data_clks, resolution

def filter_bw_lookup(fsamp, filt_mode, dec_rate):
    bw = 0
    odr = 0
    print("Checking")
    if filt_mode == "disabled":
        odr = fsamp
        bw = 0.5 * fsamp
    elif filt_mode == "sinc1":
        if dec_rate == 2:
            odr = fsamp / dec_rate
            bw = 0.25 * fsamp
        elif dec_rate == 4:
            odr = fsamp / dec_rate
            bw = 0.114 * fsamp
        elif dec_rate == 8:
            odr = fsamp / dec_rate
            bw = 0.056 * fsamp
        elif dec_rate == 16:
            odr = fsamp / dec_rate
            bw = 0.028 * fsamp
        elif dec_rate == 32:
            odr = fsamp / dec_rate
            bw = 0.014 * fsamp
        elif dec_rate == 64:
            odr = fsamp / dec_rate
            bw = 0.007 * fsamp
        elif dec_rate == 128:
            odr = fsamp / dec_rate
            bw = 0.0035 * fsamp
        elif dec_rate == 256:
            odr = fsamp / dec_rate
            bw = 0.0017 * fsamp
        elif dec_rate == 512:
            odr = fsamp / dec_rate
            bw = 0.0009 * fsamp
        elif dec_rate == 1024:
            odr = fsamp / dec_rate
            bw = 0.0004 * fsamp
    elif filt_mode == "sinc5":
        if dec_rate == 2:
            odr = fsamp / dec_rate
            bw = 0.117 * fsamp
        elif dec_rate == 4:
            odr = fsamp / dec_rate
            bw = 0.0525 * fsamp
        elif dec_rate == 8:
            odr = fsamp / dec_rate
            bw = 0.0256 * fsamp
        elif dec_rate == 16:
            odr = fsamp / dec_rate
            bw = 0.0127 * fsamp
        elif dec_rate == 32:
            odr = fsamp / dec_rate
            bw = 0.0064 * fsamp
        elif dec_rate == 64:
            odr = fsamp / dec_rate
            bw = 0.0032 * fsamp
        elif dec_rate == 128:
            odr = fsamp / dec_rate
            bw = 0.0016 * fsamp
        elif dec_rate == 256:
            odr = fsamp / dec_rate
            bw = 0.0008 * fsamp
    elif filt_mode == "sinc5_plus_compensation":
        if dec_rate == 2:
            odr = fsamp / dec_rate / 2
            bw = 0.1015 * fsamp
        elif dec_rate == 4:
            odr = fsamp / dec_rate / 2
            bw = 0.0506 * fsamp
        elif dec_rate == 8:
            odr = fsamp / dec_rate / 2
            bw = 0.0253 * fsamp
        elif dec_rate == 16:
            odr = fsamp / dec_rate / 2
            bw = 0.0127 * fsamp
        elif dec_rate == 32:
            odr = fsamp / dec_rate / 2
            bw = 0.0063 * fsamp
        elif dec_rate == 64:
            odr = fsamp / dec_rate / 2
            bw = 0.0032 * fsamp
        elif dec_rate == 128:
            odr = fsamp / dec_rate / 2
            bw = 0.0016 * fsamp
        elif dec_rate == 256:
            odr = fsamp / dec_rate / 2
            bw = 0.0008 * fsamp
    print("{:<50} {:<20}".format("Noise Bandwidth:", bw))
    print("{:<50} {:<20}".format("Output Data Rate:", odr))
    return bw, odr

def copy_script_file(generic):
    # SSH connection parameters
    port = 22
    username = 'root'
    password = 'analog'
    hostname_remote = "analog.local"

    local_path = ("script/" + generic + "_script.sh")
    remote_path = ("/home/" + generic + "_remote_script.sh")
    print(local_path)
    print(remote_path)
    # Create an SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the remote host
        ssh.connect(hostname_remote, port=port, username=username, password=password)

        # Open an SFTP session
        sftp = ssh.open_sftp()

        # Upload the file
        sftp.put(local_path, remote_path)
        print(f"File uploaded successfully to {remote_path}")

        # Close the SFTP session
        sftp.close()
    finally:
        # Close the SSH connection
        ssh.close()
    return

def run_script(generic,fsamp, filt_mode, dec_rate):
    # Connection details
    # SSH connection parameters
    port = 22
    username = 'root'
    password = 'analog'
    hostname_remote = "analog.local"
    # my_uri = "ip:" + hostname_remote + ".local"
    # my_uri = "ip:" + hostname_remote

    # Script and parameters
    remote_path = ("/home/" + generic + "_remote_script.sh")
    param1 = fsamp
    param2 = filt_mode
    param3 = dec_rate

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sleep(1)
    try:
        # Connect to remote host
        ssh.connect(hostname_remote, port=port, username=username, password=password)
        print("Remote Path:" + remote_path)
        # Build the command
        command = f'bash {remote_path} {param1} {param2} {param3}'
        print("Remote Command:" + command)
        # Execute the command
        stdin, stdout, stderr = ssh.exec_command(command)

        # Read output
        output = stdout.read().decode()

        print("Output:")
        print(output)

    finally:
        ssh.close()
    return
