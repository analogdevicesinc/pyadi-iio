import os
import time
import pytest

import nebula

# from bench.keysight import E36233A, N9040B
# from bench.rs import SMA100A
from bench.keysight import E36233A
from .profiles_testing.stage3.generate_pytest_tests import get_test_boot_files_from_archive

config_file_folder = os.path.dirname(__file__)
config_file_zu4eg = os.path.join(config_file_folder, "nebula_zu4eg.yaml")

hostname = os.getenv("HOSTNAME", "b0adsy1100")
# configs = get_test_boot_files_from_archive()

def measure_power(power_supply):
    v1 = power_supply.ch1.voltage
    c1 = power_supply.ch1.current_draw
    v2 = power_supply.ch2.voltage
    c2 = power_supply.ch2.current_draw

    results = {"v1": v1, "c1": c1, "p1": v1 * c1, "v2": v2, "c2": c2, "p2": v2 * c2}
    return results


def do_flush(neb_uart):
    # Flush to marker
    neb_uart._write_data("uname")
    found = neb_uart._read_until_done_multi(done_strings=["Linux"], max_time=10000)
    if not found or not found[0]:
        raise Exception("UART not working")


@pytest.fixture(scope="module")
def power_supply(parse_instruments):
    if "E36233A" not in parse_instruments.keys():
        pytest.skip("E36233A not found. Skipping test")
    address = parse_instruments["E36233A"]
    powerSupply = E36233A(address)
    powerSupply.connect()

    powerSupply.first_boot_powered = False

    return powerSupply


