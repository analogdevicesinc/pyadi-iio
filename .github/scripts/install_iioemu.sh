#!/bin/bash
sudo apt-get -qq update

git clone https://github.com/analogdevicesinc/libtinyiiod.git
cd libtinyiiod
mkdir build && cd build
cmake -DBUILD_EXAMPLES=OFF ..
make
sudo make install
sudo ldconfig
cd ../..

git clone -b v0.2.0 https://github.com/analogdevicesinc/iio-emu.git
cd iio-emu
mkdir build && cd build
cmake ..
make
sudo make install
sudo ldconfig
cd ../..
