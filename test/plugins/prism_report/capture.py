"""Run-level captures: iio_info, dmesg, labgrid console.

Each function returns ``bytes | None`` — None on graceful skip.
"""
from __future__ import annotations

import re
import subprocess
import sys


def _open_iio_context(uri: str):
    import iio  # pylibiio
    return iio.Context(uri)


def _walk_iio_context(uri: str) -> bytes:
    ctx = _open_iio_context(uri)
    lines = [f"# IIO context (library walk) uri={uri}",
             f"# description: {getattr(ctx, 'description', '')}"]
    for k, v in dict(ctx.attrs).items():
        lines.append(f"{k}: {v}")
    for dev in ctx.devices:
        lines.append(f"\nDevice: {dev.name} ({dev.id})")
        for k, v in dict(dev.attrs).items():
            lines.append(f"  {k}: {v.value}")
        for ch in dev.channels:
            lines.append(f"  Channel {ch.id} (output={ch.output})")
            for k, v in dict(ch.attrs).items():
                lines.append(f"    {k}: {v.value}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def capture_iio_info(uri: str, *, timeout_s: float = 15.0) -> bytes | None:
    try:
        proc = subprocess.run(
            ["iio_info", "-u", uri],
            capture_output=True, timeout=timeout_s, check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
        sys.stderr.write(
            f"prism-report: iio_info -u {uri} exited {proc.returncode}; "
            f"falling back to library walk\n"
        )
    except FileNotFoundError:
        sys.stderr.write(
            "prism-report: iio_info binary not found; falling back to library "
            "walk\n"
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write(
            f"prism-report: iio_info timed out after {timeout_s}s; falling "
            f"back to library walk\n"
        )

    try:
        return _walk_iio_context(uri)
    except Exception as exc:  # iio import error, connection refused, etc.
        sys.stderr.write(
            f"prism-report: could not capture iio_info: {exc}\n"
        )
        return None


_TS_RE = re.compile(rb"^\[\s*[\d.]+\]\s*")


def _strip_ts(line: bytes) -> bytes:
    return _TS_RE.sub(b"", line)


def _ssh_dmesg(host: str, user: str, key: str | None,
               timeout_s: float = 15.0) -> bytes | None:
    cmd = ["ssh", "-o", "BatchMode=yes",
           "-o", "StrictHostKeyChecking=accept-new",
           "-o", f"ConnectTimeout={int(timeout_s)}"]
    if key:
        cmd += ["-i", key]
    cmd += [f"{user}@{host}", "dmesg"]
    try:
        proc = subprocess.run(cmd, capture_output=True,
                              timeout=timeout_s, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write(f"prism-report: dmesg via ssh failed: {exc}\n")
        return None
    if proc.returncode != 0:
        sys.stderr.write(
            f"prism-report: dmesg via ssh exited {proc.returncode}: "
            f"{proc.stderr[:200]!r}\n"
        )
        return None
    return proc.stdout


def _console_dmesg(labgrid_session) -> bytes | None:
    if labgrid_session is None:
        return None
    try:
        result = labgrid_session.run_shell_command("dmesg")
    except Exception as exc:
        sys.stderr.write(f"prism-report: dmesg via console failed: {exc}\n")
        return None
    if isinstance(result, str):
        result = result.encode("utf-8", errors="replace")
    return result


def capture_dmesg(*, iio_uri: str, via: str, ssh_user: str,
                  ssh_key: str | None, labgrid_session) -> bytes | None:
    if via == "none":
        return None

    host: str | None = None
    if iio_uri.startswith("ip:"):
        host = iio_uri[3:].split(",")[0]

    methods: list[str] = []
    if via == "ssh":
        methods = ["ssh"]
    elif via == "console":
        methods = ["console"]
    else:  # auto
        if host is not None:
            methods.append("ssh")
        methods.append("console")

    for m in methods:
        if m == "ssh" and host is not None:
            out = _ssh_dmesg(host, ssh_user, ssh_key)
            if out is not None:
                return out
        elif m == "console":
            out = _console_dmesg(labgrid_session)
            if out is not None:
                return out
    return None


def compute_dmesg_diff(pre: bytes, post: bytes) -> bytes:
    pre_set = {_strip_ts(line) for line in pre.splitlines() if line.strip()}
    new_lines: list[bytes] = []
    for line in post.splitlines():
        if not line.strip():
            continue
        if _strip_ts(line) not in pre_set:
            new_lines.append(line)
    return (b"\n".join(new_lines) + b"\n") if new_lines else b""
