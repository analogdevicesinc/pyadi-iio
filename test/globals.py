import os

import yaml

target_uri_arg = None
ignore_skip = False
dev_checked = False
found_dev = False
found_devices = {}  # type: ignore
found_uris = {}  # type: ignore
URI = "ip:analog"
TESTCONFIG_DEFAULT_PATH = "/etc/default/pyadi_test.yaml"


def get_test_config(filename=None):
    if not filename:
        if os.name == "nt" or os.name == "posix":
            if os.path.exists(TESTCONFIG_DEFAULT_PATH):
                filename = TESTCONFIG_DEFAULT_PATH
    if not filename:
        return None

    stream = open(filename, "r")
    config = yaml.safe_load(stream)
    stream.close()
    return config


# Get default config if it exists
imported_config = get_test_config()
