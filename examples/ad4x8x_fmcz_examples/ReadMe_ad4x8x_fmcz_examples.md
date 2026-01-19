# EVAL-AD408x-FMCZ and EVAL-AD488x-FMCZ Examples Scripts
## Description
This guide gives a basic overview of the ad4x8x_fmcz_examples found in this folder. 
These examples are intended to be used with the family of EVAL-AD408x-FMCZ and EVAL-AD488x-FMCZ evaluation boards found on www.analog.com, controlled with a ZedBoard. 
The examples show how to configure and control the sampling clock rate, and the digital filters and ensure will ensure that the LVDS interface to the ZedBoard remains synchronized to the data. The code also uses Genalyzer to perform some basic time domain and frequency domain analysis. A second set of example files included here show a method to increase the size of data acquisition where a large continuous data set is require. 
The code also shows two methods by which the board configuration can be controlled:
1. Setup using only the pyadi-iio scripts remotely (that is from user's PC controlling the HW)
2. Setup using scripts run locally on the attached ZedBoard.

### Important First Step:
It is important that the first step should always be to check the board and your hardware configuration with the ACE software found at https://www.analog.com/en/resources/evaluation-hardware-and-software/evaluation-development-platforms/ace-software.html.
- Please refer to the User Guide for the Evaluation Board found on www.analog.com to correctly set up the board and run ACE
- This step of connecting to ACE is important, both to verify the hardware is set up correctly before running the scripts, but also to correctly set up the required Kuiper Linux kernel and boot files on the ZedBoard's SD card for the specific EVAL-AD4x8x-FMCZ board that you are using. ACE will automatically configure these files on the SD card.
## Installation
- Install the required boot files on the SD Card by connecting the board to ACE and installing the necessary ACE Plug-In as described in the board's User Guide.
- Please first refer to the https://github.com/analogdevicesinc/pyadi-iio/ documentation to install pyadi-iio, then switch to this feature branch.
- Please install the required packages from requirements.txt
- As the analysis is performed by Genalyzer, this must be first installed on your PC. 
    - The genalyzer-setup.exe installer for the required support files can be found at https://github.com/analogdevicesinc/genalyzer/releases
    - Information about the python package can be found here https://analogdevicesinc.github.io/genalyzer/master/setup.html

## Usage
There are 4 examples files provided:
1. ad408x_script_example.py: Script to configure the FMCZ Evaluation Board and perform basic analysis.
2. ad488x_script_example.py: Same as above but for AD4880 family of products
3. ad408x_example_large_dataset.py: Script to configure the FMCZ Evaluation Board and save up to 80M conversion results.
4. ad488x_example_large_dataset.py: Same as above but for AD4880 family of products

### For ad4x8x_script_example files
To use the code the following variables can be configured as per the attached hardware and your requirements, limited to 50M conversion results as dual channel device requires more memory.

```py
generic = "ad4080"
# Optionally pass URI as command line argument,
# else use default ip:analog.local

# if len(sys.argv) < 3:
#     print("Usage: script.py <my_uri> <Fsamp> [FiltMode] [DecRate]")
#     sys.exit(1)

my_uri = "ip:analog.local"  # my_uri = "ip:analog.local"  # Default URI
fsamp = 40e6            # Default Sampling Frequency entered in Hz
print("{:<50} {:<20}".format("Configuring for sampling frequency of: ", fsamp))
config_mode = "pyadi-iio"  # "pyadi-iio" = configure the evb via python. "remote_script": configure with bash script
# option can be set to copy a script and configure the evb from a script running on the Zedboard
# or configure the board via pyi-adi-iio
filt_mode = "disabled"   # Filter Mode options: "disabled", "sinc1", "sinc5", "sinc5_plus_compensation"
# Refer to Datasheet for options available to each Filter Mode
dec_rate = 2         # Set Decimation Rate Options: 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024

# Blank line

# Setting how many conversions results to take
my_acq_size = 2 ** 18
```
Where here the "generic" variable can be used to set which board product you are using, for example if you are using the EVAL-AD4080-FMCZ board you must set the variable as "ad4080"

```py
generic = "ad4080"
```

The "fsamp" variable can be modified if you wish to change the sampling clock frequency. The scripts will the take care of setting the adf4350 pll and the ad9508 clock divider, as well as re-synchronizing the LVDS interface.
The maximum "fsamp" value that can be set is determined by the product. For example AD4884 has a maximum allow f<sub>S</sub> of 20 MHz so "fsamp" should not be set above this value. For ad4080 it can be set up to 40 MHz
```py
fsamp = 40e6            # Default Sampling Frequency entered in Hz
```
The "config_mode" selects by which method the evaluation board will be configured. The available options are listed in the code:
1. "pyadi-iio" The device driver attributes on the ZedBoard are configure using the python pyadi-iio scripts. This uses the ad4080.py or ad4880.py files.
2. "remote_script" (name may be misleading) a bash script from the "script" folder on the remote PC running the python code is copied to the Kuiper Linux OS, that is to the SD Card of the ZedBoard. This script is then run. (The script is set run remotely, although the control is performed "local" to EVAL- board) 

```py
config_mode = "pyadi-iio"  # "pyadi-iio" = configure the evb via python. "remote_script": configure with bash script
# option can be set to copy a script and configure the evb from a script running on the Zedboard
# or configure the board via pyi-adi-iio
```

The following lines of code show the variables that can be configured to control the integrated digital filter.
Note that when filt_mode = "disabled" the dec_rate variable has no effect.
Note also, as per datasheets that valid settings for "sinc5_plus_compensation" are from 2 to 256

```py
filt_mode = "disabled"   # Filter Mode options: "disabled", "sinc1", "sinc5", "sinc5_plus_compensation"
# Refer to Datasheet for options available to each Filter Mode
dec_rate = 2    
```

The number of conversion results to be acquired can be set by the following:
```py 
# Setting how many conversions results to take
my_acq_size = 2 ** 18
```
Towards the end of the script, it is possible also to configure the "do_plots" and "do_histogram" variables. These can be set to "False" if you wish to not display the results
Note "do_histogram" is set to "False" by default, note that enabling this, for sine wave inputs (or for any signal that will have a large distribution of codes) it may be necessary to reduce the size of the data acquisition as processing and displaying a large histogram may take a long time. 

```py 
adc_resolution = resolve_generic(generic)[2] # returns only the resolution from the resolve function
print("ADC Resolution:", adc_resolution)
# ADC parameters
adc_bits = adc_resolution # ADC resolution
adc_vref = 3 # VRef Voltage
adc_chs= 1 # AD408x are single channel devices
do_plots=True # Show FFT, Time Domain and Analysis plots
do_histograms=False # show histogram of codes
```

