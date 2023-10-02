import pytest

# ADL5240 isn't in the adi_hardware_map.py in pylibiio
# This value will be changed to change to FMCOMMS11
hardware = ["adl5240"]
classname = "adi.adl5240"


#########################################
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.parametrize(
    "attr, val", [("hardwaregain", [0.06, 0.12, 0.25, 0.5, 0.9],),],
)
def test_adl5240_attr(test_attribute_multiple_values, iio_uri, classname, attr, val):
    test_attribute_multiple_values(iio_uri, classname, attr, val, 0)
