#!/bin/bash
sudo apt-get -qq update
sudo apt-get install -y git cmake graphviz libaio-dev libusb-1.0-0-dev libxml2-dev rpm tar bzip2 gzip flex bison git
git clone -b 'v0.21' --single-branch --depth 1 https://github.com/analogdevicesinc/libiio.git
cd libiio
cmake .
make
sudo make install
cd ..
