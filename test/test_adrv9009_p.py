import pytest
import os
import pathlib
import glob

hardware = "adrv9009"
classname = "adi.adrv9009"

p = pathlib.Path(__file__).parent.absolute()
p = os.path.join(p, "profiles", "adrv9009", "*")
profiles = glob.glob(p)


@pytest.mark.parametrize("classname, hardware", [(classname, hardware)])
@pytest.mark.parametrize("channel", [0, 1, [0, 1]])
@pytest.mark.parametrize("profile", profiles)
def test_adrv9009_rx_data(
    test_dma_rx, test_load_profile, classname, hardware, channel, profile
):
    test_load_profile(classname, hardware, profile)
    test_dma_rx(classname, hardware, channel)
