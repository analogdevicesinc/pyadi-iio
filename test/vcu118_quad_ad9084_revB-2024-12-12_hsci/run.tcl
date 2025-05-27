
    connect
    fpga -f "/home/snuc/ADI/pyadi/test/vcu118_quad_ad9084_revB-2024-12-12_hsci/system_top.bit"
    after 1000
    target 3
    dow "/home/snuc/ADI/pyadi/test/vcu118_quad_ad9084_revB-2024-12-12_hsci/simpleImage.vcu118_quad_ad9084_revB.strip"
    after 1000
    con
    disconnect
    