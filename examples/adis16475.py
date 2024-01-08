# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import sys

import adi

my_dev_name = sys.argv[1]
my_uri = sys.argv[2]

adis16475 = adi.adis16475(device_name=my_dev_name, uri=my_uri)

# print Y and Z axis acceleration
# print(data)
print("Product id: " + str(adis16475.product_id))
print("Serial number: " + adis16475.serial_number)
print("Firmware revision: " + adis16475.firmware_revision)
print("Firmware date: " + adis16475.firmware_date)
print("\nX acceleration: " + str(adis16475.accel_x_conv) + " m/s^2")
print("Y acceleration: " + str(adis16475.accel_y_conv) + " m/s^2")
print("Z acceleration: " + str(adis16475.accel_z_conv) + " m/s^2")

print("\nX angular velocity: " + str(adis16475.anglvel_x_conv) + " rad/s")
print("Y angular velocity: " + str(adis16475.anglvel_y_conv) + " rad/s")
print("Z angular velocity: " + str(adis16475.anglvel_z_conv) + " rad/s")

adis16475.rx_output_type = "raw"
adis16475.rx_enabled_channels = [6, 7, 8, 9, 10, 11, 12]
adis16475.sample_rate = 10
adis16475.rx_buffer_size = 10

data = adis16475.rx()

for i in range(0, 9):
    # arr = i
    print(
        "\nTemperature: "
        + str(data[0][i] * adis16475.temp.scale)
        + " millidegrees Celsius"
    )
    print(
        "X delta angle: " + str(data[1][i] * adis16475.deltaangl_x.scale) + " radians"
    )
    print(
        "Y delta angle: " + str(data[2][i] * adis16475.deltaangl_y.scale) + " radians"
    )
    print(
        "Z delta angle: " + str(data[3][i] * adis16475.deltaangl_z.scale) + " radians"
    )
    print(
        "X delta velocity: "
        + str(data[4][i] * adis16475.deltavelocity_x.scale)
        + " m/s"
    )
    print(
        "Y delta velocity: "
        + str(data[5][i] * adis16475.deltavelocity_y.scale)
        + " m/s"
    )
    print(
        "Z delta velocity: "
        + str(data[6][i] * adis16475.deltavelocity_z.scale)
        + " m/s"
    )
