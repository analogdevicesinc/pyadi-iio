# ADSY2301 — 64-Element Phased-Array Evaluation Scripts

Python scripts for configuring, calibrating, and operating the **ADSY2301**
64-element phased-array evaluation system built around the ADAR1000
beamformer and ADRV9009-ZU11EG transceiver SoM.

## Hardware Overview

| Component | Role |
|---|---|
| 16 × ADAR1000 | 4-channel beamformer ICs (64 elements total, 8 × 8 grid) |
| ADRV9009-ZU11EG | Dual-transceiver System-on-Module (data conversion + digital back-end) |
| ADXUD1AEBZ | Up/down-converter between IF and RF |
| ADF4371 | On-board LO PLL for the up/down-converter |
| TDDN engine | FPGA-based TDD timing controller |

## File Descriptions

| File | Description |
|---|---|
| `ADSY2301.py` | Core helper module — channel enable/disable, gain & phase calibration, beam steering utilities, FFT analysis. Imported by the other scripts as `import ADSY2301 as mr`. |
| `ADSY2301_bootstrap_tiles.py` | SSH-based bootstrap: initialises the 16 ADAR1000 tiles on the SoM. **Run once after every power cycle.** |
| `ADSY2301_Init.py` | Standalone hardware init for interactive debugging. Creates the array object, sets PA bias, and loads saved TX cal values from `tx_cal_values.json`. |
| `ADSY2301_Rx_Cal.py` | End-to-end RX calibration script: gain equalization → phase alignment → before/after comparison plot. |
| `ADSY2301_Rx_Steering_Example.py` | Demonstrates electronic beam steering — calibrates the array, captures at boresight, then steers to a user-defined angle and compares signal levels. |
| `ADSY2301_Rx_Electronic_Sweep.py` | Sweeps the RX beam electronically from -60° to +60° (azimuth or elevation), plotting combined magnitude vs. steering angle in real time. Saves a .png plot and .mat data file. |
| `ADSY2301_Tx_Cal.py` | End-to-end TX calibration script: per-element gain equalisation, optional DAC-channel digital phase alignment, and analog (ADAR1000) null-search phase calibration. Saves results to `tx_cal_values.json`. **Requires a spectrum analyser and power supplies** (see instrument notes in the script). |
| `ADSY2301_Tx_Electronic_Sweep.py` | Sweeps the TX beam electronically from -60° to +60°, measuring radiated power with an external spectrum analyser at each angle. Saves a .png plot and .mat data file. **Requires a spectrum analyser and power supplies** (see instrument notes in the script). |
| `ADSY2301_temp_checker.py` | Polls and displays all 16 ADAR1000 temperature sensors in a live table. |
| `DAC_TDD_Config.py` | Configures the ADRV9009 transmit DACs and TDD timing engine (pulse timing, duty cycle, TR switching). |
| `ADF4371_Internal_LO.py` | Programs the on-board ADF4371 LO PLL frequency. |
| `requirements.txt` | Python dependencies for this folder. |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Bootstrap the ADAR1000 Tiles

```bash
python ADSY2301_bootstrap_tiles.py
```

This connects to the SoM via SSH and runs the ADAR1000 initialisation script
(~4-5 minutes on first boot).

### 3. Run RX Calibration

```bash
python ADSY2301_Rx_Cal.py
```

Place an RF source at boresight, press Enter when prompted, and the script
will calibrate gain + phase across all 64 elements.

### 4. Run Beam Steering Demo

```bash
python ADSY2301_Rx_Steering_Example.py
```

After calibration, the script steers the beam to a configurable angle
(default: 30°) and prints the measured signal drop relative to boresight.

### 5. Run RX Electronic Beam Sweep

```bash
python ADSY2301_Rx_Electronic_Sweep.py
```

Sweeps the receive beam from -60° to +60° in 5° steps (configurable).
A live plot displays combined magnitude vs. steering angle. Results are
saved as a `.png` image and `.mat` data file under the output directory.

### 6. Run TX Calibration

```bash
python ADSY2301_Tx_Cal.py
```

Performs per-element gain equalisation and analog phase calibration on the
transmit path.  A receive horn at boresight connected to a spectrum analyser
is required.  Calibration results are saved to `tx_cal_values.json` and
automatically loaded by the TX sweep script.

> **Instrument note:** This script was developed with a Keysight N9000A (CXA)
> spectrum analyser, E36233A power supply, and N6705B DC power analyser.
> Search for `*** INSTRUMENT ***` in the script to find the sections that
> need to be adapted for your own equipment.

### 7. Run TX Electronic Beam Sweep

```bash
python ADSY2301_Tx_Electronic_Sweep.py
```

Sweeps the transmit beam from -60° to +60° in 1° steps (configurable),
reading the measured power from an external spectrum analyser at each angle.
Results are saved as a `.png` image and `.mat` data file.

> **Instrument note:** Same instrument requirements as TX Calibration.
> Search for `*** INSTRUMENT ***` in the script.

## Configuration

Most scripts connect to the SoM at `ip:192.168.1.1` by default. Edit the
`url` or `talise_uri` variable at the top of each script if your network
configuration differs.

The TX scripts also require VISA addresses for the bench instruments
(spectrum analyser, power supplies).  These are defined near the top of each
script and marked with `*** INSTRUMENT ADDRESS ***`.

## License

Copyright (C) 2025 Analog Devices, Inc.  
SPDX short identifier: ADIBSD
