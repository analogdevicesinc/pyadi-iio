#!/bin/bash

# Set LIBIIO_BRANCH if not set
if [ -z "$LIBIIO_BRANCH" ]; then
    LIBIIO_BRANCH="v0.25"
fi

if [ "$LIBIIO_BRANCH" = "main" ]; then
    echo "Using main branch of libiio, skipping libad9361-iio and libad9166-iio installation as they are unsupported on main."
    exit 0
fi



git clone -b 'main' --single-branch --depth 1 https://github.com/analogdevicesinc/libad9361-iio.git
cd libad9361-iio
if [ "$LIBIIO_BRANCH" = "main" ]; then
    cmake -DPYTHON_BINDINGS=ON -DLIBIIO_INCLUDEDIR=/usr/include/iio .
else
    cmake -DPYTHON_BINDINGS=ON .
fi
make
cd bindings/python
pip install .
cd ../..
sudo make install
sudo ldconfig
cd ..
rm -rf libad9361-iio

git clone -b 'main' --single-branch --depth 1 https://github.com/analogdevicesinc/libad9166-iio.git
cd libad9166-iio
if [ "$LIBIIO_BRANCH" = "main" ]; then
    cmake -DPYTHON_BINDINGS=ON -DLIBIIO_INCLUDEDIR=/usr/include/iio .
else
    cmake -DPYTHON_BINDINGS=ON .
fi
make
cd bindings/python
pip install .
cd ../..
sudo make install
sudo ldconfig
cd ..
rm -rf libad9166-iio

pip install pylibiio>=0.23.1
