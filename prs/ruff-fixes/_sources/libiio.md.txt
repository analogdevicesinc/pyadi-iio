# libiio Direct Access

**pyadi-iio** is built on-top of **libiio**, specifically its python bindings [pylibiio](https://pypi.org/project/pylibiio/). However, **pyadi-iio** tries to limit or shape the top-level access of certain properties of drivers exposed by _libiio_ and its structure so users do not have to understand how **libiio** works. This is great until you need access to something not directly exposed by one of **pyadi-iio**'s classes. Fortunately, there is an easy way to directly access the [libiio python API](https://analogdevicesinc.github.io/libiio/v0.23/python/index.html) when necessary.

## libiio Entry Points

The main object interface to **libiio** is through the **ctx** property, which is available in every device-specific class. The context is used internally by **ctx** to do all **libiio** specific operations. Here is an example of using the **ctx** property with **pyadi-iio** and **libiio**:

```python
import adi
import iio

sdr = adi.Pluto("ip:pluto.local")
ctx = iio.Context("ip:pluto.local")

for d1, d2 in zip(sdr.ctx.devices, ctx.devices):
    print(d1.name, "|", d2.name)
```

Output:

```bash
ad9361-phy | ad9361-phy
xadc | xadc
cf-ad9361-dds-core-lpc | cf-ad9361-dds-core-lpc
cf-ad9361-lpc | cf-ad9361-lpc
```

By convention device-specific classes will populate the main control driver as property **\_ctrl**, the RX driver associated with data (DMA) as **\_rxadc**, and the TX driver associated with data (DMA) and DDSs as **\_txdac**. However, this is not always guaranteed depending on class implementation.

Please refer to the [libiio python API](https://analogdevicesinc.github.io/libiio/v0.23/python/index.html) for documentation on using **libiio** directly.

## Examples

Here is an example of setting the enable state machine on Pluto through the **libiio** API through **pyadi-iio**:

```python
import adi

sdr = adi.Pluto()

phy = sdr.ctx.find_device("ad9361-phy")
# View current mode
print(phy.attrs["ensm_mode"].value)
# View options
print(phy.attrs["ensm_mode_available"].value)
# Update mode
phy.attrs["ensm_mode"].value = "alert"
# View new mode
print(phy.attrs["ensm_mode"].value)
```

Output:

```bash
fdd
sleep wait alert fdd pinctrl pinctrl_fdd_indep
alert
```

Here we can print all **libiio** debug attributes:

```python
import adi

sdr = adi.Pluto()

phy = sdr.ctx.find_device("ad9361-phy")
for dattr in phy.debug_attrs:
    print(dattr, phy.debug_attrs[dattr])
```

Output:

```bash
digital_tune digital_tune
calibration_switch_control calibration_switch_control
multichip_sync multichip_sync
gaininfo_rx2 gaininfo_rx2
gaininfo_rx1 gaininfo_rx1
bist_timing_analysis bist_timing_analysis
gpo_set gpo_set
bist_tone bist_tone
bist_prbs bist_prbs
loopback loopback
initialize initialize
adi,bb-clk-change-dig-tune-enable adi,bb-clk-change-dig-tune-enable
adi,axi-half-dac-rate-enable adi,axi-half-dac-rate-enable
adi,txmon-2-lo-cm adi,txmon-2-lo-cm
adi,txmon-1-lo-cm adi,txmon-1-lo-cm
adi,txmon-2-front-end-gain adi,txmon-2-front-end-gain
adi,txmon-1-front-end-gain adi,txmon-1-front-end-gain
...
```

On some devices it is possible to access registers. This must be done through the Device classes of the context:

```python
import adi

sdr = adi.Pluto()

phy = sdr.ctx.find_device("ad9361-phy")
# Read product ID register
pi = phy.reg_read(0x37)
print(f"ID: {hex(pi)}")
# Enable near-end loopback in the HDL core
rxfpga = sdr.ctx.find_device("cf-ad9361-lpc")
rxfpga.reg_write(0x80000418, 0x1)  # I channel
rxfpga.reg_write(0x80000458, 0x1)  # Q channel
```

Output:

```bash
ID: 0xa
```

## libiio v1.X support

**pyadi-iio** supports **libiio** v1.X and v0.X. However, the **libiio** python bindings are not available on PyPI for v1.X and they are currently unstable. If you require stable operation, please use **libiio** v0.X. Its also possible that not all ecosystem features are available yet for v1.X. Please report any issues you find with v1.X.
