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
`BootFPGASoCSSH` strategy (power, serial shell, SSH).

The images under test are the prebuilt `system_top.bit.bin` files in
adi-innersource/cse-bsps, branch `dev/talise-prod-ddr-hw-test`,
`talise/prebuilt/{full,ddr_lo,ddr_hi}/` (Git LFS; that folder's README also has the manual,
shell-only load and the HDL sources). Install, then run inside a reservation:

```
pip install -e . -r test/talise/requirements.txt
TALISE_HW=1 TALISE_CONFIG=ddr_lo TALISE_PL_BIN=/path/to/system_top.bit.bin \
adi-lg request --part adrv9009zu11eg --mode reserve --wait 1800 \
  --run 'python -m pytest test/talise --confcutdir=test/talise -o addopts= -v'
```

`TALISE_PL_BIN` is the bitstream converted for fpga_manager
(`bootgen -arch zynqmp -process_bitstream bin`). The fixture uploads it over SSH to
/lib/firmware, does a full PL reconfiguration (fpga_manager `firmware`, or the
`talise_pl.dtbo` overlay on /fpga-full), and sets M_AXI_HPM0_FPD to the 128 bits the
production design uses (FPD_SLCR.AFI_FS), since a runtime load does not rerun psu_init.

On a JTAG-only place (`BootZynqMPJTAG`), set `TALISE_BOOT_MODE=sd1-ls`: the board is powered
on, its boot mode is overridden over JTAG and it boots its own SD card, whatever the switches
say. Without it the fixture JTAG-loads the stock PL and psu_init from
`TALISE_STOCK_BITSTREAM_REMOTE` / `TALISE_STOCK_PSU_INIT_REMOTE` instead. Either JTAG path
needs a newer labgrid-plugins than the `v6` tag in `requirements.txt` (which is enough for the
`BootFPGASoCSSH` places CI uses): `BootZynqMPJTAG.boot_mode` came with #186 and the exporter
payload paths with #189, so install main at 7ddcb06 or later after the requirements:

```
pip install "labgrid-plugins @ git+https://github.com/tfcollins/labgrid-plugins.git@7ddcb064d449ce891464b1123b898ee771a9983c"
```

| Variable | Meaning |
|----------|---------|
| `TALISE_HW=1` | enable the hardware tests (skipped otherwise) |
| `TALISE_CONFIG` | `full`, `ddr_lo` or `ddr_hi`: the build under test (selects the part mapping) |
| `TALISE_PL_BIN` | local path of that build's `system_top.bit.bin` (its sha256 is checked on the target) |
| `TALISE_PL_URL` | optional: HTTP URL the board downloads the same `.bit.bin` from (`wget`), instead of an SSH upload; e.g. serve the prebuilt folder with `python3 -m http.server` on a host the board can reach |
| `TALISE_BOOT_MODE` | optional, JTAG places: boot mode to force (e.g. `sd1-ls`) |
| `TALISE_STOCK_BITSTREAM_REMOTE`, `TALISE_STOCK_PSU_INIT_REMOTE` | JTAG places without `TALISE_BOOT_MODE`: stock bitstream / psu_init.tcl paths on the exporter |
| `TALISE_JTAG_PROMPT_TIMEOUT` | seconds to wait for the U-Boot prompt after a JTAG boot (default 120) |
| `TALISE_MIG1_DATAPATH=1` | enable the MIG 1 DAC FIFO loopback test |
| `TALISE_LOG_DIR` | where boot / console logs go (default `./boot_logs`) |
| `LG_ENV` | labgrid env of the reserved place (exported by `adi-lg request`) |

Without hardware: `python -m pytest test/talise/test_talise_offline.py --confcutdir=test/talise -o addopts=`.

Tests:

* `test_production_design_loaded`: the axi_sysid ROM names the production project.
* `test_pl_ddr_calibration[mig0|mig1]`: `ddr_calib_gpio` (0x83A00000 for the PS; nominal
  0x43A00000 plus the ZynqMP HPM0_LPD offset) bit 0 / bit 1.
* `test_mig0_memory[data_bus|address_bus|pattern]`: `pl_ddr_memtest.py` on the target over
  `/dev/mem` at 0x4_0000_0000. Errors are reported per byte lane and mapped to the part.
  Skipped if MIG 0 did not calibrate: an access to an uncalibrated MIG can hang the CPU.
* `test_mig1_dacfifo_loopback` (opt-in, `TALISE_MIG1_DATAPATH=1`): MIG 1 is reachable only
  through the TX DAC FIFO, checked with a cyclic ramp in Talise framer loopback.
* `test_talise_offline.py`: no hardware; mapping and fault-injection checks of the helper.
