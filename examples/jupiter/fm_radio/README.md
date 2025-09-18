# Jupiter FM Radio Example

This is an example that demonstrates loading a profile into the Jupiter module based on ADRV9002 with pyadi-iio. Then using GNU Radio to demodulate and play FM radio stations.

## Requirements

- ADRV9002-based Jupiter module
- FM antenna connected to port RX1A
- GNU Radio installed on your system (3.9 or later with the gr-iio module)
- pyadi-iio library installed

## Running the Example

This example assumes you are using the network context (URI). If you IP is different or different context, please change the URI accordingly.

First, load the stream and profile using the provided Python script:

```bash
python load_profile.py
```

This script will load the profile (json) and stream (bin) file into the transceiver and update the sample rate to 768kHz. This was generated with the ADRV9002 Transceiver Evaluation Software (TES).

Updating the profile is only needed once, unless you power cycle the device.

Next, launch GNU Radio Companion:

```bash
gnuradio-companion
```

Load the provided `fm_radio_jupyter.grc` flowgraph. Make sure to set the source device string to match your Jupiter module's URI.

Set the fm_frequency variable to your desired FM station frequency (in Hz).

Run the flowgraph, and you should be able to hear the FM station through your audio output device.

## Notes

You many need to adjust the gain settings in the flowgraph to get a clear signal depending on your location and antenna setup. It is easiest to do that in pyadi-iio before starting GNU Radio or run IIO-Scope along side GNU Radio to do more GUI based adjustments.