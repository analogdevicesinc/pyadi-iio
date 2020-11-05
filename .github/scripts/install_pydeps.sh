#!/bin/bash
sudo apt-get install -y python3-pip python3-setuptools
pip install -r requirements.txt
pip install -r requirements_dev.txt
pip install pylibiio
