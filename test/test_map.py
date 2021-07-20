from os import sendfile


def get_test_map():
    # Keys are substrings of test function names (and usually filenames)
    # Any board-fmc name will run a specific tests with key as name

    # NO TESTS YET
    # zynq-zc702-adv7511
    # zynq-zc706-adv7511-fmcadc4
    # zynq-zc706-adv7511-fmcomms11
    # zynq-zc706-adv7511-ad9625-fmcadc2
    #
    #
    # zynq-zed-adv7511-ad9467-fmc-250ebz
    # zynq-zc706-adv7511-ad9625-fmcadc3
    #
    # zynq-zed-adv7511-cn0363
    # zynq-zc706-adv7511-ad6676-fmc
    #
    # zynq-zc706-adv7511-ad9265-fmc-125ebz
    # zynq-zc706-adv7511-ad9434-fmc-500ebz
    # zynq-zed-adv7511
    # zynq-zc706-adv7511-ad9739a-fmc
    # zynq-zed-imageon
    # zynq-zc706-adv7511-fmcdaq3-revC
    # zynq-zc706-adv7511-fmcjesdadc1
    # zynq-zed-adv7511-fmcmotcon2
    # zynq-zc706-adv7511

    test_map = {}
    test_map["daq3"] = ["zynqmp-zcu102-rev10-fmcdaq3"]
    test_map["ad9152"] = ["zynqmp-zcu102-rev10-fmcdaq3"]
    test_map["daq2"] = ["zynq-zc706-adv7511-fmcdaq2", "zynqmp-zcu102-rev10-fmcdaq2"]
    test_map["ad9144"] = ["zynq-zc706-adv7511-fmcdaq2", "zynqmp-zcu102-rev10-fmcdaq2"]
    test_map["ad9680"] = ["zynq-zc706-adv7511-fmcdaq2", "zynqmp-zcu102-rev10-fmcdaq2"]
    test_map["adrv9371"] = [
        "zynqmp-zcu102-rev10-adrv9371",
        "zynq-zc706-adv7511-adrv9371",
        "socfpga_arria10_socdk_adrv9371",
    ]
    test_map["adrv9009"] = [
        "socfpga_arria10_socdk_adrv9009",
        "zynqmp-zcu102-rev10-adrv9008-1",
        "zynqmp-zcu102-rev10-adrv9008-2",
        "zynqmp-zcu102-rev10-adrv9009",
    ]
    test_map["fmcomms5"] = [
        "zynqmp-zcu102-rev10-ad9361-fmcomms5",
        "zynq-zc702-adv7511-ad9361-fmcomms5",
        "zynq-zc706-adv7511-ad9361-fmcomms5",
        "zynq-zc706-adv7511-ad9361-fmcomms5-ext-lo-adf5355",
    ]
    test_map["pluto"] = ["pluto"]
    test_map["ad9361"] = [
        "socfpga_cyclone5_sockit_arradio",
        "zynq-zed-adv7511-ad9361-fmcomms2-3",
        "zynq-zc702-adv7511-ad9361-fmcomms2-3",
        "zynq-zc706-adv7511-ad9361-fmcomms2-3",
        "zynqmp-zcu102-rev10-ad9361-fmcomms2-3",
        "zynq-adrv9361-z7035-fmc",
        "zynq-adrv9361-z7035-box",
        "zynq-adrv9361-z7035-bob",
        "zynq-adrv9361-z7035-bob-cmos",
    ] + test_map["fmcomms5"]
    test_map["ad9364"] = [
        "socfpga_cyclone5_sockit_arradio",
        "zynq-zc702-adv7511-ad9364-fmcomms4",
        "zynq-zc706-adv7511-ad9364-fmcomms4",
        "zynqmp-zcu102-rev10-ad9364-fmcomms4",
        "zynq-adrv9364-z7020-box",
        "zynq-adrv9364-z7020-bob",
        "zynq-adrv9364-z7020-bob-cmos",
        "zynq-zed-adv7511-ad9364-fmcomms4",
    ]
    test_map["adrv9002"] = [
        "zynq-zc706-adv7511-adrv9002",
        "zynq-zc706-adv7511-adrv9002-rx2tx2",
        "zynq-zed-adv7511-adrv9002",
        "zynq-zed-adv7511-adrv9002-rx2tx2",
        "zynqmp-zcu102-rev10-adrv9002",
        "zynqmp-zcu102-rev10-adrv9002-rx2tx2",
    ]

    return test_map
