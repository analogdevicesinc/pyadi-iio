import adi

dev = adi.pqmon("serial:/dev/ttyACM0,9600,8n1")

print(dev._device_name)
print(dev.config.firmware_version)

print(dev.current_a.rms)
print(dev.voltage_a.rms)

# raw value as read by the ADC - can be used scaled using scale attribute
print(dev.voltage_a.raw)

print(dev.voltage_b.angle)
print(dev.current_b.angle)  # various attributes of current/voltage channels

# harmonics are computed when config.process_data = True
# config.process_data is handled by pyadi-iio unless
# config.single_shot_acquisition is set to True
print(dev.voltage_b.harmonics)
print(dev.current_a.harmonics)


dev.read_events()  # events need to be read before accessing them
for v in dev.dip_events:
    print(v.end_time - v.start_time)
    print(v.min_mag)


dev._rx_output_type = "SI"  # or "raw"
print(dev.rx())
