
    connect
    fpga -f "C:/ADI/Triton/pyadi-iio/test/vcu118_quad_ad9084_2023-09-28/system_top_26p4.bit"
    after 1000
    target 3
    dow "C:/ADI/Triton/pyadi-iio/test/vcu118_quad_ad9084_2023-09-28/simpleImage_26p4.strip"
    after 1000
    con
    disconnect
    