<!-- PYADI-IIO README -->

<p align="center">
<img src="images/PyADI-IIO_Logo_300.png" width="500" alt="PyADI-IIO Logo"> </br>
</p>

<p align="center">
<a href="https://github.com/analogdevicesinc/pyadi-iio/actions">
<img src="https://img.shields.io/github/workflow/status/analogdevicesinc/pyadi-iio/CI%20Pushes/master" alt="Build Status">
</a>

<a href="https://badge.fury.io/py/pyadi-iio">
<img src="https://badge.fury.io/py/pyadi-iio.svg" alt="PyPI version">
</a>

<a href="https://www.codacy.com/app/travis.collins/pyadi-iio?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=analogdevicesinc/pyadi-iio&amp;utm_campaign=Badge_Grade">
<img src="https://api.codacy.com/project/badge/Grade/4bd027bfc5774029a30a9e1cedf5a434" alt="Codacy Badge">
</a>

<a href="https://www.python.org/download/releases/3.6.0/">
<img src="https://img.shields.io/badge/python-3.6+-blue.svg" alt="Python Version">
</a>
</p>

<p align="center">
<a href="http://analogdevicesinc.github.io/pyadi-iio/">
<img alt="GitHub Pages" src="https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg">
</a>

<a href="https://ez.analog.com/sw-interface-tools/f/q-a">
<img alt="EngineerZone" src="https://img.shields.io/badge/Support-on%20EngineerZone-blue.svg">
</a>

<a href="https://wiki.analog.com/resources/tools-software/linux-software/pyadi-iio">
<img alt="Analog Wiki" src="https://img.shields.io/badge/Wiki-on%20wiki.analog.com-blue.svg">
</a>
</p>

---
### pyadi-iio: Analog Devices python interfaces for hardware with Industrial I/O drivers

pyadi-iio is a python abstraction module for ADI hardware with IIO drivers to make them easier to use. The libIIO interface although extremely flexible can be cumbersome to use due to the amount of boilerplate code required for even simple examples, especially when interfacing with buffers. This module has custom interfaces classes for specific parts and development systems which can generally make them easier to understand and use. To get up and running with a device can be as simple as a few lines of code:
```python
import adi

# Create device from specific uri address
sdr = adi.ad9361(uri="ip:192.168.2.1")
# Get data from transceiver
data = sdr.rx()
```

### Currently supported hardware
[Supported parts and boards](https://github.com/analogdevicesinc/pyadi-iio/blob/master/supported_parts.md)

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

To get optional dependency for JESD debugging
```
tcollins@jeeves:~$ (sudo) pip install pyadi-iio[jesd]
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
