#!/usr/bin/env bash
# Install pyadi-iio (editable) plus the labgrid coordinator client and
# pytest plugins into a persistent uv-managed venv at
# ~/.cache/pyadi-iio-ci/venv on the current runner host.
#
# Reused across runs so dependency resolution is paid once per host.
# The editable install always points at the current checkout, so PR
# code changes are picked up without recreating the venv.

set -euo pipefail

VENV="$HOME/.cache/pyadi-iio-ci/venv"

# Pinned to the tfcollins fork because it carries the plugin-support
# patches the adi_lg_plugins strategies depend on.  Revisit when
# upstream merges them.
LABGRID_PIP='labgrid @ git+https://github.com/tfcollins/labgrid.git@tfcollins/plugin-support'

export PATH="$HOME/.local/bin:$PATH"

if [[ ! -x "$VENV/bin/python" ]]; then
    echo "Creating pyadi-iio venv at $VENV" >&2
    uv venv --quiet "$VENV"
fi

uv pip install --quiet --python "$VENV/bin/python" \
    -e ".[jesd]" \
    "$LABGRID_PIP" \
    pytest-libiio \
    pytest-xdist
