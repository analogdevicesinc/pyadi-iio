# ADSY2301 — 64-Element Phased-Array Example Scripts

Python examples for configuring, calibrating, and operating the **ADSY2301**
phased-array evaluation system. All scripts use the helper module
[`adi/adsy2301.py`](../../adi/adsy2301.py), imported as:

```python
from adi import adsy2301 as mr
```

## Hardware Overview

| Component | Role | Accessed via |
|---|---|---|
| 16 × ADAR1000 | 4-channel beamformers (64 elements, 8 × 8 grid) | `dev.BFC` |
| ADRV9009-ZU11EG | Dual-transceiver SoM (data conversion + FPGA) | `dev.ADRV9009` |
| ADMV1320 / ADMV1420 | TX up-converter / RX down-converter | `dev.udc.admv1320`, `dev.udc.admv1420` |
| ADF4382 | Up/down-converter LO PLL | `dev.udc.adf4382` |
| ADMV8913 | Switched filter bank | `dev.udc.admv8913` |
| ADRF5030 | UDC TX/RX switch | `dev.udc.adrf5030` |
| TDDN engine | FPGA TDD timing controller | `adi.tddn(uri)` |

## Example Scripts

| File | Description |
|---|---|
| `ADSY2301_RX_Init_quad_tile.py` | Initializes the full 64-element (16 × ADAR1000) array for RX: BFC/UDC/ADRV9009 init, `sdr_init`, `tdd_init`, `RX_UDC_Band_3()`, all elements at max RX gain and 0° phase. Commented lines show how to enable all/selected RX channels. |
| `ADSY2301_RX_Init_single_tile.py` | Beamformer-only RX init for a single 16-element tile (4 × ADAR1000): max RX gain, 0° phase. UDC (LO, ADMVs, filter, switch) and ADRV9009/TDD setup are included as commented-out OPTIONAL blocks the user can uncomment. |
| `ADSY2301_Init_Tx_quad_tile.py` | Initializes the 64-element array for TX: PA/power rails off during setup, `TX_UDC_Band_0()`, LO at 14.9 GHz, TR source switched to FPGA (`external`) with bias toggle, then PA rails on and element 33 enabled. |
| `ADSY2301_Rx_Cal.py` | End-to-end RX calibration: gain equalization (`rx_gain`) → phase alignment (`find_phase_delay_fixed_ref`, `phase_analog`) → before/after plot saved as `ADSY2301_64Element_Electronic_Steering_Array_Calibration.png`. Requires an RF source at boresight. |
| `LO_Printout.py` | Reads back and prints the ADF4382 (`adf4382a`) LO settings: frequency, phase, enable, bleed polarity, auto-align, gain, and charge-pump currents for both channels. |
| `tdd_example.py` | Standalone ADRV9009 + TDDN example: generates a pulsed CW tone, programs the TDD channels (frame length, TR pulse, offload syncs), transmits a cyclic buffer, and captures/plots synchronized RX frames. |

## User-Configurable Parameters

All scripts connect to the SoM via an IIO URI defined at the top of the file:

```python
host_ip = "10.75.161.151"   # change to your SoM IP
host_uri = "ip:" + host_ip
```

`tdd_example.py` / `tdd_barker_example.py` also expose a `USER CONFIGURABLE
PARAMETERS` block (RF frequency, TX gain, frame length, duty cycle, capture
count, waveform amplitude, etc.).

## Typical Initialization Flow

```python
from adi import adsy2301 as mr

dev = mr.adsy2301(uri="ip:10.75.161.151")
dev.init_BFC(chip_ids=[...], device_map=[...],
             element_map=..., device_element_map={...})
dev.init_UDC()
dev.init_ADRV9009()

mr.sdr_init(dev)
mr.tdd_init(dev, TXRX_Bit=0)
dev.BFC.initialize_devices(pa_off=-4.8, pa_on=-4.8, lna_off=-4.8, lna_on=-4.8)
dev.udc.RX_UDC_Band_3()          # or TX_UDC_Band_0() for transmit

mr.enable_rx_channel(dev.BFC)    # all elements, or a list e.g. [1, 2, 3]
```

The `chip_ids`, `device_map`, `element_map`, and `device_element_map` for the
quad-tile (64-element) and single-tile (16-element) layouts are given in the
corresponding `*_Init_*` scripts.

## `adi/adsy2301.py` API Reference

### Class `adsy2301(uri)`

