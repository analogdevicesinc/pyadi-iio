#!/usr/bin/env python3
"""Dispatch hardware recovery for a labgrid place.

Looks up the place's `daughter-board` tag on the coordinator, then runs
the per-board recovery routine. Boards that don't yet have a recovery
strategy print "no recovery defined" and exit 0 — that's intentional;
the scaffold is built out as strategies become available.

Today's coverage:
    zc706 + adrv9371  →  adi_lg_plugins.strategies.BootZynq7000JTAGRecovery
                         (consumes recovery-config.yml under .github/)
    zc706 + adrv9009  →  adi_lg_plugins.strategies.BootFPGASoCSSH
                         (power-cycle recovery; env auto-fetched from coord)

Usage:
    LG_COORDINATOR=10.0.0.41:20408 recover-place.py <place> [target_state]
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import time
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


def _fetch_env_yaml(name: str, tier: str = "boot") -> str:
    """Fetch the coordinator-generated labgrid env yaml for a place.

    Same endpoint the hw-matrix dynamic_mode leg uses, so a recovery run
    boots the board through the identical strategy + resources as CI.
    """
    url = f"{_coord_api_base()}/api/places/{name}/env-yaml?tier={tier}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return resp.read().decode("utf-8")


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


def _bootfpgasocssh_recovery(
    place_name: str, board: str, target_state: str, config: dict
) -> int:
    """Recover a BootFPGASoCSSH board (e.g. nemo: zc706 + adrv9009).

    Unlike the JTAG-recovery path, BootFPGASoCSSH needs no special
    resources — the coordinator already generates a working boot env for
    this place (the same one CI uses). Recovery here means: drive the
    strategy to a Linux shell, reconstructing the Environment between
    attempts so a ``broken`` Strategy doesn't poison the retry. Each fresh
    Strategy walks ``powered_off -> ... -> shell``, i.e. a hard
    power-cycle — which is what clears a board wedged after a failed boot.

    The per-place block in recovery-config.yml is optional: it may pin an
    explicit ``env_yaml`` and/or a ``retries`` count. With no block, we
    auto-fetch the env and retry twice.
    """
    place_cfg = (config.get("places") or {}).get(place_name) or {}
    retries = int(place_cfg.get("retries", 2))

    env_yaml = place_cfg.get("env_yaml")
    if not env_yaml:
        try:
            env_yaml = _fetch_env_yaml(place_name)
        except Exception as exc:
            print(
                f"[recover-place] {place_name!r}: could not fetch boot env from "
                f"coordinator ({exc}); add an `env_yaml` block to "
                f"{RECOVERY_CONFIG.relative_to(REPO_ROOT)} to recover offline.",
                file=sys.stderr,
            )
            return 1

    # BootFPGASoCSSH's only meaningful terminal is the Linux shell; the
    # JTAG-oriented target_state choices don't apply here.
    if target_state not in ("shell", "sd_boot_verified"):
        print(
            f"[recover-place] {place_name!r}: BootFPGASoCSSH ignores "
            f"target_state={target_state!r}; driving to 'shell'.",
            file=sys.stderr,
        )

    try:
        from labgrid.environment import Environment
        from labgrid.strategy import Strategy
    except ImportError as exc:
        print(f"[recover-place] labgrid not importable: {exc}", file=sys.stderr)
        return 1

    last_err: Exception | None = None
    for attempt in range(1, retries + 2):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", prefix=f"recovery-{place_name}-", delete=False
        ) as f:
            f.write(env_yaml)
            env_path = f.name
        try:
            env = Environment(env_path)
            target = env.get_target("main")
            strategy = target.get_driver(Strategy)
            print(
                f"[recover-place] attempt {attempt}: "
                f"{type(strategy).__name__}.transition('shell')..."
            )
            strategy.transition("shell")
            print(f"[recover-place] {place_name!r}: recovered to Linux shell.")
            return 0
        except Exception as exc:
            last_err = exc
            if attempt > retries:
                break
            print(
                f"[recover-place] attempt {attempt} failed ({exc}); "
                "reconstructing Environment for another power-cycle",
                file=sys.stderr,
            )
            time.sleep(5)

    print(
        f"[recover-place] {place_name!r}: recovery failed after {retries + 1} "
        f"power-cycle attempts: {last_err}. Board likely needs hands-on "
        "intervention (check serial console / SD image at the bench).",
        file=sys.stderr,
    )
    return 1


# board name (from coordinator daughter-board tag) → handler.
# Add new entries as recovery strategies become available.
HANDLERS = {
    "adrv9371": _zc706_recovery,  # zc706 + adrv9371 (e.g. bq)
    "adrv9009": _bootfpgasocssh_recovery,  # zc706 + adrv9009 (e.g. nemo)
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
