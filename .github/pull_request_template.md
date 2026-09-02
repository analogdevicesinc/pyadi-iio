# Description

Summarize the change and the motivation. Link the issue this fixes.

Fixes # (issue)

## Type of change

- [ ] Bug fix
- [ ] New device class interface
- [ ] New feature on an existing class
- [ ] Breaking change
- [ ] Documentation only
- [ ] Test or CI only

# How has this been tested?

State explicitly whether this was tested against **real hardware**, an **emulated context** (iio-emu), or **not run**. Name the part(s) and the context URI or board used.

- Hardware / emulation:
- Commands run (e.g. `python3 -m pytest -k ad4080 --adi-hw-map`):
- Result:

**Test configuration**
* Kernel / libiio version:
* OS:
* FPGA carrier (if applicable):

# Documentation

- [ ] No documentation change needed
- [ ] Updated existing docs under `doc/source/`
- [ ] Added a new device page and linked it from the relevant toctree

# New device class interfaces

Skip this section if the PR does not add a new device class.

- [ ] Class extends one of the common base classes in `adi.device_base` (`rx_chan_comp`, `tx_chan_comp`, or a `_no_buff` variant). If not, explain why in the description. See the [Device Base Classes](https://analogdevicesinc.github.io/pyadi-iio/dev/device_base.html) developer doc page.
- [ ] `compatible_parts` lists every part number this class supports
- [ ] Part numbers added to `supported_parts.md` (verify with `invoke checkparts`)
- [ ] Emulation context (xml_gen, not iio_genxml) added under `test/emu/` and referenced from a test
- [ ] Tests added that run against the emulation context in CI

# Checklist

- [ ] `invoke precommit` passes locally
- [ ] All commits are signed off (`Signed-off-by: Name <email>`)
- [ ] No new warnings from the build or doc generation
- [ ] Dependent changes in libiio, kernel, or HDL are merged and referenced
