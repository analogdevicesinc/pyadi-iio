#!/usr/bin/env bash
# Ensure `uv` is available in $HOME/.local/bin on the runner.
#
# Called at the start of every hw-test workflow step that needs uv.
# On a fresh runner this downloads the standalone installer (~15 MB);
# on subsequent runs it's a no-op.  Exports PATH for the caller via
# $GITHUB_PATH so later steps in the same job see ~/.local/bin too.

set -euo pipefail

UV_BIN="$HOME/.local/bin/uv"

if [[ ! -x "$UV_BIN" ]]; then
    echo "uv not found at $UV_BIN — installing via astral.sh" >&2
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "$HOME/.local/bin" >> "$GITHUB_PATH"
"$UV_BIN" --version
