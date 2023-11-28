#!/bin/bash
exit 0

git clone -b 'master' --single-branch --depth 1 https://github.com/analogdevicesinc/libad9361-iio.git
cd libad9361-iio
cmake -DPYTHON_BINDINGS=ON -DLIBIIO_INCLUDEDIR=/usr/include/iio .
make
cd bindings/python
pip install .
cd ../..
sudo make install
sudo ldconfig
cd ..
rm -rf libad9361-iio

git clone -b 'master' --single-branch --depth 1 https://github.com/analogdevicesinc/libad9166-iio.git
cd libad9166-iio
cmake -DPYTHON_BINDINGS=ON -DLIBIIO_INCLUDEDIR=/usr/include/iio .
make
cd bindings/python
pip install .
cd ../..
sudo make install
sudo ldconfig
cd ..
rm -rf libad9166-iio

# pip install pylibiio==0.23.1
