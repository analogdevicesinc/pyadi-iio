# pyadi-iio: [BETA] Analog Devices python interfaces for hardware with Industrial I/O drivers

[![Build Status](https://travis-ci.org/analogdevicesinc/pyadi-iio.svg?branch=master)](https://travis-ci.org/analogdevicesinc/pyadi-iio) 
[![PyPI version](https://badge.fury.io/py/pyadi-iio.svg)](https://badge.fury.io/py/pyadi-iio) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/4bd027bfc5774029a30a9e1cedf5a434)](https://www.codacy.com/app/travis.collins/pyadi-iio?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=analogdevicesinc/pyadi-iio&amp;utm_campaign=Badge_Grade)

## Still in beta and feedback is appreciated

[[Docs](http://analogdevicesinc.github.io/pyadi-iio/)]
[[Support](http://ez.analog.com)]
[[Wiki](https://wiki.analog.com/resources/tools-software/linux-software/pyadi-iio)]

### Currently supported hardware
- AD936X (Pluto, FMComms, ADRV936X)
- AD9371
- ADRV9009

### Dependencies
- libiio with python bindings
- numpy

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
