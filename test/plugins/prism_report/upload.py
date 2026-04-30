"""Upload a finalized OutputDir to a Prism instance.

Delegates the multipart construction to the vendored prism client's
`upload_run`, then polls until ingest is ready. Local export is left on
disk on any failure for offline retry.
"""
from __future__ import annotations

import io
import json as _json
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

from test.plugins.prism_report._prism_client import PrismClient


class UploadError(RuntimeError):
    """Any failure during login, multipart POST, or polling."""


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    url: str


def _build_artifacts_zip(out_root: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in out_root.rglob("*"):
            if not p.is_file():
                continue
            if p.name == "junit.xml":
                continue
            zf.write(p, arcname=str(p.relative_to(out_root)))
    return buf.getvalue()


def upload(out_dir, cfg, *, poll_timeout_s: float = 60.0,
           poll_interval_s: float = 1.0) -> RunResult:
    if not cfg.upload_url:
        raise UploadError("upload() called with no upload_url")
    junit_bytes = (out_dir.root / "junit.xml").read_bytes()
    archive_bytes = _build_artifacts_zip(out_dir.root)

    client = PrismClient(cfg.upload_url)
    try:
        client.login(cfg.upload_email, cfg.upload_password)
    except Exception as exc:
        raise UploadError(f"login failed: {exc}") from exc

    try:
        result = client.upload_run(
            project_slug=cfg.upload_project,
            run_name=cfg.run_name,
            junit_xml=junit_bytes,
            archive_zip=archive_bytes,
            tags=dict(cfg.user_tags),
        )
    except RuntimeError as exc:
        raise UploadError(f"run create failed: {exc}") from exc

    run_id = result.get("id")
    if not run_id:
        raise UploadError(f"missing run id in response: {result!r}")

    deadline = time.monotonic() + poll_timeout_s
    status = result.get("status", "pending")
    url = result.get("url", f"/runs/{run_id}")
    while status not in ("ready", "failed") and time.monotonic() < deadline:
        time.sleep(poll_interval_s)
        code, resp = client._request("GET", f"/api/v1/runs/{run_id}")
        if code == 200:
            data = _json.loads(resp)
            status = data.get("status", status)
            url = data.get("url", url)
    return RunResult(run_id=run_id, status=status, url=url)
