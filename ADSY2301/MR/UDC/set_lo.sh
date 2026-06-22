#!/bin/bash
if [ $# -ne 1 ]; then
  echo "Usage: $0 <frequency_GHz>"
  echo "  Example: $0 13.4"
  exit 1
fi
FREQ_GHZ=$1
FREQ_HZ=$(echo "$FREQ_GHZ" | awk '{printf "%.0f", $1 * 1000000000}')
# Find adf4382a IIO device
ADF=""
for dev in /sys/bus/iio/devices/iio:device*; do
  name=$(cat $dev/name 2>/dev/null)
  if [ "$name" = "adf4382a" ] || [ "$name" = "adf4382" ]; then
    ADF=$dev
    break
  fi
done
if [ -z "$ADF" ]; then
  echo "ERROR: adf4382 IIO device not found"
  exit 1
fi
echo "Setting LO frequency: ${FREQ_GHZ} GHz (${FREQ_HZ} Hz)"
echo $FREQ_HZ > $ADF/out_altvoltage_frequency
READBACK=$(cat $ADF/out_altvoltage_frequency)
READBACK_GHZ=$(echo "$READBACK" | awk '{printf "%.6f", $1 / 1000000000}')
echo "Readback: ${READBACK_GHZ} GHz (${READBACK} Hz)"
echo "Done."
