# Copyright (C) 2025 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# import sys
import time
import numpy as np
from adi import ad4880, ad9508, adf4350, one_bit_adc_dac
from ad4x8x_eval_fmcz_config import config_ad488x, filter_bw_lookup, run_script, copy_script_file, resolve_generic
from ad4x8x_genalyzer import genalyzer_data_analysis

generic = "ad4884"
# Optionally pass URI as command line argument,
# else use default ip:analog.local

# if len(sys.argv) < 3:
#     print("Usage: script.py <my_uri> <Fsamp> [FiltMode] [DecRate]")
#     sys.exit(1)

my_uri = "ip:analog.local"  # Default URI
fsamp = 20e6            # Default Sampling Frequency entered in Hz
print("{:<50} {:<20}".format("Configuring for sampling frequency of: ", fsamp))
# option can be set to copy a script and configure the evb from a script running on the Zedboard
# or configure the board via pyi-adi-iio
config_mode = "remote_script"  # "pyadi-iio" = configure the evb via python. "remote_script": configure with bash script
filt_mode = "sinc1"   # Filter Mode options: "disabled", "sinc1", "sinc5", "sinc5_plus_compensation"
# Refer to Datasheet for options available to each Filter Mode
dec_rate = 2             # Set Decimation Rate Options: 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024

gain = 1.03  # Sets default gain for the eval-ad488x-fmcz board

# Setting how many conversions results to take
my_acq_size = 2 ** 20

print("{:<50} {:<20}".format("Opening connection to Zedboard at: ", my_uri))
# Establish connections to the FMC board devices
print("Connection opening...................")
my_adc = ad4880(uri=my_uri, device_name=generic)
time.sleep(0.5)
my_adc_b = ad4880(uri=my_uri, device_name=generic +"_chb")
print("Connection established...............")
print("{:<50} {:<20}".format("Lsb Size:", my_adc.channel[0].scale))   # Not necessary, just early check of device tree
time.sleep(0.5)

# Configuring how many conversions results to take
my_adc.rx_buffer_size = my_acq_size

if config_mode == "remote_script":
    print("Copy Script to Zedboard..........")
    copy_script_file(generic) # this line can be commented after file has been copied once
    print("Configure with remote script.......")
    run_script(generic, (fsamp / 1e6), str(filt_mode), dec_rate)  # script takes frequency in MHz no MHz so div by 1e6
if config_mode == "pyadi-iio":
    print("EVB configuration via pyadi-iio..")
    my_pll = adf4350(uri=my_uri, device_name="/axi/spi@e0007000/adf4350@1")
    time.sleep(0.5)
    my_divider = ad9508(uri=my_uri, device_name="ad9508")
    time.sleep(0.5)
    my_one_bit_adc_dac = one_bit_adc_dac(uri=my_uri)
    print("Configure via pyadi-iio............")
    config_ad488x(generic, my_adc, my_adc_b, my_pll, my_divider, my_one_bit_adc_dac, fsamp, filt_mode, dec_rate)

# Set timeout for Output Data Rate and number of results being acquired and returned
total_data_acquire_time = (my_acq_size * (1/my_adc.sampling_frequency))
print("{:<50} {:<20}".format("Total Data Acquire Time:", total_data_acquire_time))
set_timeout = int((total_data_acquire_time*10000) + 60000)  # This may be microseconds and not milliseconds
print("{:<50} {:<20}".format("Set Timeout Value (s):", set_timeout/10000)) # can be used optionally
my_adc.ctx.set_timeout(set_timeout)
print("{:<50} {:<20}".format("Set Timeout Value (ms):", "Disabled"))
my_adc.ctx.set_timeout(0)  # disable iio context timeout

print("Acquiring Data.....")
data = my_adc.rx()
time.sleep(0.5)
my_adc.filter_sel = "disabled"
time.sleep(0.5)
my_adc_b.filter_sel = "disabled"

adc_resolution = resolve_generic(generic)[2] # returns only the resolution from the resolve function
print("ADC Resolution:", adc_resolution)
# ADC parameters
adc_bits = adc_resolution # ADC resolution
adc_vref = 3 # VRef Voltage
adc_chs= 2  # AD488x are dual channel devices
do_plots=True  # Show FFT, Time Domain and Analysis plots
do_histograms=False # Show Histogram of codes

# Resolve the ODR and BW for the ADC configuration
noise_bw, odr = filter_bw_lookup(my_adc.sampling_frequency,filt_mode, dec_rate)
# data_array = np.array(data) # sets the format of array for genalyzer, should code genalyzer to make this redundant

# Perform Analysis on the data
genalyzer_data_analysis(data, my_adc.sampling_frequency, noise_bw, odr, 10e3, adc_bits, (2*adc_vref),adc_chs, do_plots, do_histograms)

# clean to close off all in reverse order
if config_mode == 'pyadi-iio':
    del my_one_bit_adc_dac
    del my_pll
    del my_divider
# close ADC for all cases
del my_adc
del my_adc_b