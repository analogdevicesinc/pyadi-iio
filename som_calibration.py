import adi


sdr = adi.adrv9009_zu11eg(uri="ip:192.168.86.41")
# Set a calibration
sdr.calibrate_rx_phase_correction_en = 1

# Set a cal for other attribute which don't have python properties 
sdr._set_iio_dev_attr_str("calibrate_rx_phase_correction_en", 1)

# Trigger calibration
sdr.calibrate = 1
