#!/bin/bash

busybox devmem 0x9c450088 w 0x1

iio_attr -c axi-core-tdd channel0 enable 0
iio_attr -c axi-core-tdd channel1 enable 0
iio_attr -c axi-core-tdd channel2 enable 0

iio_attr -c axi-core-tdd channel0 off_ms 1
iio_attr -c axi-core-tdd channel0 enable 1

iio_attr -c axi-core-tdd channel1 off_ms 1
iio_attr -c axi-core-tdd channel1 enable 1

iio_attr -c axi-core-tdd channel2 off_ms 1
iio_attr -c axi-core-tdd channel2 enable 1

iio_attr -d axi-core-tdd frame_length_ms 2

iio_attr -d axi-core-tdd enable 1

iio_attr -d axi-core-tdd sync_soft 0
iio_attr -d axi-core-tdd sync_soft 1
iio_attr -d axi-core-tdd sync_soft 0
 
