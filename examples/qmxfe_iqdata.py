import adi
import numpy as np

sdr = adi.QuadMxFE(uri="ip:10.44.3.86")

fs = 12000000
fc = 3000000
N = 1024
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = i + 1j * q

sdr.tx_enabled_channels = [15]
sdr.tx(iq)
# sdr.tx(np.real(iq))

## Pass noise
from scipy.io import loadmat
nf = loadmat('noise.mat')
noise = nf['dataC']
m = np.max(np.abs(noise))
noise = noise/m * 2**15 * 0.9
# Force singleton shape
noise = noise.reshape(len(noise))

sdr.tx_destroy_buffer()
sdr.tx_enabled_channels = [15]
sdr.tx(noise)
