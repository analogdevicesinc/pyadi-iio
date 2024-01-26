# Open Xilinx xsdb tool and
# source run.tcl
#
connect
fpga -f system_top_26p4.bit
after 1000
target 3
dow simpleImage_26p4.strip
after 1000
con
disconnect
