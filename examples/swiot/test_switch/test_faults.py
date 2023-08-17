import pytest
import adi
from examples.swiot import swiot_utils, constants
from time import sleep

@pytest.mark.parametrize(
    "configuration",
    [[
        ["ad74413r", "voltage_out"],
        ["ad74413r", "voltage_out"],
        ["ad74413r", "voltage_out"],
        ["ad74413r", "voltage_out"]
    ]]
)
def test_ad74413r_voltage_out_short_circuits(configuration: list):
    """
    In voltage output mode, the VI_ERR_X bit will assert if the sourced current
    exceeds 29 mA on the X channel. As such, this may be used to check for shorts
    to GND. The output voltage is arbitrary, but should be a non 0 value (or close
    to 0). The device's channels should be left floating.
    """
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    ad74413r = adi.ad74413r(uri=constants.URI)

    ad74413r.channel["voltage0"].raw = 4096
    ad74413r.channel["voltage1"].raw = 4096
    ad74413r.channel["voltage2"].raw = 4096
    ad74413r.channel["voltage3"].raw = 4096

    faults = ad74413r.reg_read(0x2E)
    faults = faults & 0xF

    assert faults == 0x0

@pytest.mark.parametrize(
    "configuration",
    [[
        ["ad74413r", "voltage_out"],
        ["ad74413r", "voltage_out"],
        ["ad74413r", "voltage_out"],
        ["ad74413r", "voltage_out"]
    ]]
)
def test_ad74413r_supply_faults(configuration: list):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    ad74413r = adi.ad74413r(uri=constants.URI)

    faults = ad74413r.reg_read(0x2E)
    faults = (faults & 0x3C) >> 6

    assert faults == 0x0

@pytest.mark.parametrize(
    "configuration",
    [[
        ["ad74413r", "current_out"],
        ["ad74413r", "current_out"],
        ["ad74413r", "current_out"],
        ["ad74413r", "current_out"]
    ]]
)
def test_ad74413r_voltage_out_open_circuits(configuration: list):
    """
    Verify that the AD74413R will assert the VI_ERR_X bits when an open wire is
    detected. All the channels should be left floating.
    """
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    ad74413r = adi.ad74413r(uri=constants.URI)

    ad74413r.channel["current0"].raw = 4096
    ad74413r.channel["current1"].raw = 4096
    ad74413r.channel["current2"].raw = 4096
    ad74413r.channel["current3"].raw = 4096

    faults = ad74413r.reg_read(0x2E)
    faults = faults & 0xF

    assert faults == 0xF

@pytest.mark.parametrize(
    "configuration",
    [[
        ["max14906", "output"],
        ["max14906", "output"],
        ["max14906", "output"],
        ["max14906", "output"]
    ]]
)
def test_max14906_global_err(configuration: list):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    max14906 = adi.max14906(uri=constants.URI)

    faults = max14906.reg_read(0x07)

    assert faults == 0x0

@pytest.mark.parametrize(
    "configuration",
    [[
        ["max14906", "output"],
        ["max14906", "output"],
        ["max14906", "output"],
        ["max14906", "output"]
    ]]
)
def test_max14906_short_vdd_err(configuration: list):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    max14906 = adi.max14906(uri=constants.URI)

    max14906.reg_write(0x09, 0x0F)

    max14906.channel["voltage0"].raw = 0
    max14906.channel["voltage1"].raw = 0
    max14906.channel["voltage2"].raw = 0
    max14906.channel["voltage3"].raw = 0

    max14906.channel["voltage0"].do_mode = "High_side"
    max14906.channel["voltage1"].do_mode = "High_side"
    max14906.channel["voltage2"].do_mode = "High_side"
    max14906.channel["voltage3"].do_mode = "High_side"

    faults = max14906.reg_read(0x06)
    faults = faults & 0x0F

    assert faults == 0x0

@pytest.mark.parametrize(
    "configuration",
    [[
        ["max14906", "output"],
        ["max14906", "output"],
        ["max14906", "output"],
        ["max14906", "output"]
    ]]
)
def test_max14906_short_gnd_err(configuration: list):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    max14906 = adi.max14906(uri=constants.URI)

    max14906.channel["voltage0"].raw = 1
    max14906.channel["voltage1"].raw = 1
    max14906.channel["voltage2"].raw = 1
    max14906.channel["voltage3"].raw = 1

    faults = max14906.reg_read(0x04)
    faults = (faults & 0xF0) >> 4

    assert faults == 0x0

@pytest.mark.parametrize(
    "configuration",
    [[
        ["max14906", "high_z"],
        ["max14906", "high_z"],
        ["max14906", "high_z"],
        ["max14906", "high_z"]
    ]]
)
def test_max14906_open_wire_err(configuration: list):
    swiot = swiot_utils.setup_config_mode(configuration=configuration)
    max14906 = adi.max14906(uri=constants.URI)

    max14906.reg_write(0xA, 0x3)
    max14906.reg_write(0x1, 0xFF)

    return 0

