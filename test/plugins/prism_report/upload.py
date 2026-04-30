"""Upload a finalized OutputDir to a Prism instance.

Builds a multipart payload (junit.xml + artifacts.zip + tags) and POSTs to
/api/v1/runs, then polls until ingest is ready. Local export is left on disk
on any failure for offline retry.
"""
from __future__ import annotations

import io
import time
import uuid
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
    junit = out_root / "junit.xml"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in out_root.rglob("*"):
            if not p.is_file():
                continue
            if p.name == "junit.xml":
                continue
            zf.write(p, arcname=str(p.relative_to(out_root)))
    return buf.getvalue()


def _multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]
               ) -> tuple[bytes, str]:
    boundary = f"----prism{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for k, v in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        )
        chunks.append(v.encode("utf-8") + b"\r\n")
    for k, (filename, content, ctype) in files.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{k}"; '
            f'filename="{filename}"\r\n'
            f'Content-Type: {ctype}\r\n\r\n'.encode()
        )
        chunks.append(content + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def upload(out_dir, cfg, *, poll_timeout_s: float = 60.0,
           poll_interval_s: float = 1.0) -> RunResult:
    if not cfg.upload_url:
        raise UploadError("upload() called with no upload_url")
    junit_bytes = (out_dir.root / "junit.xml").read_bytes()
    artifacts_bytes = _build_artifacts_zip(out_dir.root)

    fields: dict[str, str] = {
        "project": cfg.upload_project,
        "run_name": cfg.run_name,
    }
    for k, v in cfg.user_tags.items():
        fields[f"tag.{k}"] = v
    body, ctype = _multipart(
        fields,
        {
            "junit": ("junit.xml", junit_bytes, "application/xml"),
            "artifacts": ("artifacts.zip", artifacts_bytes,
                          "application/zip"),
        },
    )

    client = PrismClient(cfg.upload_url)
    try:
        client.login(cfg.upload_email, cfg.upload_password)
    except Exception as exc:
        raise UploadError(f"login failed: {exc}") from exc

    code, resp = client._request(
        "POST", "/api/v1/runs", body=body,
        headers={"Content-Type": ctype},
    )
    if code not in (200, 201):
        raise UploadError(
            f"run create failed: HTTP {code} {resp[:200]!r}"
        )
    import json as _json
    run_id = _json.loads(resp).get("id")
    if not run_id:
        raise UploadError(f"missing run id in response: {resp[:200]!r}")

    deadline = time.monotonic() + poll_timeout_s
    status = "pending"
    url = f"/runs/{run_id}"
    while time.monotonic() < deadline:
        code, resp = client._request("GET", f"/api/v1/runs/{run_id}")
        if code == 200:
            data = _json.loads(resp)
            status = data.get("status", "unknown")
            url = data.get("url", url)
            if status in ("ready", "failed"):
                break
        time.sleep(poll_interval_s)
    return RunResult(run_id=run_id, status=status, url=url)
