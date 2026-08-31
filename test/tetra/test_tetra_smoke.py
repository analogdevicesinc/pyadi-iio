import pytest

@pytest.fixture(scope="module")
def board(strategy, target):

    # strategy.stage("shell")
    strategy.transition("shell")

    shell = target.get_driver("ADIShellDriver")

    stdout = shell.run_check('cat /proc/version')
    print(f"Test result: {stdout}")

    yield target

    strategy.transition("soft_off")


def test_board_smoke(board):
    # This test is a smoke test to ensure that the board is reachable and responsive.
    # It checks if the board's shell can execute a simple command and return the expected output.

    shell = board.get_driver("ADIShellDriver")

    # Run a simple command to check if the board is responsive
    stdout = shell.run_check('echo "Hello, World!"')
    if isinstance(stdout, list):
        stdout = "\n".join(stdout)
    stdout = str(stdout).strip()
    assert stdout == "Hello, World!", "Board did not respond correctly to echo command"


def test_board_networking(board):

    shell = board.get_driver("ADIShellDriver")
    address = shell.get_ip_addresses("eth0")  # Replace "eth0" with your actual ethernet interface name if different
    ip = str(address[0].ip)
    print(f"Board IP address: {ip}")

    network = board.get_driver("SSHDriver")
    network.address = ip

    stdout = network.run_check('iio_attr -d')
    print(f"Network test result: {stdout}")

def test_drivers(board):

    import iio
    ssh = board.get_driver("SSHDriver")
    ctx = iio.Context(f"ip:{ssh.address}")

    drivers_found = [str(dev.name) for dev in ctx.devices]

    drivers = ["adrv903x-phy", "hmc7044"]

    for driver in drivers:
        assert driver in drivers_found, f"Driver {driver} not found on the board"

    for driver_found in drivers_found:
        print(f"Driver found on the board: {driver_found}")
