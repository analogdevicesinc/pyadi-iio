#!/usr/bin/env bash

# -- ABOUT THIS PROGRAM: ------------------------------------------------------
#
# Author:
# Version:      1.0.0
# Description:
# Source:       https://github.com/vitorbritto/boilerplates/blob/master/init/templates/tools/shellscript/myscript.sh
#
# -- INSTRUCTIONS: ------------------------------------------------------------
#
# Execute:
#
#
# Options:
#
#
# Example:
#
#
# Important:
#   -
#
# -- CHANGELOG: ---------------------------------------------------------------
#
#   DESCRIPTION:    First release
#   VERSION:        1.0.0
#   DATE:           DD/MM/YYYY
#   AUTHOR:
#
# -- TODO & FIXES: ------------------------------------------------------------
#
#   -
#
# -----------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# | VARIABLES                                                                  |
# ------------------------------------------------------------------------------

_V=0
BIN=vu11p.bin
DTBO=vu11p.dtbo

# ------------------------------------------------------------------------------
# | HELP                                                                       |
# ------------------------------------------------------------------------------
Help()
{
   # Display Help
   echo "Description"
   echo
   echo "Syntax: selmap.sh [-h|b|d|v]"
   echo "options:"
   echo
   echo "-b     Name of the bin file to be loaded."
   echo "       The file should be in the same folder as this script."
   echo "       default name: vu11p.bin"
   echo
   echo "-d     Name of the dtbo file to be loaded."
   echo "       The file should be in the same folder as this script."
   echo "       default name: vu11p.dtbo"
   echo
   echo "-h     Displays this message and exits."
   echo
   echo "-v     Verbose mode active."
   echo
}
# ------------------------------------------------------------------------------
# | UTILS/FUNCTIONS                                                            |
# ------------------------------------------------------------------------------
function log () {
    if [[ $_V -eq 1 ]]; then
        echo "$@"
    fi
}

while getopts ':b:d:vh' opt; do
	case "$opt" in
	h|\?)
		Help
		exit 0
		;;
	b)
		BIN=${OPTARG}
		;;
    d)
        DTBO=${OPTARG}
        ;;
	v)
		_V=1
		# echo "Verbose on."
		;;
	esac
done

# ------------------------------------------------------------------------------
# | MAIN FUNCTION	                                                       |
# ------------------------------------------------------------------------------

# Set boot bits to selectmap
log "Set chip 1 pin 118:120 to 110 (SelectMAP)"
gpioset 1 118=0
gpioset 1 119=1
gpioset 1 120=1

log "move $BIN in to /lib/firmware/vu11p.bin"
log "move $DTBO in to /lib/firmware/vu11p.dtbo"
mkdir -p /lib/firmware
cp $BIN /lib/firmware/vu11p.bin
cp $DTBO /lib/firmware/vu11p.dtbo

log "set fpga1 flag to full bitsream"
echo 0 > /sys/class/fpga_manager/fpga0/flags

log "Creating /sys/kernel/config/device-tree/overlays/full"
mkdir -p /sys/kernel/config/device-tree/overlays/full

START=$(date +%s)
log "program fpga1"
echo -n "vu11p.dtbo" > /sys/kernel/config/device-tree/overlays/full/path
END=$(date +%s)
DIFF=$(( $END - $START ))
echo "Programming took $DIFF seconds"

# log "Removing overlays/full dir"
# rmdir /sys/kernel/config/device-tree/overlays/full

log "Set chip 1 pin 118:120 to 000 (JTAG)"
gpioset 1 118=0
gpioset 1 119=0
gpioset 1 120=0

exit 0
