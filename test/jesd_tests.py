"""Tests for JESD204 interfaces"""

from pprint import pprint
from time import sleep

import pytest

import adi

try:
    import adi.jesd

    skip_jesd = False
except:
    skip_jesd = True


def verify_links(iio_uri: str, classname: str):
    """Verify that the links are up in DATA mode

    Args:
        iio_uri (str): URI of the device
        classname (str): Class name of the device

    Exceptions:
        AssertionError: If the link is not in DATA mode
    """
    if skip_jesd:
        pytest.skip("JESD204 interface support not available")

    dev = eval(classname)(uri=iio_uri, jesd_monitor=True)
    status = dev._jesd.get_all_link_statuses()
    pprint(status)

    # Check that all links are in DATA mode
    for driver in status:
        for lane in status[driver]:
            print(f"Checking {driver}/{lane}")
            data = status[driver][lane]
            pprint(data)
            assert (
                data["CGS state"] == "DATA"
            ), f"Link {driver}/{lane} is not in DATA mode"


def verify_links_errors_stable(iio_uri: str, classname: str):
    """Verify that the links are stable and not increasing errors

    Args:
        iio_uri (str): URI of the device
        classname (str): Class name of the

    Exceptions:
        AssertionError: If the link errors have increased
        AssertionError: If the link is not in DATA mode
    """
    if skip_jesd:
        pytest.skip("JESD204 interface support not available")

    dev = eval(classname)(uri=iio_uri, jesd_monitor=True)

    # Get error count on all lanes and links
    def get_link_errors(status):
        links = {}
        for driver in status:
            for lane in status[driver]:
                print(f"Checking {driver}/{lane}")
                data = status[driver][lane]
                links[f"{driver}/{lane}"] = int(data["Errors"])
        return links

    status = dev._jesd.get_all_link_statuses()
    pre_link_errors = get_link_errors(status)
    pprint(pre_link_errors)

    N = 5
    print(f"Waiting {N} seconds")
    sleep(N)

    status = dev._jesd.get_all_link_statuses()
    post_link_errors = get_link_errors(status)
    pprint(post_link_errors)

    # Check that all links have not increased in errors
    for link in pre_link_errors:
        assert (
            pre_link_errors[link] == post_link_errors[link]
        ), f"Link {link} has increased in errors"