| Member | Description |
|---|---|
| `init_BFC(chip_ids, device_map, element_map, device_element_map)` | Creates `dev.BFC` (an `adar1000_array` subclass). |
| `init_UDC()` | Initializes ADMV8913, ADRF5030, ADF4382, ADMV1320, ADMV1420 under `dev.udc`. |
| `init_ADRV9009()` | Creates `dev.ADRV9009` (`adrv9009_zu11eg`). |
| `BFC.BF_PWR_EN_01..04` | Beamformer power-rail enables (GPIO). |
| `BFC.BF_PA_ON_01..04` | PA-on control lines (GPIO). |

### UDC (`dev.udc`)

| Member | Description |
|---|---|
| `RX_UDC_Band_1()` | RX, RF 8–9 GHz, LO 13.9 GHz |
| `RX_UDC_Band_2()` | RX, RF 9–10 GHz, LO 13.4 GHz  |
| `RX_UDC_Band_3()` | RX, RF 10–11 GHz, LO 14.9 GHz |
| `RX_UDC_Band_4()` | RX, RF 11–12 GHz, LO 16.4 GHz  |
| `TX_UDC_Band_0()` | Configures the ADMV1320 TX up-converters (3–12 GHz IF). Does not set the LO, switch or filter. |
| `admv8913.set_filter_settings(hp, lp)`, `set_filter_band1..4()`, `set_filter_widest()` | Filter bank control. |
| `adrf5030.TX_SW_Enable()` / `RX_SW_Enable()` | Set UDC TX/RX switch. |

The `RX_UDC_Band_*` methods configure the ADMV1420s, set the ADF4382 LO and
switch the ADRF5030 to RX; they do not change the ADMV8913 filter.
`TX_UDC_Band_0` only configures the ADMV1320s, so the TX switch, filter and
LO must be set separately (as in `ADSY2301_Init_Tx_quad_tile.py`).

### Module Functions

| Category | Functions |
|---|---|
| Channel control | `enable_rx_channel(obj, elements=None)`, `disable_rx_channel(obj, elements=None)`, `enable_tx_channel(obj, elements=None, PA_Bias_Dict=None, gate_voltage_bias=-1.8)`, `disable_tx_channel(obj, elements=None)` |
| Transceiver / timing | `sdr_init(dev)`, `tdd_init(dev, TXRX_Bit)`, `change_duty_cycle(dev, duty_cycle)` (0.0–0.35) |
| PA power | `Vdd_PA_Power_Up(dev)`, `Vdd_PA_Power_Down(dev)` (rail off + PA pinch-off -4.8 V) |
| Data capture | `data_capture(adc)`, `data_capture_cal(adc, cal_values)`, `rx_single_channel_data(...)`, `ADSY2301_power_detector(obj, elements)` |
| RX calibration | `rx_gain(...)`, `gain_codes(...)`, `get_gain_codes(...)`, `find_phase_delay_fixed_ref(...)`, `find_phase_delay_sliding_ref(...)`, `phase_digital(...)`, `phase_analog(...)`, `cal_data(data, phaseCAL)`, `phase_delayer(data, delay)` |
| TX calibration | `phase_analog_tx(adsy2301_obj, SpecAn_obj, ...)` |
| Analysis | `fft(complex_data, combined_waveforms, tone_type)` (Genalyzer), `calc_dbfs(data)`, `get_analog_mag(data)`, `calc_array_pattern(...)`, `quantize_phase(phase, bits=8)` |
| Utilities | `create_dict`, `strip_to_last_two_digits`, `wrap_to_360`, `ind2sub` |

## Prerequisites

- Python 3.12
- [pyadi-iio](https://github.com/analogdevicesinc/pyadi-iio) with ADSY2301 support (`adi.adsy2301`, `adi.adar1000`, `adi.adf4382`, `adi.admv1320`, `adi.admv1420`, `adi.adrv9009_zu11eg`, `adi.tddn`)
- `numpy`, `matplotlib`
- [Genalyzer](https://github.com/analogdevicesinc/genalyzer) C++ library and Python bindings (imported by `adsy2301.py`):

```cmd
pip install "genalyzer @ git+https://github.com/analogdevicesinc/genalyzer.git#subdirectory=bindings/python"
```

Using a virtual environment is recommended:

```cmd
python3.12 -m venv adsy2301_python_venv
adsy2301_python_venv\Scripts\activate
python -m pip install --upgrade pip
pip install pyadi-iio numpy matplotlib
```

## Quick Start

```bash
python ADSY2301_RX_Init_quad_tile.py   # RX bring-up
python ADSY2301_Rx_Cal.py              # RX calibration (RF source at boresight)
python ADSY2301_Init_Tx_quad_tile.py   # TX bring-up
python LO_Printout.py                  # check LO state
python tdd_example.py                  # TDD pulsed TX/RX demo
```

## License

Copyright (C) 2025 Analog Devices, Inc.
SPDX short identifier: ADIBSD
