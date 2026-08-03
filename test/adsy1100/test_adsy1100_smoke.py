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