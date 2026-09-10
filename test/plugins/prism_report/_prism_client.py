"""Stdlib-only HTTP client for the Prism API.

Shared by the other scripts in this directory (`seed_demo.py`,
`upload_run.py`) so the login + CSRF + multipart dance lives in exactly
one place. No external dependencies — works anywhere Python 3.10+ is
installed (CI runners included).

Session state (auth + CSRF cookies) is held in an in-memory cookie jar
so all subsequent `self._request` calls automatically carry the login
cookie and, for mutations, the `X-Prism-Csrf` header.
"""
from __future__ import annotations

import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid

__all__ = ["PrismClient"]


class PrismClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    # --------------------------------------------------------------------- #
    # Low-level request plumbing
    # --------------------------------------------------------------------- #

    def _read_cookie(self, name: str) -> str | None:
        for c in self.jar:
            if c.name == name:
                return c.value
        return None

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, bytes]:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
        csrf = self._read_cookie("prism_csrf")
        if csrf and method in ("POST", "PUT", "PATCH", "DELETE"):
            req.add_header("X-Prism-Csrf", csrf)
        try:
            with self.opener.open(req) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    # --------------------------------------------------------------------- #
    # Auth
    # --------------------------------------------------------------------- #

    def login(self, email: str, password: str) -> None:
        payload = json.dumps({"email": email, "password": password}).encode("utf-8")
        code, body = self._request(
            "POST", "/api/v1/auth/login",
            body=payload, headers={"Content-Type": "application/json"},
        )
        if code != 200:
            raise RuntimeError(f"login failed: HTTP {code} {body!r}")

    # --------------------------------------------------------------------- #
    # Projects
    # --------------------------------------------------------------------- #

    def ensure_project(self, slug: str, name: str, description: str = "") -> None:
        """Create the project if it doesn't exist. 409 (already exists) is fine."""
        payload = json.dumps({"slug": slug, "name": name, "description": description}).encode("utf-8")
        code, body = self._request(
            "POST", "/api/v1/projects",
            body=payload, headers={"Content-Type": "application/json"},
        )
        if code not in (201, 409):
            raise RuntimeError(f"project create failed: HTTP {code} {body!r}")

    def project_exists(self, slug: str) -> bool:
        code, _ = self._request("GET", f"/api/v1/projects/{urllib.parse.quote(slug)}")
        return code == 200

    # --------------------------------------------------------------------- #
    # Runs
    # --------------------------------------------------------------------- #

    def list_runs(self, project_slug: str) -> list[dict]:
        code, body = self._request(
            "GET", f"/api/v1/runs?project={urllib.parse.quote(project_slug)}"
        )
        if code != 200:
            raise RuntimeError(f"list runs failed: HTTP {code} {body!r}")
        return json.loads(body)

    def get_run(self, run_id: str) -> dict:
        code, body = self._request("GET", f"/api/v1/runs/{urllib.parse.quote(run_id)}")
        if code != 200:
            raise RuntimeError(f"get run failed: HTTP {code} {body!r}")
        return json.loads(body)

    def delete_run(self, run_id: str) -> None:
        code, body = self._request("DELETE", f"/api/v1/runs/{urllib.parse.quote(run_id)}")
        if code not in (204, 404):
            raise RuntimeError(f"delete run failed: HTTP {code} {body!r}")

    def upload_run(
        self,
        *,
        project_slug: str,
        run_name: str,
        junit_xml: bytes,
        archive_zip: bytes | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict:
        """POST /api/v1/runs with a hand-built multipart body.

        Returns the parsed JSON response (includes run `id` + initial `status`).
        Raises RuntimeError on any non-201.
        """
        boundary = f"----prism{uuid.uuid4().hex}"
        parts: list[bytes] = []

        def _add_field(name: str, value: str) -> None:
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            parts.append(value.encode("utf-8"))
            parts.append(b"\r\n")

        def _add_file(name: str, filename: str, content_type: str, content: bytes) -> None:
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
            )
            parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
            parts.append(content)
            parts.append(b"\r\n")

        metadata = {"project_slug": project_slug, "name": run_name, "tags": tags or {}}
        _add_field("metadata", json.dumps(metadata))
        _add_file("junit", "junit.xml", "application/xml", junit_xml)
        if archive_zip is not None:
            _add_file("archive", "archive.zip", "application/zip", archive_zip)
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        code, resp_body = self._request("POST", "/api/v1/runs", body=body, headers=headers)
        if code != 201:
            raise RuntimeError(f"upload {run_name!r} failed: HTTP {code} {resp_body!r}")
        return json.loads(resp_body)
