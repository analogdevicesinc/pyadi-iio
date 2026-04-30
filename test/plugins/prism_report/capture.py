"""Run-level captures: iio_info, dmesg, labgrid console.

Each function returns ``bytes | None`` — None on graceful skip.
"""
from __future__ import annotations

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
