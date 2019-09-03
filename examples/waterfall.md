# Waterfall Example

This example demonstrates a simple waterfall plot using ADALM-PLUTO and some standard python packages for plotting. The example transmits a "real" tone where I and Q are in-phase so we observe symmetrical spectrum. This example has been adapted from [here](https://hackaday.io/project/165403/logs) for ADALM-PLUTO.

## Requirements
- [ADALM-PLUTO Hardware](https://www.analog.com/en/design-center/evaluation-hardware-and-software/evaluation-boards-kits/ADALM-PLUTO.html)
- [ADALM-PLUTO drivers](https://wiki.analog.com/university/tools/pluto/users/quick_start)
- pyadi-iio
- matplotlib
- pygame
- PIL

## Running

`python waterfall.y`

with an SMA cable connecting TX and RX you should see something similar to the figure below:
![waterfall_plot](https://wiki.analog.com/_media/resources/tools-software/image.png?w=400&tok=87fadd)
