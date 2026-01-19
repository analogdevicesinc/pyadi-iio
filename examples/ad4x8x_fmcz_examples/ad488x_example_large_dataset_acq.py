
import numpy as np
from scipy.signal import windows
from scipy.fft import fft, fftfreq
from matplotlib import pyplot as plt
from mpl_interactions import panhandler, zoom_factory
from ad4x8x_eval_fmcz_config import config_ad488x, filter_bw_lookup, run_script, copy_script_file
from adi import ad4880, ad9508, adf4350, one_bit_adc_dac
from ad4x8x_genalyzer import genalyzer_data_analysis
import paramiko  # to use SSH
import time
generic="ad4880"
# Data source flag = 'FILE' | 'pyADC' | 'zedADC'
# 'FILE' -> loads the data from a file specified in the line 'with open('FILE_NAME.xxx', 'rb') as file:'
# 'pyADC' -> Acquire the data from the AD4880 using the pyadi-iio library
# 'zedADC' -> Acquire the data from the AD4880 via ZedBoard IIO driver and then transfer the file to this PC via SCP.
# P.S. -> Always perform a reboot in the ZedBoard when changing from 'pyADC' to 'zedADC' and vice-versa.
# P.S.2 -> Restarting the Python kernel every once in a while also helps to prevent memory allocation errors in the PC.
fsamp = 40e6  # Default Sampling Frequency entered in Hz
# Filter Mode options: "disabled", "sinc1", "sinc5", "sinc5_plus_compensation"
filt_mode = "disabled"
# Set Decimation Rate Options: 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024
# Refer to Datasheet for options available to each Filter Mode
# This setting is ignored when FiltMode = "disabled"
dec_rate = 4
# Setting how many conversions results to take
# my_acq_size = 15 * 1024 * 1024 # 512  # For pyadi-iio Max 15M samples, i.e. 30M/2 Channels
my_acq_size = 50 * 1024 * 1024  # For remote_script, Max 50M samples for Dual channel ??
# "pyadi-iio" = configure the evb via python. "remote_script": configure with bash script
# This will copy a script file to the Zedboard and run the configuration onboard
config_mode = "remote_script"
# config_mode = "pyadi-iio"
# config_mode = "FILE" # You must create a folder C:\zedboard_data on you machine
 #   # Config
 #   ADC_sf = 8000000 # Variable Input Sampling Frequency
# SSH connection parameters
#    host = '169.254.77.175'  # ZedBoard IP address
port = 22
username = 'root'
password = 'analog'
hostname_remote = "analog.local"
# my_uri = "ip:" + hostname_remote + ".local"
my_uri = "ip:" + hostname_remote

# If we are NOT extracting data straight from a local file on the C: drive, then we need to configure the
# board to acquire new data
if config_mode != "FILE":
    print("{:<50} {:<20}".format("Opening connection to Zedboard at: ", my_uri))
    # Establish connections to the FMC board devices
    print("Connection opening...................")
    my_adc = ad4880(uri=my_uri, device_name="ad4880")
    time.sleep(0.5)
    my_adc_b = ad4880(uri=my_uri, device_name="ad4880_chb")
    print("Connection established...............")
    print("{:<50} {:<20}".format("Lsb Size:", my_adc.channel[0].scale))   # Not necessary, just early check of device tree
    time.sleep(0.5)
    # Configuring how many conversions results to take
    my_adc.rx_buffer_size = my_acq_size
    # Set timeout for Output Data Rate and number of results being acquired and returned
    total_data_acquire_time = (my_acq_size * (1 / my_adc.sampling_frequency))
    print("{:<50} {:<20}".format("Total Data Acquire Time:", total_data_acquire_time))
    set_timeout = int((total_data_acquire_time * 10000000) + 20000)  # This may be microseconds and not milliseconds
    # print("{:<50} {:<20}".format("Set Timeout Value (ms):", set_timeout/10000)) # can be used optionally
    # my_adc.ctx.set_timeout(set_timeout)
    print("{:<50} {:<20}".format("Set Timeout Value (ms):", "Disabled"))
    my_adc.ctx.set_timeout(0)  # disable iio context timeout

