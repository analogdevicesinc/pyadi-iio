"""Update device classes to reflect all component classes"""

import glob
import os

CATEGORIES = {
    "Transceivers": [
        "adi.ad936x",
        "adi.ad937x",
        "adi.adrv9002",
        "adi.adrv9009",
        "adi.adrv9009_zu11eg",
        "adi.adrv9009_zu11eg_fmcomms8",
        "adi.adrv9009_zu11eg_multi",
    ],
    "High-Speed Converters": [
        "adi.ad6676",
        "adi.ad9081",
        "adi.ad9081_mc",
        "adi.ad9083",
        "adi.ad9084",
        "adi.ad9084_mc",
        "adi.ad9094",
        "adi.ad9136",
        "adi.ad9144",
        "adi.ad9152",
        "adi.ad9162",
        "adi.ad9166",
        "adi.ad9172",
        "adi.ad9213",
        "adi.ad9250",
        "adi.ad9265",
        "adi.ad9434",
        "adi.ad9467",
        "adi.ad9625",
        "adi.ad9680",
        "adi.ad9739a",
        "adi.QuadMxFE_multi",
    ],
    "Precision ADCs": [
        "adi.ad4020",
        "adi.ad405x",
        "adi.ad4080",
        "adi.ad4110",
        "adi.ad4130",
        "adi.ad4170",
        "adi.ad4630",
        "adi.ad469x",
        "adi.ad4858",
        "adi.ad7124",
        "adi.ad7134",
        "adi.ad717x",
        "adi.ad719x",
        "adi.ad7291",
        "adi.ad738x",
        "adi.ad7405",
        "adi.ad7490",
        "adi.ad7606",
        "adi.ad7689",
        "adi.ad7768",
        "adi.ad777x",
        "adi.ad7799",
        "adi.ltc2314_14",
        "adi.ltc2378",
        "adi.ltc2387",
        "adi.ltc2499",
        "adi.ltc2983",
        "adi.max11205",
    ],
    "Precision DACs": [
        "adi.ad353xr",
        "adi.ad3552r",
        "adi.ad3552r_hs",
        "adi.ad5592r",
        "adi.ad5627",
        "adi.ad5686",
        "adi.ad5706r",
        "adi.ad5710r",
        "adi.ad5754r",
        "adi.ad579x",
        "adi.ltc2664",
        "adi.ltc2672",
        "adi.ltc2688",
    ],
    "Sensors and Health": [
        "adi.adpd1080",
        "adi.adpd188",
        "adi.adpd410x",
        "adi.adt7420",
        "adi.adxl313",
        "adi.adxl345",
        "adi.adxl355",
        "adi.adxl380",
        "adi.adxrs290",
        "adi.adis16375",
        "adi.adis16460",
        "adi.adis16475",
        "adi.adis16480",
        "adi.adis16485",
        "adi.adis16488",
        "adi.adis16490",
        "adi.adis16495",
        "adi.adis16497",
        "adi.adis16507",
        "adi.adis16545",
        "adi.adis16547",
        "adi.adis16550",
        "adi.ad5940",
        "adi.max31855",
        "adi.max31865",
        "adi.max9611",
    ],
    "RF and Microwave": [
        "adi.adl5240",
        "adi.adl5960",
        "adi.adl8113",
        "adi.admv8818",
        "adi.adrf5720",
        "adi.adar1000",
        "adi.adf4030",
        "adi.adf4159",
        "adi.adf4355",
        "adi.adf4371",
        "adi.adf4377",
        "adi.adf4382",
        "adi.adf5610",
        "adi.adf5611",
        "adi.cn0511",
    ],
    "Development Systems and Modules": [
        "adi.cn0532",
        "adi.cn0540",
        "adi.cn0554",
        "adi.cn0556",
        "adi.cn0565",
        "adi.cn0566",
        "adi.cn0575",
        "adi.cn0579",
        "adi.daq2",
        "adi.daq3",
        "adi.fmc_vna",
        "adi.fmcadc3",
        "adi.fmcjesdadc1",
        "adi.fmclidar1",
        "adi.fmcomms11",
        "adi.fmcomms5",
        "adi.ada4355",
        "adi.ada4356_lidar",
        "adi.ada4961",
        "adi.adaq8092",
    ],
    "Other": [
        "adi.ad2s1210",
        "adi.ad514x",
        "adi.ad7091rx",
        "adi.ad7746",
        "adi.adg2128",
        "adi.axi_aion_trig",
        "adi.gen_mux",
        "adi.hmc7044",
        "adi.jesd",
        "adi.lm75",
        "adi.max14001",
        "adi.one_bit_adc_dac",
        "adi.tdd",
        "adi.tddn",
    ],
}


