import time

import adi
import pytest


def check_jesd_links(classname, uri, iterations=4):
    """Check that the JESD links are up and in DATA mode

    Args:
        classname (str): The name of the class to instantiate
        uri (str): The URI of the device to connect to
        iterations (int): The number of times to check the JESD links
    """

    sdr = eval(f"{classname}(uri='{uri}', disable_jesd_control=False)")

    for _ in range(iterations):
        # Check that the JESD links are up
        links = sdr._jesd.get_all_statuses()
        for link in links:
            print(f"Link {link} status: \n{links[link]}")
            assert links[link]["enabled"] == "enabled", f"Link {link} is down"
            assert links[link]["Link status"] == "DATA", f"Link {link} not in DATA mode"

        time.sleep(1)
