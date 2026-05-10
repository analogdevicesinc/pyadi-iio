#!/usr/bin/env bash
# Install pyadi-iio (editable) plus dev/test requirements and the
# labgrid coordinator client into a persistent uv-managed venv at
# ~/.cache/pyadi-iio-ci/venv on the current runner host.
#
# Reused across runs so dependency resolution is paid once per host.
# The editable install always points at the current checkout, so PR
# code changes are picked up without recreating the venv.

set -euo pipefail

VENV="$HOME/.cache/pyadi-iio-ci/venv"

# adi-labgrid-plugins registers custom resource classes (KuiperRelease,
# VesyncPowerDriver, KuiperDLDriver, etc.) that the coordinator forwards
# from the exporter when a place is acquired — without these, labgrid
# fails place-resolution with InvalidConfigError.  It transitively pulls
# in the tfcollins/plugin-support labgrid fork the strategies need.
# [kuiper] extra pulls in pytsk3 for ImageExtractor / KuiperDLDriver,
# which BootFPGASoC[TFTP] strategies invoke during target construction.
# pytsk3 has manylinux wheels so no libtsk-dev is needed at install time.
ADI_LG_PLUGINS_PIP='adi-labgrid-plugins[kuiper] @ git+https://github.com/tfcollins/labgrid-plugins.git'

export PATH="$HOME/.local/bin:$PATH"

if [[ ! -x "$VENV/bin/python" ]]; then
    echo "Creating pyadi-iio venv at $VENV" >&2
    uv venv --quiet "$VENV"
fi

# requirements_dev.txt covers scipy/scapy/matplotlib/etc. that
# test/conftest.py + test/rf/spec transitively import on collection.
# pytest-rerunfailures lets the workflow retry tests that fail with
# Microblaze-IIO-daemon BrokenPipe drops on nuc without masking real
# failures (filtered via --only-rerun in hardware-test.yml).
uv pip install --quiet --python "$VENV/bin/python" \
    -e ".[jesd]" \
    -r requirements_dev.txt \
    "$ADI_LG_PLUGINS_PIP" \
    pytest-rerunfailures
