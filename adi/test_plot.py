# Calculate element patterns with different cosine powers
import numpy as np
import matplotlib.pyplot as plt

th = np.linspace(-90, 90, 1000)  # degrees
th_rad = np.deg2rad(th)



# cosTheta^1
cosTh1p0 = 10 * np.log10(np.abs(np.cos(th_rad)**1.0))
# cosTheta^1.2
cosTh1p2 = 10 * np.log10(np.abs(np.cos(th_rad)**1.2))
# cosTheta^1.5
cosTh1p5 = 10 * np.log10(np.abs(np.cos(th_rad)**1.5))
# cosTheta^1.7
cosTh1p7 = 10 * np.log10(np.abs(np.cos(th_rad)**1.7))
# cosTheta^2.0
cosTh2p0 = 10 * np.log10(np.abs(np.cos(th_rad)**2.0))

plt.figure(figsize=(10, 6))
plt.plot(th, cosTh1p0, label='n=1.0')
plt.plot(th, cosTh1p2, label='n=1.2')
plt.plot(th, cosTh1p5, label='n=1.5')
plt.plot(th, cosTh1p7, label='n=1.7')
plt.plot(th, cosTh2p0, label='n=2.0')
plt.title('Element Pattern Models (cos^n θ)')
plt.xlabel('Angle (degrees)')
plt.ylabel('Relative Power (dB)')
plt.grid(True)
plt.legend()
plt.ylim(-50, 0)
plt.show()