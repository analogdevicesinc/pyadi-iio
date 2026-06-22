#!/bin/bash
if [ $# -ne 2 ]; then
  echo "Usage: $0 <HPF_freq_GHz> <LPF_freq_GHz>"
  echo "  HPF range: 6.4 - 11.4 GHz"
  echo "  LPF range: 7.2 - 12.3 GHz"
  echo "  Example: $0 8.0 11.0"
  exit 1
fi
HPF_FREQ=$1
LPF_FREQ=$2
# Find Artix mantaray_control by checking for LO_CE label
CTRL=""
for dev in /sys/bus/iio/devices/iio:device*; do
  if [ "$(cat $dev/out_voltage16_label 2>/dev/null)" = "LO_CE" ]; then
    CTRL=$dev
    break
  fi
done
if [ -z "$CTRL" ]; then
  echo "ERROR: Artix mantaray_control not found"
  exit 1
fi
# HPF: state = (freq - 6.4) / 0.333
# LPF: state = (freq - 7.2) / 0.34
HPF_STATE=$(echo "$HPF_FREQ" | awk '{s = int(($1 - 6.4) / 0.333 + 0.5); if(s<0) s=0; if(s>15) s=15; print s}')
LPF_STATE=$(echo "$LPF_FREQ" | awk '{s = int(($1 - 7.2) / 0.34 + 0.5); if(s<0) s=0; if(s>15) s=15; print s}')
HPF_ACTUAL=$(echo "$HPF_STATE" | awk '{printf "%.1f", 6.4 + $1 * 0.333}')
LPF_ACTUAL=$(echo "$LPF_STATE" | awk '{printf "%.1f", 7.2 + $1 * 0.34}')
echo "Requested: HPF = ${HPF_FREQ} GHz, LPF = ${LPF_FREQ} GHz"
echo "Nearest:   HPF = ${HPF_ACTUAL} GHz (state $HPF_STATE), LPF = ${LPF_ACTUAL} GHz (state $LPF_STATE)"
echo ""
# Extract 4 bits
HPF_B0=$(( (HPF_STATE >> 0) & 1 ))
HPF_B1=$(( (HPF_STATE >> 1) & 1 ))
HPF_B2=$(( (HPF_STATE >> 2) & 1 ))
HPF_B3=$(( (HPF_STATE >> 3) & 1 ))
LPF_B0=$(( (LPF_STATE >> 0) & 1 ))
LPF_B1=$(( (LPF_STATE >> 1) & 1 ))
LPF_B2=$(( (LPF_STATE >> 2) & 1 ))
LPF_B3=$(( (LPF_STATE >> 3) & 1 ))
echo "Setting HPF bits: B3=$HPF_B3 B2=$HPF_B2 B1=$HPF_B1 B0=$HPF_B0"
echo $HPF_B0 > $CTRL/out_voltage8_raw
echo $HPF_B1 > $CTRL/out_voltage9_raw
echo $HPF_B2 > $CTRL/out_voltage10_raw
echo $HPF_B3 > $CTRL/out_voltage11_raw
echo "Setting LPF bits: B3=$LPF_B3 B2=$LPF_B2 B1=$LPF_B1 B0=$LPF_B0"
echo $LPF_B0 > $CTRL/out_voltage12_raw
echo $LPF_B1 > $CTRL/out_voltage13_raw
echo $LPF_B2 > $CTRL/out_voltage14_raw
echo $LPF_B3 > $CTRL/out_voltage15_raw
echo ""
echo "Readback:"
echo "  HPF_B0 (ch8):  $(cat $CTRL/out_voltage8_raw)"
echo "  HPF_B1 (ch9):  $(cat $CTRL/out_voltage9_raw)"
echo "  HPF_B2 (ch10): $(cat $CTRL/out_voltage10_raw)"
echo "  HPF_B3 (ch11): $(cat $CTRL/out_voltage11_raw)"
echo "  LPF_B0 (ch12): $(cat $CTRL/out_voltage12_raw)"
echo "  LPF_B1 (ch13): $(cat $CTRL/out_voltage13_raw)"
echo "  LPF_B2 (ch14): $(cat $CTRL/out_voltage14_raw)"
echo "  LPF_B3 (ch15): $(cat $CTRL/out_voltage15_raw)"
echo ""
echo "Passband: ~${HPF_ACTUAL} GHz to ~${LPF_ACTUAL} GHz"
echo "Done."
