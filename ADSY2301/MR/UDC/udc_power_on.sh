#!/bin/bash
find_iio_by_label() {
  for dev in /sys/bus/iio/devices/iio:device*; do
    if [ "$(cat $dev/label 2>/dev/null)" = "$1" ]; then
      echo "$dev"
      return
    fi
  done
  echo ""
}
find_artix_ctrl() {
  for dev in /sys/bus/iio/devices/iio:device*; do
    if [ "$(cat $dev/out_voltage16_label 2>/dev/null)" = "LO_CE" ]; then
      echo "$dev"
      return
    fi
  done
  echo ""
}
PWR=$(find_iio_by_label "mantaray_pwr_control")
CTRL=$(find_artix_ctrl)
if [ -z "$PWR" ]; then
  echo "ERROR: mantaray_pwr_control not found"
  exit 1
fi
if [ -z "$CTRL" ]; then
  echo "ERROR: Artix mantaray_control not found"
  exit 1
fi
echo "Using PWR: $PWR"
echo "Using CTRL: $CTRL"
echo ""
echo "=== Enabling power rails ==="
echo "Enabling UDC_5P0V_PWR_EN (channel 3)..."
echo 1 > $PWR/out_voltage3_raw
sleep 0.5
echo "  Readback: $(cat $PWR/out_voltage3_raw)"
echo "Enabling UDC_3P3V_PWR_EN (channel 2)..."
echo 1 > $PWR/out_voltage2_raw
sleep 0.5
echo "  Readback: $(cat $PWR/out_voltage2_raw)"
echo "Enabling UDC_NEG_PWR_EN (channel 1)..."
echo 1 > $PWR/out_voltage1_raw
sleep 0.5
echo "  Readback: $(cat $PWR/out_voltage1_raw)"
echo ""
echo "=== Enabling RF_FL_LDO_EN ==="
echo "Enabling RF_FL_LDO_EN (channel 4)..."
echo 1 > $CTRL/out_voltage4_raw
sleep 0.5
echo "  Readback: $(cat $CTRL/out_voltage4_raw)"
echo ""
echo "=== Enabling LO_CE ==="
echo "Enabling LO_CE (channel 16)..."
echo 1 > $CTRL/out_voltage16_raw
sleep 0.5
echo "  Readback: $(cat $CTRL/out_voltage16_raw)"
echo ""
echo "=== Readback all enables ==="
echo "  N6P0V_EN      (ch0): $(cat $PWR/out_voltage0_raw)"
echo "  UDC_NEG_PWR   (ch1): $(cat $PWR/out_voltage1_raw)"
echo "  UDC_3P3V_PWR  (ch2): $(cat $PWR/out_voltage2_raw)"
echo "  UDC_5P0V_PWR  (ch3): $(cat $PWR/out_voltage3_raw)"
echo "  RF_FL_LDO_EN  (ch4): $(cat $CTRL/out_voltage4_raw)"
echo "  LO_CE        (ch16): $(cat $CTRL/out_voltage16_raw)"
echo ""
echo "=== Binding SPI drivers ==="
echo "Binding ADF4382..."
echo spi7.0 > /sys/bus/spi/drivers/adf4382a/bind 2>/dev/null || echo spi7.0 > /sys/bus/spi/drivers/adf4382/bind 2>/dev/null
sleep 0.5
echo "Binding ADMV1320 (TX)..."
echo spi8.0 > /sys/bus/spi/drivers/admv1320/bind 2>/dev/null
echo spi8.1 > /sys/bus/spi/drivers/admv1320/bind 2>/dev/null
echo spi8.2 > /sys/bus/spi/drivers/admv1320/bind 2>/dev/null
echo spi8.3 > /sys/bus/spi/drivers/admv1320/bind 2>/dev/null
sleep 0.5
echo "Binding ADMV1420 (RX)..."
echo spi9.0 > /sys/bus/spi/drivers/admv1420/bind 2>/dev/null
echo spi9.1 > /sys/bus/spi/drivers/admv1420/bind 2>/dev/null
echo spi9.2 > /sys/bus/spi/drivers/admv1420/bind 2>/dev/null
echo spi9.3 > /sys/bus/spi/drivers/admv1420/bind 2>/dev/null
sleep 0.5
echo ""
echo "=== IIO devices ==="
for dev in /sys/bus/iio/devices/iio:device*; do
  echo "  $(basename $dev): $(cat $dev/name 2>/dev/null) [$(cat $dev/label 2>/dev/null)]"
done
echo ""
echo "=== dmesg (last 20 lines) ==="
dmesg | tail -20
echo ""
echo "Done."
