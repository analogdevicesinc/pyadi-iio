"""upload(): exercises a tiny in-process fake of the Prism API."""
from __future__ import annotations

import http.server
import json
import threading
import time
from pathlib import Path

import pytest

from test.plugins.prism_report.config import Config
from test.plugins.prism_report.manifest import OutputDir
from test.plugins.prism_report.upload import upload, UploadError


class _FakeHandler(http.server.BaseHTTPRequestHandler):
    runs: dict[str, str] = {}  # run_id -> status
    received: list[dict] = []

    def log_message(self, *args, **kwargs):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        if self.path == "/api/v1/auth/login":
            self.send_response(200)
            self.send_header("Set-Cookie", "prism_session=abc; Path=/")
            self.send_header("Set-Cookie", "prism_csrf=xyz; Path=/")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")
            return
        if self.path == "/api/v1/runs":
            csrf = self.headers.get("X-Prism-Csrf")
            if csrf != "xyz":
                self.send_response(403); self.end_headers(); return
            self.received.append({
                "headers": dict(self.headers),
                "len": len(body),
            })
            run_id = "run-1"
            self.runs[run_id] = "pending"
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id": run_id}).encode())
            return
        self.send_response(404); self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/v1/runs/"):
            run_id = self.path.rsplit("/", 1)[-1]
            status = self.runs.get(run_id, "missing")
            if status == "pending":
                self.runs[run_id] = "ready"  # flip on second poll
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "id": run_id, "status": status,
                "url": f"/runs/{run_id}",
            }).encode())
            return
        self.send_response(404); self.end_headers()


@pytest.fixture
def fake_prism():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    _FakeHandler.received.clear()
    _FakeHandler.runs.clear()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def _stage_outdir(tmp_path: Path) -> OutputDir:
    out = OutputDir(tmp_path / "run")
    out.initialize()
    out.write_run_artifact("junit.xml",
                           b"<testsuites><testsuite/></testsuites>",
                           kind="junit")
    out.write_case_artifact(
        case_nodeid="t::c", filename="spectrum.html",
        content=b"<html/>", kind="spectrum",
    )
    out.finalize(run_meta={"x": 1})
    return out


def _cfg(url: str, **kw):
    base = dict(
        enabled=True, out_dir=None, upload_url=url,
        upload_email="u@x", upload_password="p",
        upload_project="p1", run_name="r1",
        user_tags={"branch": "main"}, labgrid_place=None, no_labgrid=True,
        dmesg_via="none", dmesg_ssh_user="root", dmesg_ssh_key=None,
        fail_on_upload_error=False,
    )
    base.update(kw)
    return Config(**base)


def test_upload_round_trip(fake_prism, tmp_path):
    out = _stage_outdir(tmp_path)
    res = upload(out, _cfg(fake_prism))
    assert res.run_id == "run-1"
    assert res.status == "ready"
    assert _FakeHandler.received[0]["headers"].get("X-Prism-Csrf") == "xyz"


def test_login_failure_preserves_local(fake_prism, tmp_path, monkeypatch):
    # Override fake to return 401 on login.
    orig = _FakeHandler.do_POST
    def fail_login(self):
        if self.path == "/api/v1/auth/login":
            self.send_response(401); self.end_headers()
            self.wfile.write(b"{}")
            return
        return orig(self)
    monkeypatch.setattr(_FakeHandler, "do_POST", fail_login)
    out = _stage_outdir(tmp_path)
    with pytest.raises(UploadError, match="login"):
        upload(out, _cfg(fake_prism))
    # Local export still on disk:
    assert (out.root / "manifest.json").exists()
