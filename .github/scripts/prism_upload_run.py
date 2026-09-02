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
import os
import sys
import time
from pathlib import Path

# The shared client lives next to this file; use a path-relative import so the
# script works when invoked from anywhere (e.g. `python3 /repo/scripts/...`).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _prism_client import PrismClient  # noqa: E402  (import after sys.path tweak)

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


def _env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    return v if v else default


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
    p.add_argument(
        "--email", default=_env("PRISM_EMAIL"), help="Login email (env: PRISM_EMAIL)."
    )
    p.add_argument(
        "--password",
        default=_env("PRISM_PASSWORD"),
        help="Login password (env: PRISM_PASSWORD).",
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
        default=None,
        help="Optional .zip of measurement artifacts to upload alongside the JUnit.",
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
        ("email", "PRISM_EMAIL"),
        ("password", "PRISM_PASSWORD"),
        ("project", "PRISM_PROJECT"),
        ("run_name", "PRISM_RUN_NAME"),
    ):
        if not getattr(args, attr, None):
            missing.append(f"--{attr.replace('_', '-')} (or {env})")
    if missing:
        print(
            "error: missing required argument(s): " + ", ".join(missing),
            file=sys.stderr,
        )
        return EXIT_BAD_INPUT

    if not args.junit.exists() or not args.junit.is_file():
        print(f"error: JUnit file not found: {args.junit}", file=sys.stderr)
        return EXIT_BAD_INPUT
    if args.archive is not None and (
        not args.archive.exists() or not args.archive.is_file()
    ):
        print(f"error: archive file not found: {args.archive}", file=sys.stderr)
        return EXIT_BAD_INPUT

    say = (lambda _m: None) if args.quiet else print

    # --- Auth ------------------------------------------------------------- #
    client = PrismClient(args.url)
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
    archive_bytes = args.archive.read_bytes() if args.archive is not None else None
    tags = dict(args.tag)

    if args.verbose:
        say(
            f"→ uploading {args.junit.name} ({len(junit_bytes)} bytes) "
            f"as run {args.run_name!r} in project {args.project!r}"
            + (
                f" with archive {args.archive.name} ({len(archive_bytes or b'')} bytes)"
                if archive_bytes
                else ""
            )
        )

    # --- Upload ----------------------------------------------------------- #
    try:
        result = client.upload_run(
            project_slug=args.project,
            run_name=args.run_name,
            junit_xml=junit_bytes,
            archive_zip=archive_bytes,
            tags=tags,
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
