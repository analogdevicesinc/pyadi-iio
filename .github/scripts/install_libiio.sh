#!/bin/bash
sudo apt-get -qq update
sudo apt-get install -y git cmake graphviz libavahi-common-dev libavahi-client-dev libaio-dev libusb-1.0-0-dev libxml2-dev rpm tar bzip2 gzip flex bison git
git clone -b 'main' --single-branch --depth 1 https://github.com/analogdevicesinc/libiio.git
cd libiio
cmake . -DHAVE_DNS_SD=OFF
make
sudo make install
cd ..
rm -rf libiio

# Python pieces
sudo apt-get install -y python3-pip python3-setuptools
git clone -b 'main' --single-branch --depth 1 https://github.com/analogdevicesinc/libiio.git
cd libiio
cmake . -DHAVE_DNS_SD=OFF -DPYTHON_BINDINGS=ON
make
cd bindings/python
pip install .
cd ../..
cd ..
rm -rf libiio
