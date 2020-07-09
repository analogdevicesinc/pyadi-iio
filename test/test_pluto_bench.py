import pytest
from adi import ad9361

hardware = ["pluto", "adrv9361", "fmcomms2"]
classname = "adi.Pluto"


def inner_function_rx(device):
    data = device.rx()


def test_benchmark_rx(benchmark):
    sdr = ad9361(uri="ip:192.168.86.35")
    benchmark.pedantic(inner_function_rx, args=(sdr,), rounds=5, iterations=100)
