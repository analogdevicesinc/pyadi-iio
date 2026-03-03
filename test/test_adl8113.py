# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import pytest

hardware = "adl8113"
classname = "adi.adl8113"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [classname])
@pytest.mark.parametrize(
    "attr, val", [("hardwaregain", [14, -2]),],
)
def test_adl8113_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)
