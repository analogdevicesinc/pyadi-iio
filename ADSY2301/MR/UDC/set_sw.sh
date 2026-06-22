#!/bin/bash
if [ $# -ne 3 ]; then
  echo "Usage: $0 <switch 1-4> <enable 0|1> <ctrl 0|1>"
  echo "  Example: $0 1 0 0   # SW1 enabled, CTRL=0 (RFC-RF2)"
  echo "           $0 2 0 1   # SW2 enabled, CTRL=1 (RFC-RF1)"
  echo "           $0 3 1 X   # SW3 disabled"
  exit 1
fi
SW=$1
EN=$2
CTRL=$3
if [ "$SW" -lt 1 ] || [ "$SW" -gt 4 ]; then
  echo "ERROR: Switch must be 1-4"
  exit 1
fi
if [ "$EN" != "0" ] && [ "$EN" != "1" ]; then
  echo "ERROR: Enable must be 0 or 1"
  exit 1
fi
if [ "$CTRL" != "0" ] && [ "$CTRL" != "1" ]; then
  echo "ERROR: Ctrl must be 0 or 1"
  exit 1
fi
# Find mantaray_txrx_control IIO device
TXRX=""
for dev in /sys/bus/iio/devices/iio:device*; do
  if [ "$(cat $dev/label 2>/dev/null)" = "mantaray_txrx_control" ]; then
    TXRX=$dev
    break
  fi
done
if [ -z "$TXRX" ]; then
  echo "ERROR: mantaray_txrx_control not found"
  exit 1
fi
# CTRL channels: 8,9,10,11 for SW 1,2,3,4
# EN channels:  12,13,14,15 for SW 1,2,3,4
CTRL_CH=$((7 + SW))
EN_CH=$((11 + SW))
echo "=== ADRF5030 SW${SW} ==="
echo "Setting EN   (ch${EN_CH}): ${EN}"
echo $EN > $TXRX/out_voltage${EN_CH}_raw
echo "Setting CTRL (ch${CTRL_CH}): ${CTRL}"
echo $CTRL > $TXRX/out_voltage${CTRL_CH}_raw
echo ""
echo "Readback:"
echo "  EN   (ch${EN_CH}):   $(cat $TXRX/out_voltage${EN_CH}_raw)"
echo "  CTRL (ch${CTRL_CH}): $(cat $TXRX/out_voltage${CTRL_CH}_raw)"
echo "Done."
