# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse
from time import sleep

import adi

# Set up AD7124
# Optionally pass URI as command line argument with -u option,
# else use default to "ip:analog.local"
parser = argparse.ArgumentParser(description="AD7124 Example Script")
parser.add_argument(
    "-u",
    default="ip:analog.local",
    help="-u (arg) URI of target device's context, eg: 'ip:analog.local',\
    'ip:192.168.2.1',\
    'serial:COM4,115200,8n1n'",
    action="store",
)

parser.add_argument(
    "-v", "--verbose", default=False, help="Enable verbose output", action="store_true",
)

args = parser.parse_args()
my_uri = args.u
verbose = args.verbose

print("uri: " + str(my_uri))

my_ad7124 = adi.ad7124(uri=my_uri)
my_ad7124.rx_destroy_buffer()


sampling_frequency = 19200
filter_type = "sinc3"

for i in range(0, len(my_ad7124.channel)):
    my_ad7124.channel[i].sampling_frequency = 4800

print(
    "Welcome to the ad7124 example script, where the local temperature is ",
    my_ad7124.temp(),
    " degrees C.",
)


print("setting sample rate of all channels to ", sampling_frequency)
print("setting filter type of all channels to ", filter_type)
print("AD7124 channels:")


for i in range(0, len(my_ad7124.channel)):
    my_ad7124.channel[i].sampling_frequency = sampling_frequency
    my_ad7124.channel[i].filter_type = filter_type
    print("channel ", i, " name: ", my_ad7124.channel[i].name)


print("Now reading out all raw channels...")

for i in range(0, len(my_ad7124.channel)):
    print("Channel ", i, ":  ", my_ad7124.channel[i].raw)
    sleep(0.1)


my_ad7124.rx_enabled_channels = [1, 2, 3, 4, 5, 6, 7, 8]


sleep(0.1)


ad_channel0 = 1  # voltage0-voltage1 plug to CH1 on my m2k
ad_channel1 = 2  # voltage2-voltage3 plug to CH2 on my m2k

sc = my_ad7124.channel[1].scale_available

my_ad7124.channel[ad_channel0].scale = sc[-1]  # get highest range
my_ad7124.channel[ad_channel1].scale = sc[-1]  # get highest range


my_ad7124.rx_output_type = "SI"
# sets sample rate for all enabled

my_ad7124.channel[ad_channel0].sampling_frequency = 4800
my_ad7124.channel[ad_channel1].sampling_frequency = 4800

my_ad7124.rx_enabled_channels = [ad_channel0, ad_channel1]
my_ad7124.rx_buffer_size = 100
my_ad7124._ctx.set_timeout(100000)

data = my_ad7124.rx()

print(data)

if verbose is True:
    import matplotlib.pyplot as plt

    plt.figure(1)
    plt.title(
        f"{my_ad7124._ctrl.name} @{my_ad7124.channel[ad_channel0].sampling_frequency}sps"
    )
    plt.ylabel("Volts")
    plt.xlabel("Sample Number")
    plt.plot(
        data[0], label=my_ad7124.channel[ad_channel0].name, color="orange", linewidth=2
    )
    plt.plot(
        data[1], label=my_ad7124.channel[ad_channel1].name, color="blue", linewidth=2
    )
    plt.show()

del my_ad7124
