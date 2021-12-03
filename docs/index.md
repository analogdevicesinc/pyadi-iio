# Analog Devices Hardware Python Interfaces

<p align="center">
<img id="logo_dark_mode" src="images/PyADI-IIO_Logo_300.png" alt="logo">
<img id="logo_light_mode" src="images/PyADI-IIO_Logo_g_300.png" alt="logo">
<!-- <img src="images/PyADI-IIO_Logo_g_300.png" width="500" alt="PyADI-IIO Logo"> </br> -->

<a class="reference external image-reference" href="http://travis-ci.org/analogdevicesinc/pyadi-iio"><img alt="https://secure.travis-ci.org/analogdevicesinc/pyadi-iio.png" src="https://secure.travis-ci.org/analogdevicesinc/pyadi-iio.png" /></a>
<a class="reference external image-reference" href="https://badge.fury.io/py/pyadi-iio"><img alt="https://badge.fury.io/py/pyadi-iio.svg" src="https://badge.fury.io/py/pyadi-iio.svg" /></a>
<a class="reference external image-reference" href="https://www.codacy.com/app/travis.collins/pyadi-iio?utm_source=github.com&amp;amp;utm_medium=referral&amp;amp;utm_content=analogdevicesinc/pyadi-iio&amp;amp;utm_campaign=Badge_Grade"><img alt="https://api.codacy.com/project/badge/Grade/4bd027bfc5774029a30a9e1cedf5a434" src="https://api.codacy.com/project/badge/Grade/4bd027bfc5774029a30a9e1cedf5a434" /></a>

</p>

**pyadi-iio** is a python abstraction module for ADI hardware with IIO drivers to make them easier to use. The libIIO interface although extremely flexible can be cumbersome to use due to the amount of boilerplate code required for even simple examples, especially when interfacing with buffers. This module has custom interfaces classes for specific parts and development systems which can generally make them easier to understand and use. To get up and running with a device can be as simple as a few lines of code:

```python

 import adi

 # Create device from specific uri address
 sdr = adi.ad9361(uri="ip:192.168.2.1")
 # Get data from transceiver
 data = sdr.rx()
```

## Requirements

- numpy
- [libiio](http://github.com/analogdevicesinc/libiio)
- [(Optional) libad9361 for AD9361 specific devices](http://github.com/analogdevicesinc/libad9361)
