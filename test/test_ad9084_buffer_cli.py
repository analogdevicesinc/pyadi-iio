import os
import struct
import subprocess
import shutil

import iio
import numpy as np
import pytest

hardware = ["adsy1100"]
uri = os.environ.get("IIO_URI", "ip:10.44.3.143")


@pytest.mark.iio_hardware(hardware)
def test_ad9084_buffer_cli():
    os.makedirs("sample", exist_ok=True)

    dac_buffer_cli = shutil.which("dac_buffer_cli")
    assert dac_buffer_cli, "No dac_buffer_cli found!"

    subprocess.run(
        [
            dac_buffer_cli,
            "-u",
            uri,
            "-d",
            "axi-ad9084-tx-hpc",
            "-f",
            "/mnt/wsl/data/repos/iio-oscilloscope/waveforms/sinewave_0.9.mat",
        ],
        check=True,
    )
