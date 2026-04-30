"""OutputDir round-trip and refusal of non-empty dirs."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from test.plugins.prism_report.manifest import OutputDir


def test_writes_run_and_case_artifacts(tmp_path: Path):
    out = OutputDir(tmp_path / "run1")
    out.initialize()
    out.write_run_artifact("boot.log", b"line1\nline2\n", kind="boot_log")
    out.write_case_artifact(
        case_nodeid="test/foo.py::test_bar[0]",
        filename="spectrum.html",
        content=b"<html></html>",
        kind="spectrum",
    )
    manifest = out.finalize(run_meta={"foo": "bar"})

    assert (tmp_path / "run1" / "boot.log").read_bytes() == b"line1\nline2\n"
    case_dir = tmp_path / "run1" / "cases" / "test_foo.py__test_bar_0_"
    assert (case_dir / "spectrum.html").read_bytes() == b"<html></html>"

    on_disk = json.loads((tmp_path / "run1" / "manifest.json").read_text())
    assert on_disk == manifest
    assert manifest["run_meta"] == {"foo": "bar"}
    assert any(a["filename"] == "boot.log" for a in manifest["run_artifacts"])
    assert any(
        c["case_nodeid"] == "test/foo.py::test_bar[0]"
        for c in manifest["cases"]
    )


def test_refuses_non_empty_dir(tmp_path: Path):
    (tmp_path / "preexisting.txt").write_text("hi")
    out = OutputDir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        out.initialize()
    assert exc.value.code == 4


def test_safe_test_id_strips_unsafe_chars(tmp_path: Path):
    out = OutputDir(tmp_path / "run")
    out.initialize()
    out.write_case_artifact(
        case_nodeid="test/x::test_y[a/b c]",
        filename="x.json",
        content=b"{}",
        kind="metrics",
    )
    cases = list((tmp_path / "run" / "cases").iterdir())
    assert len(cases) == 1
    assert "/" not in cases[0].name
    assert " " not in cases[0].name


def test_finalize_idempotent(tmp_path: Path):
    out = OutputDir(tmp_path / "run")
    out.initialize()
    a = out.finalize(run_meta={"a": 1})
    b = out.finalize(run_meta={"a": 1})
    assert a == b


def test_writes_before_initialize_raises_runtime_error(tmp_path: Path):
    out = OutputDir(tmp_path / "run")
    with pytest.raises(RuntimeError, match="initialize"):
        out.write_run_artifact("x.log", b"hi", kind="boot_log")
    with pytest.raises(RuntimeError, match="initialize"):
        out.write_case_artifact(
            case_nodeid="t::x", filename="y.json", content=b"{}",
            kind="metrics",
        )