# Depending on the mode of configuration we wish to use, the configuration steps will differ
# "remote_script" copies a script file to a directory on the Zedboard, then runs this script to configure the evb
# the script is passed conditions for the acquisition. Data is acquired and stored on a file on the Zedboard
# named samples.dat. This file is then transferred via SSH
# This can acquire the largest data set, as it mounts a drive to store data, so it is not limited
# to the RAM of the Zedboard
# Ethernet would be preferred here over USB, in case there is a limitation
if config_mode == "remote_script":
    print("Copy Script to Zedboard..........")
    copy_script_file(generic) # this line can be commented after file has been copied once
    print("Configure with remote script.......")
    run_script(generic, (fsamp / 1e6), str(filt_mode), dec_rate)  # script takes frequency in MHz no MHz so div by 1e6
    print('Data source: acquire from ADC via ZedBoard')
    iio_rx_buff_size = 4 * 1024 * 1024  # samples -> default 4194304
    iio_dma_buff_size = 4 * iio_rx_buff_size  # bytes -> default 16777216
    zed_RX_stream = my_acq_size
    zedboard_filepath = '../mnt/samples.dat'
    windows_filepath = ''

    # Create an SSH client
    print('Opening the SSH connection...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the Linux PC
        ssh.connect(hostname_remote, port, username, password)
        print('SSH connection successful!')
        print('Checking temp RAM drive...')
        # Execute the 'df' command to check if the temporary file system is mounted on '/mnt'
        stdin, stdout, stderr = ssh.exec_command('df -h')
        # Read the output of the command
        output = stdout.read().decode()
        print(output)

        # Check if '/mnt' is in the output
        if '/mnt' not in output:
            # Execute the command
            stdin, stdout, stderr = ssh.exec_command('mount -t tmpfs -o size=400m tmpfs /mnt')
            # Check if everything was ok
            error = stderr.read().decode()
            if error:
                print("Error occurred:", error)
            else:
                print('RAM drive created successfully!')
        else:
            print('RAM drive already exists!\n')

        # Execute the command
        print('iio_readdev -u local: -b ' + str(iio_rx_buff_size) + ' -s ' + str(
            zed_RX_stream) + ' ad4880 > ../mnt/samples.dat')
        stdin, stdout, stderr = ssh.exec_command('iio_readdev -u local: -b ' + str(iio_rx_buff_size) + ' -s ' + str(
            zed_RX_stream) + ' ad4880 > ../mnt/samples.dat')
        # Check if everything was ok
        error = stderr.read().decode()
        if 'Success (0)' in error:
            print("Samples Acquired successfully!")
        else:
            print("Error (Ignore?) :", error)

        # Transfer the file from the zedboard
        # Create SCP client
        scp = ssh.open_sftp()
        # Copy the file from zedboard to Windows
        print("Copying file from Zedboard to c:\zedboard_data\samples_zedADC.dat")
        scp.get('/mnt/samples.dat', 'c:\\zedboard_data\\samples_zedADC.dat')
        print("Opening file locally from c:\zedboard_data\samples_zedADC.dat")
        with open('\\zedboard_data\\samples_zedADC.dat', 'rb') as file:
            data = np.frombuffer(file.read(), dtype=np.int32)
            print("Data Acquisition Size: ", len(data))
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your username and password.")
    except paramiko.SSHException as ssh_exception:
        print(f"SSH connection error: {str(ssh_exception)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        # Close the SCP and SSH clients
        scp.close()
        ssh.close()
# "pyadi-iio" uses the pyadi-iio code to configure the evb and the code passed the acquired data directly using
# iio
# The hardware limitation here is the size of the available RAM on the Zedboard.
# There may also be a SW limitation on the iio connection in the transfer. That may lie in Python or remote iio
# drivers of the Zedboard
elif config_mode == "pyadi-iio":
    print("EVB configuration via pyadi-iio..")
    my_pll = adf4350(uri=my_uri, device_name="/axi/spi@e0007000/adf4350@1")
    time.sleep(0.5)
    my_divider = ad9508(uri=my_uri, device_name="ad9508")
    time.sleep(0.5)
    my_one_bit_adc_dac = one_bit_adc_dac(uri=my_uri)
    print("Configure via pyadi-iio............")
    config_ad488x(generic, my_adc, my_adc_b, my_pll, my_divider, my_one_bit_adc_dac, fsamp, filt_mode, dec_rate)
    print('Data source: acquire from ADC')

    # Create an SSH client
    print('Opening the SSH connection...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print('Open SSH...')
        # Connect to the Linux PC
        ssh.connect(hostname_remote, port, username, password)
        print('SSH connection successful!')

        print('Setting ZedBoard dma buffer size...')
        # Execute the command
        stdin, stdout, stderr = ssh.exec_command(
            'echo 335544320 >/sys/module/industrialio_buffer_dma/parameters/max_block_size')
        # Print the output of the command
        print(stdout.read().decode())

        print('Checking ZedBoard dma buffer size...')
        # Execute the command
        stdin, stdout, stderr = ssh.exec_command('cat /sys/module/industrialio_buffer_dma/parameters/max_block_size')
        # Print the output of the command
        print(stdout.read().decode())

        # Check if there was any error during command execution
        # error = stderr.read().decode()
        # if error:
        #    raise Exception(f"Command execution error: {error}")

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your username and password.")
    except paramiko.SSHException as ssh_exception:
        print(f"SSH connection error: {str(ssh_exception)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        # Close the SSH connection
        stdin.close()
        ssh.close()

        # Do the acquisition
        my_adc.rx_enabled = True
        print("Acquiring Data.....")
        data_both_Ch = my_adc.rx()
        data = data_both_Ch[0]
        # my_adc.rx_destroy_buffer()
        my_adc.rx_enabled = False
        my_adc.filter_sel = "disabled"
        time.sleep(0.5)
        my_adc_b.filter_sel = "disabled"
        time.sleep(0.5)

        # save the data
        with open('../phaser/samples_pyADC.dat', 'wb') as file:
            data.tofile(file)

# Load the samples straight from a local file, does not engage the Zedboard
elif config_mode == 'FILE':
    print('Data source: load from file')

    #with open('samples_pyADC.dat', 'rb') as file:
    with open('c:\\zedboard_data\\samples_zedADC.dat', 'rb') as file:
        data = np.frombuffer(file.read(), dtype=np.int32)


# Analyzing the data
data_label = 'test'
adc_res = 20
max_full_scale = 2 ** (adc_res - 1)
min_full_scale = 2 ** (adc_res - 1) * (-1)

###### Print signal parameters ######
print('\n')
print('############ Config checks ############\n')
print('Number of samples:', data.size)
print('Maximum DN:', np.max(data), '->', format(np.max(data) / max_full_scale * 100, '.2f'), '%FS')
print('Maximum DN position:', np.argmax(data))
print('Max value vicinity:', data[np.argmax(data) - 10:np.argmax(data) + 11])
print('Minimum DN:', np.min(data), '->', format(np.min(data) / min_full_scale * 100, '.2f'), '%FS')
print('Minimum DN position:', np.argmin(data))
print('Min value vicinity:', data[np.argmin(data) - 10:np.argmin(data) + 11])
print('\n')

# This is analysis code using genalyzer, this may not run for large acquisitions
# ADC parameters
adc_bits = 20
adc_vref = 3
adc_chs= 1
do_plots=True
do_histograms=True

# Resolve the ODR and BW for the ADC configuration
noise_bw, odr = filter_bw_lookup(fsamp,filt_mode, dec_rate)
# data_array = np.array(data) # sets the format of array for genalyzer, should code genalyzer to make this redundant

# Perform Analysis on the data
if config_mode == 'FILE':
    adc_chs = 2
    genalyzer_data_analysis(data, fsamp, noise_bw, odr, 10e3, adc_bits, (2*adc_vref),adc_chs, do_plots, do_histograms)
else:
    data_a = data[::2]
    data_b = data[1::2]
    adc_chs = 1
    genalyzer_data_analysis(data_a, fsamp, noise_bw, odr, 10e3, adc_bits, (2 * adc_vref), adc_chs, do_plots,
                            do_histograms)
    # clean to close off all in reverse order
    if config_mode == 'pyadi-iio':
        del my_one_bit_adc_dac
        del my_pll
        del my_divider
    # close ADC for all cases other than reading from file
    del my_adc
    del my_adc_b
print("END")