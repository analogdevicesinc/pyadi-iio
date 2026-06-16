"""Update device classes to reflect all component classes"""

import glob
import importlib
import inspect
import os
import sys


def update_devs():
    root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.abspath(os.path.join(root, "..")))

    import adi

    to_skip = {
        "__init__",
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
        "jesd",
    }

    # Get all .py files in adi/
    adi_dir = os.path.abspath(os.path.join(root, "..", "adi"))
    py_files = glob.glob(os.path.join(adi_dir, "*.py"))

    device_modules = []
    for f in py_files:
        name = os.path.splitext(os.path.basename(f))[0]
        if name not in to_skip:
            device_modules.append(name)

    device_modules.sort()

    out_dir = os.path.join(root, "source", "devices")
    os.makedirs(out_dir, exist_ok=True)

    # Clean up existing files in source/devices/ except skipped / non-generated ones
    existing = glob.glob(os.path.join(out_dir, "adi.*.rst"))
    for f in existing:
        os.remove(f)

    for mod_name in device_modules:
        try:
            mod = importlib.import_module(f"adi.{mod_name}")
        except Exception as e:
            print(f"Error importing adi.{mod_name}: {e}")
            continue

        # Find all classes defined in this module
        classes = []
        for member_name in dir(mod):
            member = getattr(mod, member_name)
            if inspect.isclass(member) and member.__module__ == f"adi.{mod_name}":
                classes.append((member_name, member))

        rst_path = os.path.join(out_dir, f"adi.{mod_name}.rst")

        # Fallback if no classes defined
        if not classes:
            content = f"""{mod_name}
{"=" * len(mod_name)}

.. automodule:: adi.{mod_name}
   :members:
   :undoc-members:
   :show-inheritance:
"""
        else:
            # Sort main classes first, channel classes at the end
            main_classes = [c for c in classes if not c[0].endswith("_channel")]
            channel_classes = [c for c in classes if c[0].endswith("_channel")]

            # Sort main_classes so that if one matches the mod_name (case-insensitive), it goes first
            main_classes.sort(key=lambda x: (x[0].lower() != mod_name.lower(), x[0]))

            lines = [mod_name, "=" * len(mod_name), ""]

            # 1. Supported Drivers / Compatible Parts
            compat_list = []
            for cname, cls in main_classes:
                compat = getattr(cls, "compatible_parts", None)
                if compat and isinstance(compat, (list, tuple)):
                    compat_list.append((cname, compat))

            if compat_list:
                lines.append("Supported Drivers")
                lines.append("-----------------")
                lines.append("")
                for cname, compat in compat_list:
                    lines.append(
                        f"The class **adi.{cname}** supports the following IIO drivers:"
                    )
                    lines.append("")
                    lines.append(
                        f".. autoattribute:: adi.{mod_name}.{cname}.compatible_parts"
                    )
                    lines.append("")

            # 2. Class API
            lines.append("Class API")
            lines.append("---------")
            lines.append("")
            for cname, cls in main_classes:
                exclude = ""
                compat = getattr(cls, "compatible_parts", None)
                if compat:
                    exclude = "\n   :exclude-members: compatible_parts"
                lines.append(
                    f".. autoclass:: adi.{mod_name}.{cname}\n   :members:\n   :undoc-members:\n   :show-inheritance:{exclude}"
                )
                lines.append("")

            # 3. Dynamic Attributes / Channel classes
            if channel_classes:
                lines.append("Dynamic Attributes")
                lines.append("------------------")
                lines.append("")
                for cname, cls in channel_classes:
                    base_name = cname.replace("_channel", "")
                    lines.append(
                        f"The {base_name} class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the {cname} class."
                    )
                    lines.append("")
                    lines.append(
                        f".. autoclass:: adi.{mod_name}.{cname}\n   :members:\n   :undoc-members:\n   :show-inheritance:"
                    )
                    lines.append("")

            content = "\n".join(lines)

        with open(rst_path, "w") as f:
            f.write(content)

    # Regenerate index.rst for devices
    index_lines = [
        "Supported Devices",
        "=================",
        "",
        "",
        "",
        ".. toctree::",
        "   :maxdepth: 2",
        "",
    ]
    for mod_name in device_modules:
        index_lines.append(f"   adi.{mod_name}")
    index_lines.append("")
    index_lines.append("-----")
    index_lines.append("")
    index_lines.append(".. automodule:: adi")
    index_lines.append("   :members:")
    index_lines.append("   :undoc-members:")
    index_lines.append("   :show-inheritance:")
    index_lines.append("")

    with open(os.path.join(out_dir, "index.rst"), "w") as f:
        f.write("\n".join(index_lines))


if __name__ == "__main__":
    update_devs()
