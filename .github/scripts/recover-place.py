#!/usr/bin/env python3
"""Dispatch hardware recovery for a labgrid place.

Looks up the place's `daughter-board` tag on the coordinator, then runs
the per-board recovery routine. Boards that don't yet have a recovery
strategy print "no recovery defined" and exit 0 — that's intentional;
the scaffold is built out as strategies become available.

Today's coverage:
    zc706 + adrv9371  →  adi_lg_plugins.strategies.BootZynq7000JTAGRecovery
                         (consumes recovery-config.yml under .github/)

Usage:
    LG_COORDINATOR=10.0.0.41:20408 recover-place.py <place> [target_state]
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RECOVERY_CONFIG = REPO_ROOT / ".github" / "recovery-config.yml"


def _coord_api_base() -> str:
    coord = os.environ.get("LG_COORDINATOR") or os.environ.get("ADI_LG_COORDINATOR", "")
    if not coord:
        raise SystemExit(
            "LG_COORDINATOR not set (expected host:port for the gRPC coord)"
        )
    host = coord.split(":")[0]
    return f"http://{host}:8000"


def _fetch_place(name: str) -> dict:
    url = f"{_coord_api_base()}/api/places/{name}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.load(resp)


def _load_recovery_config() -> dict:
    if not RECOVERY_CONFIG.exists():
        return {}
    import yaml

    return yaml.safe_load(RECOVERY_CONFIG.read_text()) or {}


def _no_recovery(place_name: str, board: str | None) -> int:
    print(
        f"[recover-place] no recovery strategy defined for "
        f"place={place_name!r} board={board!r}; nothing to do.",
        file=sys.stderr,
    )
    return 0


def _zc706_recovery(
    place_name: str, board: str, target_state: str, config: dict
) -> int:
    """Run BootZynq7000JTAGRecovery against the place.

    The strategy needs a *full* labgrid env with explicit JTAG/TFTP
    resources — RemotePlace can't supply XilinxDeviceJTAG /
    TFTPServerResource if the exporter hasn't registered them. We
    materialize an env from recovery-config.yml's per-place override
    block, falling back to the RemotePlace shape for whatever resources
    are exported. Operator prereqs (Vivado/xsdb, Digilent drivers,
    TFTP root, BOOT.BIN-extracted artifacts) are documented in
    labgrid-plugins/examples/zynq7000_recovery/lg_zc706_recovery.yaml.
    """
    place_cfg = (config.get("places") or {}).get(place_name)
    if not place_cfg:
        print(
            f"[recover-place] {place_name!r}: zc706 recovery requires a per-place "
            f"block in {RECOVERY_CONFIG.relative_to(REPO_ROOT)} with paths to "
            "ps7_init.tcl / u-boot.elf / bitstream / SD image. Skipping until "
            "the operator stages those artifacts.",
            file=sys.stderr,
        )
        return 0

    env_yaml = place_cfg.get("env_yaml")
    if not env_yaml:
        print(
            f"[recover-place] {place_name!r}: missing `env_yaml` in recovery-config.yml. "
            "See labgrid-plugins/examples/zynq7000_recovery/ for a working template.",
            file=sys.stderr,
        )
        return 1

    # Stage the env yaml to a temp file and hand to labgrid.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", prefix=f"recovery-{place_name}-", delete=False
    ) as f:
        f.write(env_yaml)
        env_path = f.name

    try:
        from labgrid.environment import Environment
        from labgrid.strategy import Strategy
    except ImportError as exc:
        print(f"[recover-place] labgrid not importable: {exc}", file=sys.stderr)
        return 1

    env = Environment(env_path)
    target = env.get_target("main")
    strategy = target.get_driver(Strategy)
    print(
        f"[recover-place] running {type(strategy).__name__}.transition({target_state!r})..."
    )
    strategy.transition(target_state)
    print(f"[recover-place] {place_name!r}: recovery complete ({target_state}).")
    return 0


# board name (from coordinator daughter-board tag) → handler.
# Add new entries as recovery strategies become available.
HANDLERS = {
    "adrv9371": _zc706_recovery,  # zc706 + adrv9371 (e.g. bq)
}


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("usage: recover-place.py <place> [target_state]", file=sys.stderr)
        return 2
    place_name = args[0]
    target_state = args[1] if len(args) >= 2 else "sd_boot_verified"

    place = _fetch_place(place_name)
    board = (place.get("tags") or {}).get("daughter-board")
    handler = HANDLERS.get(board)
    if handler is None:
        return _no_recovery(place_name, board)

    config = _load_recovery_config()
    return handler(place_name, board, target_state, config)


if __name__ == "__main__":
    sys.exit(main())
