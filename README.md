# pyadi-iio: Analog Devices python interfaces for hardware with Industrial I/O drivers

![PyADI-IIO Logo](images/PyADI-IIO_Logo_72.png)

[![Build Status](https://travis-ci.org/analogdevicesinc/pyadi-iio.svg?branch=master)](https://travis-ci.org/analogdevicesinc/pyadi-iio)
[![PyPI version](https://badge.fury.io/py/pyadi-iio.svg)](https://badge.fury.io/py/pyadi-iio) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/4bd027bfc5774029a30a9e1cedf5a434)](https://www.codacy.com/app/travis.collins/pyadi-iio?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=analogdevicesinc/pyadi-iio&amp;utm_campaign=Badge_Grade) [![](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/download/releases/3.6.0/)

[[Docs](http://analogdevicesinc.github.io/pyadi-iio/)]
[[Support](http://ez.analog.com)]
[[Wiki](https://wiki.analog.com/resources/tools-software/linux-software/pyadi-iio)]

pyadi-iio is a python abstraction module for ADI hardware with IIO drivers to make them easier to use. The libIIO interface although extremely flexible can be cumbersome to use due to the amount of boilerplate code required for even simple examples, especially when interfacing with buffers. This module has custom interfaces classes for specific parts and development systems which can generally make them easier to understand and use. To get up and running with a device can be as simple as a few lines of code:
```python
import adi

# Create device from specific uri address
sdr = adi.ad9361(uri="ip:192.168.2.1")
# Get data from transceiver
data = sdr.rx()
```

### Currently supported hardware
[Supported parts and boards](supported_parts.md)

### Dependencies
- [libiio with python bindings](https://wiki.analog.com/resources/tools-software/linux-software/libiio)
- [numpy](https://scipy.org/install.html)

### Installing from source
```
tcollins@jeeves:~$ git clone https://github.com/analogdevicesinc/pyadi-iio.git
tcollins@jeeves:~$ cd pyadi-iio
tcollins@jeeves:~$ (sudo) python setup.py install
```
### Installing from pip
```
tcollins@jeeves:~$ (sudo) pip install pyadi-iio
```
### Building doc
Install necessary tools
```
tcollins@jeeves:~$ (sudo) pip install -r requirements_doc.txt
```
Build actual doc with sphinx
```
tcollins@jeeves:~$ cd doc
tcollins@jeeves:~$ make html
```
### Developing
Install necessary tools
```
tcollins@jeeves:~$ (sudo) pip install -r requirements_dev.txt
```

Running pre-commit checks
```
tcollins@jeeves:~$ pre-commit run --all-files
```