def update_devs():
    root = os.path.dirname(os.path.abspath(__file__))
    # Change directory to doc root to ensure correct paths for sphinx-apidoc
    original_cwd = os.getcwd()
    os.chdir(root)

    devices = glob.glob(os.path.join("source", "devices", "adi.*.rst"))

    skip = ["adi.ad9081_mc.rst"]
    devices = [d for d in devices if os.path.basename(d) not in skip]

    mfile = os.path.join("source", "devices", "modules.rst")
    devices_all = devices + [mfile] if os.path.exists(mfile) else devices

    # Autodoc won't generate these pages
    classes_not_modules = [
        "adi.adis16375.rst",
        "adi.adis16480.rst",
        "adi.adis16485.rst",
        "adi.adis16488.rst",
        "adi.adis16490.rst",
        "adi.adis16495.rst",
        "adi.adis16497.rst",
        "adi.adis16545.rst",
        "adi.adis16547.rst",
    ]

    for dev in devices_all:
        if os.path.basename(dev) in classes_not_modules:
            continue
        print("Removing {}".format(dev))
        if os.path.exists(dev):
            os.remove(dev)

    # Call autodoc
    cmd = "sphinx-apidoc -T -e -o source/devices ../adi"
    stream = os.popen(cmd)
    output = stream.read()
    print(output)

    # Process all generated device files
    new_devices = glob.glob(os.path.join("source", "devices", "adi.*.rst"))
    for dev in new_devices:
        if os.path.basename(dev) in classes_not_modules:
            continue
        with open(dev, "r") as f:
            txt = f.read()
            txt = txt.replace("adi.", "")
            txt = txt.replace(".. automodule:: ", ".. automodule:: adi.")
            txt = txt.replace(" module", "")
        with open(dev, "w") as f:
            f.write(txt)

    # Remove classes we shouldn't document
    to_skip = [
        "obs",
        "attribute",
        "context_manager",
        "dds",
        "rx_tx",
        "sshfs",
        "jesd_internal",
        "sync_start",
        "dsp",
        "compat",
        "device_base",
        "mcp_server",
    ]
    adi_rst_path = os.path.join("source", "devices", "adi.rst")
    if os.path.exists(adi_rst_path):
        with open(adi_rst_path, "r") as f:
            lines = f.readlines()
            for s in to_skip:
                s_path = os.path.join("source", "devices", "adi.{}.rst".format(s))
                if os.path.exists(s_path):
                    os.remove(s_path)
                lines = [l for l in lines if s not in l]

        # Collect remaining devices from adi.rst to see what is not categorized
        actual_devices = []
        for line in lines:
            line = line.strip()
            if line.startswith("adi."):
                actual_devices.append(line)

        # Build categorized index.rst
        output_lines = [
            "Supported Devices",
            "=================",
            "",
            "This page lists the devices currently supported by **pyadi-iio**, categorized by their primary function.",
            "",
        ]

        categorized_count = 0
        for category, parts in CATEGORIES.items():
            output_lines.append(category)
            output_lines.append("-" * len(category))
            output_lines.append(".. toctree::")
            output_lines.append("   :maxdepth: 1")
            output_lines.append("")

            category_parts = []
            for part in parts:
                if part in actual_devices:
                    category_parts.append("   " + part)
                    actual_devices.remove(part)
                    categorized_count += 1

            output_lines.extend(category_parts)
            output_lines.append("")

        # Add any remaining devices to 'Other' if not already there, or a new 'Uncategorized' section
        if actual_devices:
            output_lines.append("Uncategorized")
            output_lines.append("-------------")
            output_lines.append(".. toctree::")
            output_lines.append("   :maxdepth: 1")
            output_lines.append("")
            for part in actual_devices:
                output_lines.append("   " + part)
            output_lines.append("")

        output_lines.append("-----")
        output_lines.append("")
        output_lines.append(".. automodule:: adi")
        output_lines.append("   :members:")
        output_lines.append("   :undoc-members:")
        output_lines.append("   :show-inheritance:")

        with open(os.path.join("source", "devices", "index.rst"), "w") as f:
            f.write("\n".join(output_lines) + "\n")

        os.remove(adi_rst_path)

    os.chdir(original_cwd)


if __name__ == "__main__":
    update_devs()
