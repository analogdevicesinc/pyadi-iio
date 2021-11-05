import adi
import numpy as np

sdr = adi.adrv9002(uri="ip:analog.local")
sdr.tx_enabled_channels = [0]
fs = sdr.tx_sample_rate

# Create a sinewave waveform
fc = 100000
N = 1024
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = i + 1j * q

# Send data to binary file
sdr._output_byte_filename = "iq_data.bin"
sdr._push_to_file = True
sdr.tx(iq)

# Push from commandline
# cat iq_data.bin | iio_writedev -c -b 1024 -u ip:analog.local axi-adrv9002-tx-lpc voltage0 voltage1