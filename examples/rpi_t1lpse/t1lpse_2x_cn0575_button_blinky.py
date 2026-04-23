# Copyright (C) 2023 Analog Devices Inc.
#
# SPDX short identifier: ADIBSD
from time import sleep

import adi

my_cn0575a = adi.cn0575(uri="ip:192.168.10.2")
my_cn0575b = adi.cn0575(uri="ip:192.168.10.130")

while (1):
    my_cn0575a.led = my_cn0575b.button
    my_cn0575b.led = my_cn0575a.button

    sleep(0.1)