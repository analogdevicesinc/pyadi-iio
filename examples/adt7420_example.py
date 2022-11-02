# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 08:00:03 2022

@author: jsanbuen
"""

import adi 

adt7420 = adi.adt7420_trial(uri="")

print('Max Temperature Threshold = ' + str(adt7420.temp_max))
print('Min Temperature Threshold = ' + str(adt7420.temp_min))
print('Crit Temperature Threshold = ' + str(adt7420.temp_crit))
print('Hysteresis Temperature Setting = ' + str(adt7420.temp_hyst))

datapoints = 10
for i in range(datapoints):
    print('Temperature Measurement ' + str(i + 1) + ' = ' + str(adt7420.temp) )
