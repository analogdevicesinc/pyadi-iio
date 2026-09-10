"""Update device classes to reflect all component classes"""

import glob
import os


def update_devs():
    root = os.path.dirname(os.path.abspath(__file__))
    source_devices = os.path.join(root, "source", "devices")
    adi_dir = os.path.abspath(os.path.join(root, "..", "adi"))

    # Autodoc won't generate these pages because they are classes within modules
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

    # Custom documentation pages that should not be deleted before running autodoc
    custom_pages = classes_not_modules + [
        "adi.ad9081_mc.rst",
        "adi.ad4020.rst",
        "adi.cn0532.rst",
        "adi.cn0540.rst",
        "adi.jesd.rst",
    ]

    mfile = os.path.join(source_devices, "modules.rst")
    if os.path.exists(mfile):
        os.remove(mfile)

    existing_devices = glob.glob(os.path.join(source_devices, "adi.*.rst"))
    for dev in existing_devices:
        if os.path.basename(dev) in custom_pages:
            continue
        print("Removing {}".format(dev))
        os.remove(dev)

    # Call autodoc
    cmd = f"sphinx-apidoc -T -e -o {source_devices} {adi_dir}"
    stream = os.popen(cmd)
    output = stream.read()
    print(output)

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
    for s in to_skip:
        skip_path = os.path.join(source_devices, f"adi.{s}.rst")
        if os.path.exists(skip_path):
            os.remove(skip_path)

    # Clean titles and automodule strings for all device pages
    all_devices = sorted(glob.glob(os.path.join(source_devices, "adi.*.rst")))
    for dev in all_devices:
        bname = os.path.basename(dev)
        mod_name = bname[4:-4]  # strip 'adi.' and '.rst'
        if mod_name in to_skip:
            continue

        with open(dev, "r") as f:
            content = f.read()

        lines = content.splitlines()
        # Remove leading blank lines
        while lines and not lines[0].strip():
            lines.pop(0)

        if not lines:
            continue

        # Determine uniform title
        if bname == "adi.admt4000ard1z.rst":
            title = "admt4000ard1z"
        elif bname == "adi.cn0532.rst":
            title = "cn0532"
        elif bname == "adi.cn0540.rst":
            title = "cn0540"
        elif bname == "adi.trigger.rst":
            title = "trigger"
        else:
            title = lines[0].replace("adi.", "").replace(" module", "").strip()

        lines[0] = title
        if len(lines) > 1 and set(lines[1]) <= {"=", "-"}:
            lines[1] = "=" * len(title)
        else:
            lines.insert(1, "=" * len(title))

        txt = "\n".join(lines) + "\n"
        txt = txt.replace(".. automodule:: ", ".. automodule:: adi.")
        txt = txt.replace(".. automodule:: adi.adi.", ".. automodule:: adi.")
        # Ensure jesd points to jesd_internal
        if bname == "adi.jesd.rst":
            txt = txt.replace(".. automodule:: adi.jesd\n", ".. automodule:: adi.jesd_internal\n")

        with open(dev, "w") as f:
            f.write(txt)

    # Generate index.rst
    device_names = [
        os.path.splitext(os.path.basename(f))[0]
        for f in sorted(glob.glob(os.path.join(source_devices, "adi.*.rst")))
        if os.path.splitext(os.path.basename(f))[0][4:] not in to_skip
    ]

    index_lines = [
        "Supported Devices",
        "=================",
        "",
        "",
        "",
        "",
        ".. toctree::",
        "   :maxdepth: 2",
        "",
    ]
    for dev_name in device_names:
        index_lines.append(f"   {dev_name}")

    index_lines.extend(
        [
            "",
            "-----",
            "",
            ".. automodule:: adi",
            "   :members:",
            "   :undoc-members:",
            "   :show-inheritance:",
            "",
        ]
    )

    with open(os.path.join(source_devices, "index.rst"), "w") as f:
        f.write("\n".join(index_lines))

    adi_rst_path = os.path.join(source_devices, "adi.rst")
    if os.path.exists(adi_rst_path):
        os.remove(adi_rst_path)


if __name__ == "__main__":
    update_devs()

