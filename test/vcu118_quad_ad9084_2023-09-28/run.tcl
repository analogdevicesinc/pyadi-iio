# Open Xilinx xsdb tool and
# source run.tcl
#
connect
fpga -f system_top.bit
after 1000
target 3
dow simpleImage.strip
after 1000
con
disconnect
