#!/usr/bin/env python3
"""Upload a pytest JUnit XML result to a Prism server.

Typical use from CI:

    python3 scripts/upload_run.py results.xml \\
      --project my-service --run-name "$CI_JOB_ID" \\
      --tag branch=$GIT_BRANCH --tag sha=$GIT_SHA --wait

All `--foo` flags fall back to `PRISM_FOO`-style environment variables,
so a hardened CI pipeline can skip the command-line switches entirely:

    PRISM_URL=...  PRISM_EMAIL=...  PRISM_PASSWORD=...  \\
    PRISM_PROJECT=my-service  PRISM_RUN_NAME="$CI_JOB_ID"  \\
      python3 scripts/upload_run.py results.xml

Exit codes:
  0  success
  2  bad argument or input file not found
  3  authentication failed
  4  project not found (pass --auto-create-project to create it)
  5  upload failed (HTTP error from the server)
  6  --wait timed out before ingest finished

Stdlib-only — works on any CI runner with Python 3.10+.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, NamedTuple

# The shared client lives next to this file; use a path-relative import so the
# script works when invoked from anywhere (e.g. `python3 /repo/scripts/...`).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _prism_client import PrismClient

EXIT_OK = 0
EXIT_BAD_INPUT = 2
EXIT_AUTH = 3
EXIT_NO_PROJECT = 4
EXIT_UPLOAD = 5
EXIT_WAIT_TIMEOUT = 6


def _parse_tag(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"--tag expects key=value, got {raw!r}")
    k, v = raw.split("=", 1)
    k = k.strip()
    v = v.strip()
    if not k:
        raise argparse.ArgumentTypeError(f"--tag key is empty in {raw!r}")
    return k, v


class Measurement(NamedTuple):
    name: str
    value: float
    unit: str | None
    spec_min: float | None
    spec_max: float | None


def _parse_measurement(raw: str) -> Measurement:
    """Parse ``name=value[:unit[:min[:max]]]`` (empty trailing fields allowed)."""
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"--measurement expects name=value, got {raw!r}")
    name, _, rest = raw.partition("=")
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"--measurement name is empty in {raw!r}")
    fields = rest.split(":")
    try:
        value = float(fields[0])
    except (IndexError, ValueError):
        raise argparse.ArgumentTypeError(
            f"--measurement value must be numeric in {raw!r}"
        ) from None

    def _opt_float(i: int) -> float | None:
        if len(fields) <= i or fields[i].strip() == "":
            return None
        try:
            return float(fields[i])
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"--measurement field {i} must be numeric in {raw!r}"
            ) from None

    unit = fields[1].strip() if len(fields) > 1 and fields[1].strip() else None
    return Measurement(name, value, unit, _opt_float(2), _opt_float(3))


def inject_measurements(junit_bytes: bytes, measurements: list[Measurement]) -> bytes:
    """Add measurement <property> entries to the JUnit's single testcase.

    Measurements attach to a test case in Prism, so this requires the JUnit to
    contain exactly one <testcase> (the canonical one-suite-one-case shape).
    With zero or several cases it raises ValueError — emit the measurements from
    your test instead (pytest's record_property / pytest-prism record_measurement).
    """
    import xml.etree.ElementTree as ET

    # junit_bytes is the caller's own local JUnit file (their test output), not
    # untrusted network input, and this helper is stdlib-only by design (see
    # CLAUDE.md) so defusedxml is not available. S314 is therefore a non-risk.
    root = ET.fromstring(junit_bytes)  # noqa: S314
    cases = root.findall(".//testcase")
    if len(cases) != 1:
        raise ValueError(
            f"--measurement needs a JUnit with exactly one <testcase>, found {len(cases)}; "
            "record measurements in your test instead"
        )
    case = cases[0]
    props = case.find("properties")
    if props is None:
        props = ET.SubElement(case, "properties")
    for m in measurements:
        ET.SubElement(props, "property", name=m.name, value=repr(m.value))
        if m.unit is not None:
            ET.SubElement(props, "property", name=f"{m.name}__unit", value=m.unit)
        if m.spec_min is not None:
            ET.SubElement(props, "property", name=f"{m.name}__min", value=repr(m.spec_min))
        if m.spec_max is not None:
            ET.SubElement(props, "property", name=f"{m.name}__max", value=repr(m.spec_max))
    # ET.tostring is typed as returning Any in the stdlib stubs; with
    # encoding="utf-8" it returns bytes. Bind to a typed local so mypy's
    # no-any-return is satisfied without a cast or ignore.
    xml: bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml


def _env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    return v if v else default


def _metadata_object(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    if raw.lstrip().startswith("{"):
        value = json.loads(raw)
    else:
        value = json.loads(Path(raw.removeprefix("@")).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("metadata must be a JSON object")
    return value


def _with_transcript(archive: bytes | None, transcript: bytes) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as destination:
        if archive is not None:
            with zipfile.ZipFile(io.BytesIO(archive)) as source:
                for item in source.infolist():
                    if item.filename != "terminal.log":
                        destination.writestr(item, source.read(item))
        destination.writestr("terminal.log", transcript)
    return output.getvalue()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="upload_run.py",
        description="Upload a pytest JUnit XML to Prism.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Each --foo flag also accepts a PRISM_FOO environment variable "
            "(e.g. PRISM_URL, PRISM_EMAIL, PRISM_PROJECT, PRISM_RUN_NAME)."
        ),
    )
    p.add_argument("junit", type=Path, help="Path to the JUnit XML file.")
    p.add_argument(
        "--url",
        default=_env("PRISM_URL", "http://localhost:8000"),
        help="Prism API base URL (env: PRISM_URL).",
    )
    p.add_argument("--email", default=_env("PRISM_EMAIL"), help="Login email (env: PRISM_EMAIL).")
    p.add_argument(
        "--password",
        default=_env("PRISM_PASSWORD"),
        help="Login password (env: PRISM_PASSWORD).",
    )
    p.add_argument(
        "--token",
        default=_env("PRISM_TOKEN"),
        help="API token for bearer auth (env: PRISM_TOKEN). Use instead of --email/--password.",
    )
    p.add_argument(
        "--project",
        default=_env("PRISM_PROJECT"),
        help="Target project slug (env: PRISM_PROJECT).",
    )
    p.add_argument(
        "--run-name",
        dest="run_name",
        default=_env("PRISM_RUN_NAME"),
        help="Name for this Test Suite Run (env: PRISM_RUN_NAME).",
    )
    p.add_argument(
        "--tag",
        action="append",
        type=_parse_tag,
        default=[],
        metavar="key=value",
        help="Repeatable. Arbitrary tag on the run (branch=main, sha=abc123).",
    )
    p.add_argument(
        "--archive",
        type=Path,
        default=_env("PRISM_ARCHIVE"),
        help="Optional .zip of measurement artifacts to upload alongside the JUnit.",
    )
    p.add_argument("--ci-json", default=_env("PRISM_CI_JSON"), help="CI JSON object or file path.")
    p.add_argument(
        "--hardware-json",
        default=_env("PRISM_HARDWARE_JSON"),
        help="Reserved-hardware JSON object or file path.",
    )
    p.add_argument("--job-url", default=_env("PRISM_CI_JOB_URL"), help="Exact CI job URL.")
    p.add_argument(
        "--pytest-log",
        type=Path,
        default=_env("PRISM_PYTEST_LOG"),
        help="Complete pytest terminal transcript to archive (env: PRISM_PYTEST_LOG).",
    )
    p.add_argument(
        "--measurement",
        action="append",
        type=_parse_measurement,
        default=[],
        metavar="name=value[:unit[:min[:max]]]",
        help="Repeatable. Inject a numeric measurement into the JUnit's single "
        "testcase (e.g. channel_power_dBm=-10.2:dBm::-9.0). Becomes a Prism "
        "Measurement with pass/fail margin.",
    )
    p.add_argument(
        "--auto-create-project",
        action="store_true",
        help="Create the target project if it doesn't exist.",
    )
    p.add_argument(
        "--wait",
        nargs="?",
        type=int,
        const=60,
        default=None,
        metavar="SECONDS",
        help="After upload, poll every 2s until the run is no longer "
        "pending. Bare flag uses a 60s timeout; pass a value for longer.",
    )
    p.add_argument(
        "--insecure",
        "-k",
        action="store_true",
        default=(_env("PRISM_INSECURE", "false") or "false").lower() in ("1", "true", "yes"),
        help="Disable SSL/TLS certificate verification for HTTPS (env: PRISM_INSECURE).",
    )
    verbosity = p.add_mutually_exclusive_group()
    verbosity.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print the final result line; errors still go to stderr.",
    )
    verbosity.add_argument(
        "--verbose", "-v", action="store_true", help="Print each step to stdout."
    )
    return p


def _require(args: argparse.Namespace, name: str, env: str) -> str | None:
    val: str | None = getattr(args, name, None)
    if not val:
        print(
            f"error: --{name.replace('_', '-')} is required (or set {env})",
            file=sys.stderr,
        )
        return None
    return val


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # --- Validate required args ------------------------------------------- #
    missing = []
    for attr, env in (
        ("project", "PRISM_PROJECT"),
        ("run_name", "PRISM_RUN_NAME"),
    ):
        if not getattr(args, attr, None):
            missing.append(f"--{attr.replace('_', '-')} (or {env})")
    # Auth: an API token, or an email + password.
    if not args.token and not (args.email and args.password):
        missing.append("--token (or PRISM_TOKEN), or --email + --password")
    if missing:
        print(
            "error: missing required argument(s): " + ", ".join(missing),
            file=sys.stderr,
        )
        return EXIT_BAD_INPUT

    if not args.junit.exists() or not args.junit.is_file():
        print(f"error: JUnit file not found: {args.junit}", file=sys.stderr)
        return EXIT_BAD_INPUT
    if args.archive is not None and (not args.archive.exists() or not args.archive.is_file()):
        print(f"error: archive file not found: {args.archive}", file=sys.stderr)
        return EXIT_BAD_INPUT
    try:
        ci = _metadata_object(args.ci_json)
        hardware = _metadata_object(args.hardware_json)
        archive_bytes = args.archive.read_bytes() if args.archive is not None else None
        if args.pytest_log is not None:
            archive_bytes = _with_transcript(archive_bytes, args.pytest_log.read_bytes())
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"error: invalid metadata or logs — {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    say = (lambda _m: None) if args.quiet else print

    # --- Auth ------------------------------------------------------------- #
    client = PrismClient(args.url, token=args.token, insecure=args.insecure)
    if args.insecure and args.verbose:
        say("→ TLS certificate verification disabled (--insecure)")
    if args.token:
        if args.verbose:
            say(f"→ using API token against {args.url}")
    else:
        if not args.email or not args.password:
            print(
                "error: provide --token (PRISM_TOKEN) or --email/--password "
                "(PRISM_EMAIL/PRISM_PASSWORD).",
                file=sys.stderr,
            )
            return EXIT_BAD_INPUT
        if args.verbose:
            say(f"→ logging in to {args.url} as {args.email}")
        try:
            client.login(args.email, args.password)
        except RuntimeError as exc:
            print(f"error: authentication failed — {exc}", file=sys.stderr)
            return EXIT_AUTH

    # --- Project ---------------------------------------------------------- #
    if args.auto_create_project:
        client.ensure_project(
            args.project, args.project, description="Auto-created by upload_run.py"
        )
    elif not client.project_exists(args.project):
        print(
            f"error: project {args.project!r} not found. "
            "Pass --auto-create-project to create it, or create it in the UI first.",
            file=sys.stderr,
        )
        return EXIT_NO_PROJECT

    # --- Read payloads ---------------------------------------------------- #
    junit_bytes = args.junit.read_bytes()
    if args.measurement:
        try:
            junit_bytes = inject_measurements(junit_bytes, args.measurement)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_BAD_INPUT
        if args.verbose:
            say(f"→ injected {len(args.measurement)} measurement(s) into the JUnit")
    tags = dict(args.tag)

    if args.verbose:
        say(
            f"→ uploading {args.junit.name} ({len(junit_bytes)} bytes) "
            f"as run {args.run_name!r} in project {args.project!r}"
            + (f" with artifacts ({len(archive_bytes or b'')} bytes)" if archive_bytes else "")
        )

    # --- Upload ----------------------------------------------------------- #
    try:
        result = client.upload_run(
            project_slug=args.project,
            run_name=args.run_name,
            junit_xml=junit_bytes,
            archive_zip=archive_bytes,
            tags=tags,
            ci=ci,
            hardware=hardware,
            job_url=args.job_url,
        )
    except RuntimeError as exc:
        print(f"error: upload failed — {exc}", file=sys.stderr)
        return EXIT_UPLOAD

    run_id: str = str(result["id"])
    status: str = str(result.get("status", "pending"))

    # --- Optional wait-for-ingest ---------------------------------------- #
    if args.wait is not None:
        if args.verbose:
            say(f"→ waiting up to {args.wait}s for ingest to finish …")
        deadline = time.monotonic() + args.wait
        while status == "pending":
            if time.monotonic() >= deadline:
                print(
                    f"warning: timed out after {args.wait}s; run {run_id} is still pending",
                    file=sys.stderr,
                )
                # Still print the normal success line so CI can capture the ID.
                print(f"uploaded {args.run_name} (id={run_id}, status=pending)")
                return EXIT_WAIT_TIMEOUT
            time.sleep(2)
            try:
                detail = client.get_run(run_id)
            except RuntimeError as exc:
                print(f"warning: could not poll run status — {exc}", file=sys.stderr)
                break
            status = str(detail.get("status", status))

    print(f"uploaded {args.run_name} (id={run_id}, status={status})")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
