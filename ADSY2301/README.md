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

## Prerequisites

### Python Requirements

**Python 3.12.10** is required. Download it from the official
[Python 3.12 releases page](https://www.python.org/downloads/).

> The commands below use a Windows command prompt as an example. For
> development, it is recommended to use your preferred IDE (VSCode / PyCharm)
> and set up its corresponding environment accordingly.

### Software Prerequisites — Genalyzer

[Genalyzer](https://github.com/analogdevicesinc/genalyzer) is a C++ library
that facilitates the computation of commonly used data-converter RF
performance metrics in a standards-compliant manner. It supports waveform
generation for characterizing data-converters as well as computation of
performance metrics from time- or frequency-domain data.

Follow the
[Genalyzer C++ download instructions](https://analogdevicesinc.github.io/genalyzer/main/quick_start.html)
for your platform (Mac/Linux/Windows). Once the main C++ library is
installed, the Python bindings are installed in the steps below.

---

## Installing

> **Note:** If you left *"Create venv and install python package dependencies
> (recommended)"* checked during installation, steps 1–5 below will likely
> have already been completed automatically. There is no harm in running them
> again if you are unsure.

### 1. Navigate to this package

Open a command prompt and `cd` to the directory containing this file and
`requirements.txt`. Your path may differ depending on where the package was
installed.

```cmd
cd "C:\Analog Devices\cots-adsy2301-test"
```

### 2. Create & activate a virtual environment

```cmd
python3.12 -m venv adsy2301_python_venv
.\adsy2301_python_venv\Scripts\activate
```

After activation you should see the venv name in the prompt:

```
(adsy2301_python_venv) C:\Analog Devices\cots-adsy2301-test>
```

### 3. Upgrade pip

Make sure pip is at least version 24.0.0:

```cmd
python -m pip install --upgrade pip
```

> If this gives a permissions error, re-open the command prompt as an
> administrator, reactivate the venv, and try again.

### 4. Install Python dependencies

```cmd
pip install -r requirements.txt
```

### 5. Install Genalyzer Python bindings

```cmd
pip install "genalyzer @ git+https://github.com/analogdevicesinc/genalyzer.git#subdirectory=bindings/python"
```

> In future versions this will be included in `requirements.txt`.

Installing dependencies may take a few minutes depending on your internet
connection.

### Notes

- Packages installed within the venv do **not** affect your global Python
  environment.
- To exit the venv run `deactivate`. Reactivate it at any time with
  `.\adsy2301_python_venv\Scripts\activate`.
- All ADSY2301 scripts expect to be run from within the venv.
- To verify installed packages run `pip list`.

### VSCode setup (optional, recommended)

1. Install the **Python** extension (by Microsoft) from the VSCode
   marketplace.
2. Press `Ctrl+Shift+P` → *"Python: Select Interpreter"* → choose the
   interpreter labelled **Python (adsy2301_python_venv)**.
3. You should now be able to run and debug the ADSY2301 examples directly
   from VSCode.

---

## Quick Start

### 1. Bootstrap the ADAR1000 Tiles

```bash
python ADSY2301_bootstrap_tiles.py
```

This connects to the SoM via SSH and runs the ADAR1000 initialisation script
(~4-5 minutes on first boot).

### 2. Run RX Calibration

```bash
python ADSY2301_Rx_Cal.py
```

Place an RF source at boresight, press Enter when prompted, and the script
will calibrate gain + phase across all 64 elements.

### 3. Run Beam Steering Demo

```bash
python ADSY2301_Rx_Steering_Example.py
```

After calibration, the script steers the beam to a configurable angle
(default: 30°) and prints the measured signal drop relative to boresight.

### 4. Run RX Electronic Beam Sweep

```bash
python ADSY2301_Rx_Electronic_Sweep.py
```

Sweeps the receive beam from -60° to +60° in 5° steps (configurable).
A live plot displays combined magnitude vs. steering angle. Results are
saved as a `.png` image and `.mat` data file under the output directory.

### 5. Run TX Calibration

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

### 6. Run TX Electronic Beam Sweep

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
