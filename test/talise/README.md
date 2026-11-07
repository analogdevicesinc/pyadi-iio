# ADRV9009-ZU11EG production PL DDR4 tests

Per-part checks of the two PL DDR4 MIGs of the `adrv2crr_fmc_production` HDL builds
(MIG 0: U30/U31, MIG 1: U41/U42). The `ddr_lo` / `ddr_hi` builds narrow both MIGs to one
part, so a failure points at a single part.

| `TALISE_CONFIG` | MIG 0     | MIG 1     |
|-----------------|-----------|-----------|
| `full`          | U30 + U31 | U41 + U42 |
| `ddr_lo`        | U30       | U41       |
| `ddr_hi`        | U31       | U42       |

The board boots its own SD card image; only the PL is replaced at runtime, so the card is
never modified and a power cycle restores the stock design. The place uses the
`BootFPGASoCSSH` strategy (power, serial shell, SSH). Run inside a reservation:

```
TALISE_HW=1 TALISE_CONFIG=ddr_lo TALISE_PL_BIN=/path/to/system_top.bit.bin \
adi-lg request --part adrv9009zu11eg --mode reserve --wait 1800 \
  --run 'python -m pytest test/talise --confcutdir=test/talise -o addopts= -v'
```

`TALISE_PL_BIN` is the bitstream converted for fpga_manager
(`bootgen -arch zynqmp -process_bitstream bin`). The fixture uploads it over SSH to
/lib/firmware, does a full PL reconfiguration (fpga_manager `firmware`, or the
`talise_pl.dtbo` overlay on /fpga-full), and sets M_AXI_HPM0_FPD to the 128 bits the
production design uses (FPD_SLCR.AFI_FS), since a runtime load does not rerun psu_init.

Tests:

* `test_production_design_loaded`: the axi_sysid ROM names the production project.
* `test_pl_ddr_calibration[mig0|mig1]`: `ddr_calib_gpio` (0x43A00000) bit 0 / bit 1.
* `test_mig0_memory[data_bus|address_bus|pattern]`: `pl_ddr_memtest.py` on the target over
  `/dev/mem` at 0x4_0000_0000. Errors are reported per byte lane and mapped to the part.
  Skipped if MIG 0 did not calibrate: an access to an uncalibrated MIG can hang the CPU.
* `test_mig1_dacfifo_loopback` (opt-in, `TALISE_MIG1_DATAPATH=1`): MIG 1 is reachable only
  through the TX DAC FIFO, checked with a cyclic ramp in Talise framer loopback.
* `test_talise_offline.py`: no hardware; mapping and fault-injection checks of the helper.
