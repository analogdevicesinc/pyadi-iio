"""prism_report pytest plugin — wired hooks."""
from __future__ import annotations

import datetime as _dt
import io
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

from test.plugins.prism_report import __version__ as _PLUGIN_VERSION
from test.plugins.prism_report.analyze import analyze, PayloadError
from test.plugins.prism_report.capture import (
    SessionPre, capture_session_post, capture_session_pre,
)
from test.plugins.prism_report.config import Config, ConfigError
from test.plugins.prism_report.manifest import OutputDir
from test.plugins.prism_report.render import render_spectrum
from test.plugins.prism_report.upload import UploadError, upload


@dataclass
class _State:
    cfg: Config
    out_dir: OutputDir
    pre: SessionPre | None = None
    iio_uri: str | None = None
    started_at: str = ""


def pytest_addoption(parser: pytest.Parser) -> None:
    g = parser.getgroup("prism_report", "Prism test-report plugin")
    g.addoption("--prism-report", action="store_true", default=False)
    g.addoption("--prism-out", default=None)
    g.addoption("--prism-url", default=None)
    g.addoption("--prism-email", default=None)
    g.addoption("--prism-password", default=None)
    g.addoption("--prism-project", default=None)
    g.addoption("--prism-run-name", default=None)
    g.addoption("--prism-tag", action="append", default=[])
    g.addoption("--prism-labgrid-place", default=None)
    g.addoption("--prism-no-labgrid", action="store_true", default=False)
    g.addoption("--prism-dmesg-via", default=None,
                choices=["auto", "ssh", "console", "none"])
    g.addoption("--prism-dmesg-ssh-user", default=None)
    g.addoption("--prism-dmesg-ssh-key", default=None)
    g.addoption("--prism-fail-on-upload-error", action="store_true",
                default=False)


def pytest_configure(config: pytest.Config) -> None:
    if not config.getoption("--prism-report"):
        return
    try:
        cfg = Config.from_pytest(config)
    except ConfigError as exc:
        raise pytest.UsageError(f"prism-report: {exc}") from exc
    out_dir = OutputDir(cfg.out_dir)
    out_dir.initialize()
    config._prism_report_state = _State(cfg=cfg, out_dir=out_dir)
    # Force a JUnit XML output path inside our out-dir:
    junit_path = cfg.out_dir / "junit.xml"
    config.option.xmlpath = str(junit_path)
    # Emit any config-time warnings.
    for topic, msg in cfg.warnings.items():
        config.issue_config_time_warning(
            pytest.PytestConfigWarning(f"prism-report: {topic}: {msg}"),
            stacklevel=1,
        )


def pytest_sessionstart(session: pytest.Session) -> None:
    st = getattr(session.config, "_prism_report_state", None)
    if st is None:
        return
    st.started_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    iio_uri = _resolve_iio_uri(session.config)
    st.iio_uri = iio_uri
    st.pre = capture_session_pre(st.cfg, iio_uri or "")
    if st.pre.iio_info is not None:
        st.out_dir.write_run_artifact("iio_info.txt", st.pre.iio_info,
                                      kind="iio_info")
    if st.pre.boot_log is not None:
        st.out_dir.write_run_artifact("boot.log", st.pre.boot_log,
                                      kind="boot_log")
    if st.pre.dmesg is not None:
        st.out_dir.write_run_artifact("dmesg_pre.log", st.pre.dmesg,
                                      kind="dmesg_pre")


def _resolve_iio_uri(config) -> str | None:
    # pyadi-iio's existing fixture conventions: --uri or PYADI_IIO_URI.
    # --uri may not be registered by every host project; tolerate that.
    try:
        cli_uri = config.getoption("--uri", default=None)
    except (ValueError, KeyError):
        cli_uri = None
    return cli_uri or _env("PYADI_IIO_URI")


