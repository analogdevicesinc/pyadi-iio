#!/bin/bash
sudo apt-get install -y python3-pip python3-setuptools
pip install -r requirements.txt
pip install -r requirements_dev.txt
pip install setuptools wheel twine build

if [ "$LIBIIO_BRANCH" = "main" ]; then
    pip install --no-deps --force-reinstall pytest-libiio@git+https://github.com/tfcollins/pytest-libiio.git@master
    pip install lxml pyyaml
    # Update python bindings again
    git clone -b $LIBIIO_BRANCH --single-branch --depth 1 https://github.com/analogdevicesinc/libiio.git
    cd libiio
    cmake . -DHAVE_DNS_SD=OFF -DPYTHON_BINDINGS=ON
    make
    cd bindings/python
    pip install .
    cd ../..
    cd ..
    rm -rf libiio
else
    pip install "pytest-libiio>=0.0.18"
fi
