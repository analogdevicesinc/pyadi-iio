#!/bin/bash
sudo apt-get install -y python3-pip python3-setuptools
pip install -r requirements.txt
pip install -r requirements_dev.txt


if [ "$LIBIIO_BRANCH" = "main" ]; then
    pip install --force-reinstall pytest-libiio@git+https://github.com/tfcollins/pytest-libiio.git@libiio-v1-support
else
    pip install pytest-libiio==0.0.14
fi
