#!/bin/bash
echo "Deasserting FPGA_TRIG..."
echo 1 > /sys/bus/iio/devices/iio:device1/out_voltage3_raw
sleep 0.5
echo "Creating overlay directory..."
mkdir /sys/kernel/config/device-tree/overlays/artix
sleep 0.5
echo "Applying overlay..."
echo "artix-mantaray-tiles.dtbo" > /sys/kernel/config/device-tree/overlays/artix/path
sleep 0.5
echo "IIO Devices:"
for dev in /sys/bus/iio/devices/iio:device*; do
  name=$(cat "$dev/name" 2>/dev/null)
  echo "  $(basename $dev): $name"
done
echo "Done."
