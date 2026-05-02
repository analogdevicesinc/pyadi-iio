"""L5 bench loop: drives real Pluto, asserts artifacts + SFDR bands."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
THRESHOLDS = yaml.safe_load(
    (Path(__file__).parent / "thresholds.yaml").read_text()
)
PLUTO_URI = os.environ.get("BENCH_PLUTO_URI")


@pytest.mark.bench_pluto
@pytest.mark.skipif(not PLUTO_URI, reason="BENCH_PLUTO_URI not set")
def test_bench_pluto_loopback(tmp_path: Path):
    out = tmp_path / "bench-run"
    cmd = [
        sys.executable, "-m", "pytest",
        "test/test_ad9364_p.py",
        "-k", "test_ad9364_sfdr or test_ad9364_dds_loopback "
              "or test_ad9364_two_tone_loopback or test_ad9364_iq_loopback",
        "--prism-report", f"--prism-out={out}",
        "--prism-no-labgrid",
        "--uri", PLUTO_URI,
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True,
                          timeout=15 * 60)
    assert proc.returncode in (0, 1), (
        f"bench run errored (rc={proc.returncode}): {proc.stderr[-500:]!r}"
    )

    manifest = json.loads((out / "manifest.json").read_text())
    on_disk = {a["filename"] for a in manifest["run_artifacts"]}
    for required in THRESHOLDS["artifacts_required"]:
        # boot.log requires labgrid; we passed --prism-no-labgrid above so
        # it's expected absent. Skip in this profile.
        if required == "boot.log":
            continue
        assert required in on_disk, f"missing run artifact: {required}"

    for case in manifest["cases"]:
        files = {a["filename"] for a in case["artifacts"]}
        for required in THRESHOLDS["case_artifacts_required"]:
            assert required in files, (
                f"case {case['case_nodeid']}: missing {required}"
            )
        # SFDR sanity: pull metrics.json
        rel = next((a["rel_path"] for a in case["artifacts"]
                    if a["filename"] == "metrics.json"), None)
        if rel is None:
            continue
        metrics = json.loads((out / rel).read_text())
        sfdr = metrics.get("sfdr_dbc")
        if sfdr is not None:
            assert sfdr >= THRESHOLDS["sfdr_min_dbc"], (
                f"case {case['case_nodeid']}: SFDR {sfdr} < "
                f"min {THRESHOLDS['sfdr_min_dbc']}"
            )
