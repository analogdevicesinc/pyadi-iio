# Copyright (C) 2019-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.ad2s1210 import ad2s1210
from adi.ad469x import ad469x
from adi.ad578x import ad578x
from adi.ad717x import ad717x
from adi.ad719x import ad719x
from adi.ad777x import ad777x
from adi.ad936x import Pluto, ad9361, ad9363, ad9364
from adi.ad4020 import ad4020
from adi.ad4110 import ad4110
from adi.ad4130 import ad4130
from adi.ad4630 import ad4630
from adi.ad4858 import ad4858
from adi.ad5592r import ad5592r
from adi.ad5686 import ad5686
from adi.ad5754r import ad5754r
from adi.ad5940 import ad5940
from adi.ad6676 import ad6676
from adi.ad7124 import ad7124
from adi.ad7291 import ad7291
from adi.ad7606 import ad7606
from adi.ad7689 import ad7689
from adi.ad7746 import ad7746
from adi.ad7768 import ad7768, ad7768_4
from adi.ad7768_1 import ad7768_1
from adi.ad7799 import ad7799
from adi.ad9081 import ad9081
from adi.ad9081_mc import QuadMxFE, ad9081_mc
from adi.ad9083 import ad9083
from adi.ad9084 import ad9084
from adi.ad9084_mc import Triton, ad9084_mc
from adi.ad9094 import ad9094
from adi.ad9136 import ad9136
from adi.ad9144 import ad9144
from adi.ad9152 import ad9152
from adi.ad9162 import ad9162
from adi.ad9166 import ad9166
from adi.ad9172 import ad9172
from adi.ad9250 import ad9250
from adi.ad9265 import ad9265
from adi.ad9371 import ad9371
from adi.ad9434 import ad9434
from adi.ad9467 import ad9467
from adi.ad9625 import ad9625
from adi.ad9680 import ad9680
from adi.ada4961 import ada4961
from adi.adaq8092 import adaq8092
from adi.adar1000 import adar1000, adar1000_array
from adi.adf4159 import adf4159
from adi.adf4355 import adf4355
from adi.adf4371 import adf4371
from adi.adf5610 import adf5610
from adi.adg2128 import adg2128
from adi.adis16460 import adis16460
from adi.adis16475 import adis16475
from adi.adis16495 import adis16495
from adi.adis16507 import adis16507
from adi.adl5240 import adl5240
from adi.adl5960 import adl5960
from adi.admv8818 import admv8818
from adi.adpd188 import adpd188
from adi.adpd410x import adpd410x
from adi.adpd1080 import adpd1080
from adi.adrf5720 import adrf5720
from adi.adrv9002 import adrv9002
from adi.adrv9009 import adrv9009
from adi.adrv9009_zu11eg import adrv9009_zu11eg
from adi.adrv9009_zu11eg_fmcomms8 import adrv9009_zu11eg_fmcomms8
from adi.adrv9009_zu11eg_multi import adrv9009_zu11eg_multi
from adi.adt7420 import adt7420
from adi.adxl313 import adxl313
from adi.adxl345 import adxl345
from adi.adxl355 import adxl355
from adi.adxrs290 import adxrs290
from adi.cn0511 import cn0511
from adi.cn0532 import cn0532
from adi.cn0554 import cn0554
from adi.cn0566 import CN0566
from adi.cn0575 import cn0575
from adi.cn0579 import cn0579
from adi.daq2 import DAQ2
from adi.daq3 import DAQ3
from adi.fmc_vna import fmcvna
from adi.fmcadc3 import fmcadc3
from adi.fmcjesdadc1 import fmcjesdadc1
from adi.fmclidar1 import fmclidar1
from adi.fmcomms5 import FMComms5
from adi.fmcomms11 import FMComms11
from adi.gen_mux import genmux
from adi.lm75 import lm75
from adi.ltc2314_14 import ltc2314_14
from adi.ltc2387 import ltc2387
from adi.ltc2499 import ltc2499
from adi.ltc2688 import ltc2688
from adi.ltc2983 import ltc2983
from adi.max9611 import max9611
from adi.max11205 import max11205
from adi.max14001 import max14001
from adi.max31855 import max31855
from adi.max31865 import max31865
from adi.one_bit_adc_dac import one_bit_adc_dac
from adi.QuadMxFE_multi import QuadMxFE_multi
from adi.tdd import tdd

try:
    from adi.jesd import jesd
except ImportError:
    pass

__version__ = "0.0.17"
name = "Analog Devices Hardware Interfaces"