def _env(key: str) -> str | None:
    import os
    v = os.environ.get(key)
    return v or None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if call.when != "call":
        return
    st = getattr(item.config, "_prism_report_state", None)
    if st is None:
        return
    payload = getattr(pytest, "data_log", None)
    if payload is None:
        return
    pytest.data_log = None  # consume

    test_failed = call.excinfo is not None
    failure_summary = call.excinfo.exconly() if test_failed else ""

    # Legacy {"html": "..."} payload: attach verbatim, no genalyzer.
    if "html" in payload and "iq" not in payload:
        st.out_dir.write_case_artifact(
            case_nodeid=item.nodeid, filename="legacy.html",
            content=payload["html"].encode("utf-8"),
            kind="legacy_html",
        )
        return

    try:
        result = analyze(payload)
    except PayloadError as exc:
        sys.stderr.write(
            f"prism-report: case {item.nodeid}: payload error: {exc}\n"
        )
        return
    except Exception as exc:
        sys.stderr.write(
            f"prism-report: case {item.nodeid}: analyze raised: {exc}\n"
        )
        return

    try:
        html = render_spectrum(
            result, payload,
            meta={
                "test_id": item.nodeid,
                "test_failed": test_failed,
                "failure_summary": failure_summary,
            },
        )
    except Exception as exc:
        sys.stderr.write(
            f"prism-report: case {item.nodeid}: render failed: {exc}\n"
        )
        return

    st.out_dir.write_case_artifact(
        case_nodeid=item.nodeid, filename="spectrum.html",
        content=html.encode("utf-8"), kind="spectrum",
    )
    iq_buf = io.BytesIO()
    np.savez_compressed(
        iq_buf, iq=np.asarray(payload["iq"]),
        fs=np.float64(payload["fs"]),
        expected_tones=np.array(payload.get("expected_tones") or []),
        domain=np.array(payload.get("domain", "complex")),
    )
    st.out_dir.write_case_artifact(
        case_nodeid=item.nodeid, filename="iq.npz",
        content=iq_buf.getvalue(), kind="iq_raw",
    )
    metrics = {
        "sfdr_dbc": result.sfdr_dbc, "snr_db": result.snr_db,
        "sinad_db": result.sinad_db, "thd_dbc": result.thd_dbc,
        "nsd_dbfs_per_hz": result.nsd_dbfs_per_hz,
        "test_metrics": payload.get("metrics", {}),
    }
    st.out_dir.write_case_artifact(
        case_nodeid=item.nodeid, filename="metrics.json",
        content=json.dumps(metrics, indent=2, default=str).encode("utf-8"),
        kind="metrics",
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    st = getattr(session.config, "_prism_report_state", None)
    if st is None:
        return
    post = capture_session_post(st.cfg, st.iio_uri or "", st.pre or
                                SessionPre(None, None, None, None, "skipped"))
    if post.dmesg_post is not None:
        st.out_dir.write_run_artifact("dmesg_post.log", post.dmesg_post,
                                      kind="dmesg_post")
    if post.dmesg_diff is not None:
        st.out_dir.write_run_artifact("dmesg_diff.log", post.dmesg_diff,
                                      kind="dmesg_diff")
    run_meta = {
        "started_at": st.started_at,
        "ended_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "iio_uri": st.iio_uri,
        "labgrid_place": st.cfg.labgrid_place,
        "tags": dict(st.cfg.user_tags),
        "plugin_version": _PLUGIN_VERSION,
        "dmesg_capture_method": (st.pre.dmesg_capture_method
                                  if st.pre else "skipped"),
    }
    st.out_dir.finalize(run_meta=run_meta)
    sys.stderr.write(f"prism-report: wrote run to {st.out_dir.root}\n")

    if not st.cfg.upload_url:
        return
    try:
        result = upload(st.out_dir, st.cfg)
    except UploadError as exc:
        sys.stderr.write(
            f"prism-report: upload failed: {exc}; preserved at "
            f"{st.out_dir.root}\n"
        )
        if st.cfg.fail_on_upload_error:
            session.exitstatus = 5
        return
    sys.stderr.write(
        f"prism-report: uploaded run {result.run_id} (status={result.status}) "
        f"-> {st.cfg.upload_url}{result.url}\n"
    )
