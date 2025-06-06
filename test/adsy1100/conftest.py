import os
import time
import pytest

import nebula

# from bench.keysight import E36233A, N9040B
# from bench.rs import SMA100A
from bench.keysight import E36233A
from .profiles_testing.stage3.generate_pytest_tests import get_test_boot_files_from_archive

@pytest.fixture(scope="module")
def power_supply(parse_instruments):
    if "E36233A" not in parse_instruments.keys():
        pytest.skip("E36233A not found. Skipping test")
    address = parse_instruments["E36233A"]
    powerSupply = E36233A(address)
    powerSupply.connect()

    powerSupply.first_boot_powered = False

    return powerSupply


