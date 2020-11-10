from test.generics import compare_states, get_states, iio_buffer_check

import iio

import pytest

hardware = ["pluto", "adrv9361", "fmcomms2"]
classname = ""


#########################################
# fmt: off
@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "attrtype, dev_name, chan_name, inout, attr, start, stop, step, tol, repeats",
    [
        ("channel","ad9361-phy","voltage0",False,"hardwaregain",-89.75,0.0,0.25,0,100,),
        ("channel","ad9361-phy","TX_LO",True,"frequency",47000000,6000000000,1,4,100,),
        ("channel","ad9361-phy","RX_LO",True,"frequency",70000000,6000000000,1,4,100,),
    ],
)
def test_iio_attr(
    test_iio_attribute_single_value,iio_uri,attrtype,dev_name,chan_name,inout,
    attr,start,stop,step,tol,repeats,
):
    test_iio_attribute_single_value(
        iio_uri,attrtype,dev_name,chan_name,inout,
        attr,start,stop,step,tol,repeats,
    )
# fmt: on

#########################################
@pytest.mark.iio_hardware(hardware)
def test_attribute_changes(context_desc):

    ctx = None
    for ctx_desc in context_desc:
        if ctx_desc["hw"] in hardware:
            ctx = iio.Context(ctx_desc["uri"])
    if not ctx:
        pytest.skip("No valid hardware found")

    drivers_to_ignore = "xadc"

    # Set initial state
    ctx.find_device("ad9361-phy").find_channel("RX_LO").attrs[
        "frequency"
    ].value = "1000000000"
    ctx.find_device("ad9361-phy").find_channel("TX_LO").attrs[
        "frequency"
    ].value = "1000000000"

    # Collect state of all attributes
    state1 = get_states(ctx, drivers_to_ignore)

    # Change LOs
    ctx.find_device("ad9361-phy").find_channel("RX_LO").attrs[
        "frequency"
    ].value = "2000000000"
    ctx.find_device("ad9361-phy").find_channel("TX_LO").attrs[
        "frequency"
    ].value = "2000000000"

    # Collect state of all attributes after change
    state2 = get_states(ctx, drivers_to_ignore)

    # Set up comparison
    expected_to_change = [
        "ad9361-phy_out_altvoltage0_frequency",
        "ad9361-phy_out_altvoltage1_frequency",
    ]
    allowed_to_change = [
        "ad7291_in_temp0_mean_raw",
        "ad7291_in_temp0_raw",
        "ad9361-phy_in_temp0_input",
        "ad9361-phy_in_voltage0_hardwaregain",
        "ad9361-phy_in_voltage1_hardwaregain",
        "ad9361-phy_in_voltage2_raw",
        "ad9361-phy_in_voltage0_rssi",
        "ad9361-phy_in_voltage1_rssi",
        "ad9361-phy_in_voltage0_hardwaregain_available",
        "ad9361-phy_in_voltage1_hardwaregain_available",
    ]
    for k in range(6):
        allowed_to_change.append("ad7291_in_voltage{}_raw".format(k))

    compare_states(state1, state2, expected_to_change, allowed_to_change)


#########################################


@pytest.mark.parametrize("percent_fail", [(0.1)])
@pytest.mark.iio_hardware(hardware)
def test_iio_buffer_check(single_ctx_desc, percent_fail):
    iio_buffer_check(
        "ad9361-phy", "cf-ad9361-lpc", single_ctx_desc["uri"], percent_fail
    )
