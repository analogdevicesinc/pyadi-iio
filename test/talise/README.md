# ADRV9009-ZU11EG production PL DDR4 tests

Per-part checks of the two PL DDR4 MIGs of the `adrv2crr_fmc_production` HDL builds
(MIG 0: U30/U31, MIG 1: U41/U42). The `ddr_lo` / `ddr_hi` builds narrow both MIGs to one
part, so a failure points at a single part.

| `TALISE_CONFIG` | MIG 0     | MIG 1     |
|-----------------|-----------|-----------|
| `full`          | U30 + U31 | U41 + U42 |
| `ddr_lo`        | U30       | U41       |
| `ddr_hi`        | U31       | U42       |

The place must be SD strapped and use the `BootFPGASoCSSH` strategy. Run inside a reservation:

```
TALISE_HW=1 TALISE_CONFIG=ddr_lo TALISE_BOOT_BIN=/path/to/BOOT.BIN \
adi-lg request --part adrv9009zu11eg --carrier adrv2crrfmc --mode reserve --wait 1800 \
  --run 'python -m pytest test/talise --confcutdir=test/talise -o addopts= -v'
```

The fixture keeps the card's BOOT.BIN as `/boot/BOOT.BIN.stock-ci`, boots the image under
test, and restores the stock BOOT.BIN on teardown.

Tests:

* `test_production_design_loaded`: the axi_sysid ROM names the production project.
* `test_pl_ddr_calibration[mig0|mig1]`: `ddr_calib_gpio` (0x43A00000) bit 0 / bit 1.
* `test_mig0_memory[data_bus|address_bus|pattern]`: `pl_ddr_memtest.py` on the target over
  `/dev/mem` at 0x4_0000_0000. Errors are reported per byte lane and mapped to the part.
  Skipped if MIG 0 did not calibrate: an access to an uncalibrated MIG can hang the CPU.
* `test_mig1_dacfifo_loopback` (opt-in, `TALISE_MIG1_DATAPATH=1`): MIG 1 is reachable only
  through the TX DAC FIFO, checked with a cyclic ramp in Talise framer loopback.
* `test_talise_offline.py`: no hardware; mapping and fault-injection checks of the helper.
