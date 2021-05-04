# Copyright (C) 2019 Analog Devices, Inc.
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

from adi.ad936x import ad9361, ad9363, ad9364, Pluto

from adi.fmcomms5 import FMComms5

from adi.ad9371 import ad9371

from adi.adrv9002 import adrv9002

from adi.adrv9009 import adrv9009

from adi.adrv9009_zu11eg import adrv9009_zu11eg

from adi.adrv9009_zu11eg_multi import adrv9009_zu11eg_multi

from adi.adrv9009_zu11eg_fmcomms8 import adrv9009_zu11eg_fmcomms8

from adi.ad9081 import ad9081

from adi.ad9081_mc import ad9081_mc, QuadMxFE

from adi.ad9094 import ad9094

from adi.ad9680 import ad9680

from adi.ad9136 import ad9136

from adi.ad9144 import ad9144

from adi.ad9152 import ad9152

from adi.cn0532 import cn0532

from adi.daq2 import DAQ2

from adi.daq3 import DAQ3

from adi.adis16460 import adis16460

from adi.adis16507 import adis16507

from adi.ad7124 import ad7124

from adi.adxl345 import adxl345

from adi.adxrs290 import adxrs290

from adi.fmclidar1 import fmclidar1

from adi.ad5686 import ad5686

from adi.adar1000 import adar1000, adar1000_array

from adi.ltc2983 import ltc2983

from adi.one_bit_adc_dac import one_bit_adc_dac

from adi.ltc2314_14 import ltc2314_14

from adi.ad7606 import ad7606

from adi.ad7799 import ad7799

from adi.ad7746 import ad7746

try:
    from adi.jesd import jesd
except ImportError:
    pass

__version__ = "0.0.8"
name = "Analog Devices Hardware Interfaces"
