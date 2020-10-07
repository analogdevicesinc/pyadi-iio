import iio
import pprint
import pytest

hardware = ["pluto", "adrv9361", "fmcomms2"]
classname = ""


def get_states(ctx, devices_to_ignore=None, show_skipped=False):
    # Read all attributes in to flattened structure
    state = {}
    for device in ctx.devices:
        if str(device.name) in devices_to_ignore:
            continue
        state[device.name] = {}
        # Get device attributes
        for attr in device.attrs:
            # print(attr)
            try:
                state[device.name][attr] = device.attrs[attr].value
            except OSError:
                if show_skipped:
                    print("Skipped {} {}".format(device.name, attr))
                continue
        # Get channel attributes
        for channel in device.channels:
            # if channel.name:
            #     c_name = str(channel.name) + "_out" if channel.output else "_in"
            # else:
            c_name = "out" if channel.output else "in"
            c_name += "_" + str(channel.id)
            state[device.name][c_name] = {}
            for attr in channel.attrs:
                # print(attr)
                try:
                    # print(c_name)
                    state[device.name][c_name][attr] = channel.attrs[attr].value
                except OSError:
                    if show_skipped:
                        print(
                            "Skipped {} {} {}".format(device.name, channel.name, attr)
                        )
                    continue
    return state


def compare_dictionaries(dict_1, dict_2, dict_1_name, dict_2_name, path=""):
    err = ""
    key_err = ""
    value_err = ""
    old_path = path
    for k in dict_1.keys():
        path = old_path + "[%s]" % k
        if k not in dict_2:
            pass
            # key_err += "Key %s%s\nnot in %s\n" % (dict_2_name, path, dict_2_name)
        else:
            if isinstance(dict_1[k], dict) and isinstance(dict_2[k], dict):
                err += compare_dictionaries(
                    dict_1[k], dict_2[k], dict_1_name, dict_2_name, path
                )
            else:
                if dict_1[k] != dict_2[k]:
                    value_err += "Value of %s%s (%s)\n-------- %s%s (%s)\n" % (
                        dict_1_name,
                        path,
                        dict_1[k],
                        dict_2_name,
                        path,
                        dict_2[k],
                    )

    for k in dict_2.keys():
        path = old_path + "[%s]" % k
        if k not in dict_1:
            key_err += "Key %s%s not in %s\n" % (dict_2_name, path, dict_1_name)

    return key_err + value_err + err


def get_attrs(diff_str):
    lines = diff_str.split("\n")
    odds = lines[::2]
    odds = odds[:-1]
    attr_trees = []
    for line in odds:
        attr_tree = ""
        b1 = line.split("[")
        c = 0
        for b in b1:
            if "]" in b:
                c += 1
                d = b.split("]")[0]
                attr_tree += d + "_"
                if c == 3:
                    break
        attr_trees.append(attr_tree[:-1])

    return attr_trees


def compare_states(state1, state2, expected_to_change, allowed_to_change):
    a = compare_dictionaries(state1, state2, "state1", "state2")
    if a:
        print("\n--Found attribute differences:--")
        print(a)
        delta_attrs = get_attrs(a)
        for attr in delta_attrs:
            if attr not in expected_to_change and attr not in allowed_to_change:
                raise Exception("Unexpected attribute change: " + attr)
        for attr in expected_to_change:
            if attr not in delta_attrs:
                raise Exception("Expected attribute change not found: " + attr)
    else:
        print("\nNo found attribute differences:\n", a)
        if expected_to_change:
            raise Exception("Expected changed attributes did not change")


def test_attribute_changes(contexts):

    ctx = None
    for ctx_desc in contexts:
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
