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
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

__all__ = ["PrismClient"]


def resolve_job_url(
    jobs: list[dict[str, Any]], *, job_name: str, runner_name: str | None = None
) -> str | None:
    """Match an exact display name or the unique active job on this runner."""
    matches = [job.get("html_url") for job in jobs if job.get("name") == job_name]
    if not matches and runner_name:
        matches = [
            job.get("html_url")
            for job in jobs
            if job.get("runner_name") == runner_name
            and job.get("status") == "in_progress"
        ]
    return str(matches[0]) if len(matches) == 1 and matches[0] else None


def _read_explicit_ci(raw: str, job_url: str | None) -> dict[str, Any]:
    """Read an explicit provider object or file."""
    ci = (
        json.loads(raw)
        if raw.lstrip().startswith("{")
        else json.loads(Path(raw.removeprefix("@")).read_text(encoding="utf-8"))
    )
    if not isinstance(ci, dict):
        raise ValueError("expected an object")
    if job_url:
        ci["job_url"] = job_url
    return ci


def _github_identity() -> dict[str, Any]:
    """Collect the run, attempt, and matrix supplied by Actions."""
    repository = os.getenv("GITHUB_REPOSITORY", "")
    run_id = os.getenv("GITHUB_RUN_ID", "")
    attempt = os.getenv("GITHUB_RUN_ATTEMPT", "1")
    ci: dict[str, Any] = {
        "provider": "github",
        "repository": repository,
        "workflow": os.getenv("GITHUB_WORKFLOW", ""),
        "run_id": run_id,
        "attempt": attempt,
        "job_name": os.getenv("PRISM_CI_JOB_NAME") or os.getenv("GITHUB_JOB", ""),
    }
    if repository and run_id:
        server = os.getenv("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
        ci[
            "run_url"
        ] = f"{server}/{repository}/actions/runs/{run_id}/attempts/{attempt}"
    raw_matrix = os.getenv("PRISM_CI_MATRIX")
    if raw_matrix:
        try:
            matrix = json.loads(raw_matrix)
            if not isinstance(matrix, dict):
                raise ValueError("expected a JSON object")
            ci["matrix"] = matrix
        except (ValueError, TypeError):
            ci["collection_errors"] = ["PRISM_CI_MATRIX is not a JSON object"]
    return ci


def _github_jobs(ci: dict[str, Any], token: str) -> list[dict[str, Any]]:
    """Read every page of jobs from the current run attempt."""
    api = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    jobs: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (
            f"{api}/repos/{ci['repository']}/actions/runs/{ci['run_id']}"
            f"/attempts/{ci['attempt']}/jobs?per_page=100&page={page}"
        )
        if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
            raise ValueError("GitHub API URL must be HTTP or HTTPS")
        request = urllib.request.Request(  # noqa: S310
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
            batch = json.load(response).get("jobs", [])
        jobs.extend(batch)
        if len(batch) < 100:
            return jobs
        page += 1


def _attach_github_job(ci: dict[str, Any], job_url: str | None) -> None:
    """Attach an explicit or uniquely resolved job link."""
    explicit_url = (
        job_url or os.getenv("PRISM_CI_JOB_URL") or os.getenv("GITHUB_JOB_URL")
    )
    if explicit_url:
        ci["job_url"] = explicit_url
        return
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token or not all(
        ci.get(key) for key in ("repository", "run_id", "job_name")
    ):
        return
    try:
        jobs = _github_jobs(ci, token)
        resolved = resolve_job_url(
            jobs, job_name=ci["job_name"], runner_name=os.getenv("RUNNER_NAME")
        )
        if resolved:
            ci["job_url"] = resolved
    except (OSError, ValueError, TypeError, AttributeError):
        ci.setdefault("collection_errors", []).append(
            "Exact GitHub job link unavailable"
        )


def detect_ci(*, job_url: str | None = None) -> dict[str, Any] | None:
    """Collect explicit CI metadata or automatically detect GitHub Actions."""
    explicit = os.getenv("PRISM_CI_JSON")
    if explicit:
        try:
            return _read_explicit_ci(explicit, job_url)
        except (OSError, ValueError):
            return {
                "collection_errors": [
                    "PRISM_CI_JSON could not be read as a JSON object"
                ]
            }
    if os.getenv("GITHUB_ACTIONS", "").lower() != "true":
        return {"job_url": job_url} if job_url else None
    ci = _github_identity()
    _attach_github_job(ci, job_url)
    return ci


class PrismClient:
    def __init__(
        self, base_url: str, token: str | None = None, insecure: bool = False,
    ) -> None:
        """Initialize authentication and the HTTP transport."""
        # Reject non-http(s) schemes up front so the noqa: S310 below is true.
        # urllib's default opener handles file://, ftp://, data://, etc., which
        # an attacker who can set PRISM_URL could abuse for local-file
        # disclosure / SSRF. See ruff S310. This guard must mirror the one in
        # clients/python-pytest/src/pytest_prism/client.py since this file is
        # the vendoring source for pyadi-iio's prism-report plugin.
        scheme = urllib.parse.urlsplit(base_url).scheme.lower()
        if scheme not in ("http", "https"):
            raise ValueError(
                f"PrismClient base_url must be http or https; got scheme {scheme!r}"
            )
        self.base_url = base_url.rstrip("/")
        # When set, authenticate every request with a bearer API token instead
        # of the cookie session (no login + no CSRF needed; the server skips
        # CSRF for bearer auth).
        self.token = token
        if not insecure:
            insecure = os.getenv("PRISM_INSECURE", "").lower() in ("1", "true", "yes")
        self.insecure = insecure
        self.jar = http.cookiejar.CookieJar()
        handlers: list[urllib.request.BaseHandler] = [
            urllib.request.HTTPCookieProcessor(self.jar)
        ]
        if self.insecure:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            handlers.append(urllib.request.HTTPSHandler(context=ctx))
        self.opener = urllib.request.build_opener(*handlers)

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
        # base_url's scheme is validated to http/https in __init__, so this is safe.
        req = urllib.request.Request(  # noqa: S310
            url, data=body, method=method, headers=headers or {}
        )
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        csrf = self._read_cookie("prism_csrf")
        if csrf and method in ("POST", "PUT", "PATCH", "DELETE"):
            req.add_header("X-Prism-Csrf", csrf)
        try:
            with self.opener.open(req) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()
        except urllib.error.URLError as exc:
            raise RuntimeError(f"request to {url} failed: {exc.reason}") from exc

    # --------------------------------------------------------------------- #
    # Auth
    # --------------------------------------------------------------------- #

    def login(self, email: str, password: str) -> None:
        if self.token:
            return  # bearer token auth: no session login needed
        payload = json.dumps({"email": email, "password": password}).encode("utf-8")
        code, body = self._request(
            "POST",
            "/api/v1/auth/login",
            body=payload,
            headers={"Content-Type": "application/json"},
        )
        if code != 200:
            raise RuntimeError(f"login failed: HTTP {code} {body!r}")

    # --------------------------------------------------------------------- #
    # Projects
    # --------------------------------------------------------------------- #

    def ensure_project(self, slug: str, name: str, description: str = "") -> None:
        """Create the project if it doesn't exist. 409 (already exists) is fine."""
        payload = json.dumps(
            {"slug": slug, "name": name, "description": description}
        ).encode("utf-8")
        code, body = self._request(
            "POST",
            "/api/v1/projects",
            body=payload,
            headers={"Content-Type": "application/json"},
        )
        if code not in (201, 409):
            raise RuntimeError(f"project create failed: HTTP {code} {body!r}")

    def set_genalyzer_auto(self, slug: str, enabled: bool = True) -> None:
        """Toggle a project's genalyzer auto-analysis (admin-only PATCH)."""
        payload = json.dumps({"genalyzer_auto": enabled}).encode("utf-8")
        code, body = self._request(
            "PATCH",
            f"/api/v1/projects/{urllib.parse.quote(slug)}",
            body=payload,
            headers={"Content-Type": "application/json"},
        )
        if code != 200:
            raise RuntimeError(f"set genalyzer_auto failed: HTTP {code} {body!r}")

    def project_exists(self, slug: str) -> bool:
        code, _ = self._request("GET", f"/api/v1/projects/{urllib.parse.quote(slug)}")
        return code == 200

    def delete_project(self, slug: str) -> None:
        """Delete a project and everything under it (runs, artifacts, blobs)."""
        # Admin-only (`DELETE /api/v1/admin/projects/{slug}`). A 404 is treated as
        # success so `--reset` is a no-op when the project doesn't exist yet.
        code, body = self._request(
            "DELETE", f"/api/v1/admin/projects/{urllib.parse.quote(slug)}"
        )
        if code not in (200, 204, 404):
            raise RuntimeError(f"delete project failed: HTTP {code} {body!r}")

    # --------------------------------------------------------------------- #
    # Runs
    # --------------------------------------------------------------------- #

    def list_runs(self, project_slug: str) -> list[dict[str, object]]:
        code, body = self._request(
            "GET", f"/api/v1/runs?project={urllib.parse.quote(project_slug)}"
        )
        if code != 200:
            raise RuntimeError(f"list runs failed: HTTP {code} {body!r}")
        result: list[dict[str, object]] = json.loads(body)
        return result

    def get_run(self, run_id: str) -> dict[str, object]:
        code, body = self._request("GET", f"/api/v1/runs/{urllib.parse.quote(run_id)}")
        if code != 200:
            raise RuntimeError(f"get run failed: HTTP {code} {body!r}")
        result: dict[str, object] = json.loads(body)
        return result

    def upload_run(
        self,
        *,
        project_slug: str,
        run_name: str,
        junit_xml: bytes,
        archive_zip: bytes | None = None,
        tags: dict[str, str] | None = None,
        ci: dict[str, Any] | None = None,
        hardware: dict[str, Any] | None = None,
        job_url: str | None = None,
    ) -> dict[str, object]:
        """POST /api/v1/runs with a hand-built multipart body.

        Returns the parsed JSON response (includes run `id` + initial `status`).
        Raises RuntimeError on any non-201.
        """
        boundary = f"----prism{uuid.uuid4().hex}"
        parts: list[bytes] = []

        def _add_field(name: str, value: str) -> None:
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            )
            parts.append(value.encode("utf-8"))
            parts.append(b"\r\n")

        def _add_file(
            name: str, filename: str, content_type: str, content: bytes
        ) -> None:
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
            )
            parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
            parts.append(content)
            parts.append(b"\r\n")

        metadata: dict[str, Any] = {
            "project_slug": project_slug,
            "name": run_name,
            "tags": tags or {},
        }
        metadata["ci"] = dict(ci) if ci is not None else detect_ci(job_url=job_url)
        if job_url and metadata["ci"] is not None:
            metadata["ci"]["job_url"] = job_url
        metadata["hardware"] = hardware
        _add_field("metadata", json.dumps(metadata))
        _add_file("junit", "junit.xml", "application/xml", junit_xml)
        if archive_zip is not None:
            _add_file("archive", "archive.zip", "application/zip", archive_zip)
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        code, resp_body = self._request(
            "POST", "/api/v1/runs", body=body, headers=headers
        )
        if code != 201:
            raise RuntimeError(f"upload {run_name!r} failed: HTTP {code} {resp_body!r}")
        result: dict[str, object] = json.loads(resp_body)
        return result
