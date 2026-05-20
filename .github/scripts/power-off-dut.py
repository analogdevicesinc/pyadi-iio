#!/usr/bin/env python3
"""Power off the DUT referenced by ``LG_ENV`` (best-effort test teardown).

Run at the end of a hw-matrix leg's pytest step, while the place is still
acquired, so the board is left powered down once labgrid tests finish.
Tries each known power driver in turn; if none is bound, or power-off
fails, it logs and exits 0 — teardown must never turn a green run red.

Mirrors the resource shapes the coordinator generates: the ZC706 places
expose ``HomeAssistantPowerDriver`` and the ZCU102/VCU118 places expose
``VesyncPowerDriver``.
"""

from __future__ import annotations

import os
import sys

# Order doesn't matter — only one is bound per target — but list the
# drivers actually used across the lab first.
POWER_DRIVERS = (
    "HomeAssistantPowerDriver",
    "VesyncPowerDriver",
    "NetworkPowerDriver",
    "USBPowerDriver",
)


def main() -> int:
    lg_env = os.environ.get("LG_ENV")
    if not lg_env:
        print("[power-off] LG_ENV not set; nothing to power off", file=sys.stderr)
        return 0

    try:
        from labgrid.environment import Environment
    except ImportError as exc:
        print(f"[power-off] labgrid not importable: {exc}", file=sys.stderr)
        return 0

    try:
        target = Environment(lg_env).get_target("main")
    except Exception as exc:
        print(f"[power-off] could not load target from LG_ENV: {exc}", file=sys.stderr)
        return 0

    driver = None
    chosen = None
    for name in POWER_DRIVERS:
        try:
            driver = target.get_driver(name)
        except Exception:
            driver = None
        if driver is not None:
            chosen = name
            break

    if chosen is None:
        print("[power-off] no power driver bound to target; skipping", file=sys.stderr)
        return 0

    try:
        target.activate(driver)
        driver.off()
        print(f"[power-off] DUT powered off via {chosen}", file=sys.stderr)
    except Exception as exc:
        print(f"[power-off] {chosen}.off() failed: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
