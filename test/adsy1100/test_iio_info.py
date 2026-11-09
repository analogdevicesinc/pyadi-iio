#!/usr/bin/env python3
"""ADSY1100 IIO Info Emulation & Attribute Diagnostic Testing.

This module systematically reads and diagnoses all IIO attributes across an
ADSY1100 target, emulating `iio_info` while isolating breaking attributes
(such as buffer attributes on streaming/sniffer cores or JESD204 debug attributes).

Can be run via pytest:
    pytest -vs test/adsy1100/test_iio_info.py --uri=ip:192.168.2.1 -s
Or directly from CLI:
    python -m test.adsy1100.test_iio_info --uri ip:192.168.2.1 --category all
"""

import argparse
import fnmatch
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import iio
import pytest

DEFAULT_XML_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "emu", "devices", "adsy1100.xml")
)


@dataclass
class ProbeResult:
    """Stores the outcome of probing a single IIO attribute."""

    device_name: str
    device_id: str
    channel_name: Optional[str]
    category: str  # 'context', 'device', 'channel', 'buffer', 'debug', 'trigger'
    attr_name: str
    status: str  # 'OK', 'ERROR', 'SKIPPED', 'CRASH'
    value: Optional[str] = None
    error: Optional[str] = None
    errno: Optional[int] = None
    duration: float = 0.0


class IIOProbeRunner:
    """Manages attribute probing, live logging, health verification, and reporting."""

    def __init__(
        self,
        ctx: iio.Context,
        category: str = "all",
        device_filter: str = "",
        skip_patterns: Optional[List[str]] = None,
        health_check: bool = False,
    ):
        self.ctx = ctx
        self.category = category.lower()
        self.device_filter = device_filter.lower()
        self.skip_patterns = [p.lower() for p in (skip_patterns or [])]
        self.health_check = health_check
        self.results: List[ProbeResult] = []

    def is_device_match(self, dev_name: str) -> bool:
        if not self.device_filter:
            return True
        name = dev_name.lower()
        return fnmatch.fnmatch(name, self.device_filter) or (self.device_filter in name)

    def is_attr_skipped(self, attr_name: str) -> bool:
        name = attr_name.lower()
        for pat in self.skip_patterns:
            if fnmatch.fnmatch(name, pat) or (pat in name):
                return True
        return False

    def is_category_enabled(self, cat: str) -> bool:
        return self.category == "all" or self.category == cat.lower()

    def check_alive(self) -> bool:
        """Lightweight verification that context is still responsive."""
        try:
            _ = self.ctx.description
            return True
        except Exception as e:
            print(f"\n[CRITICAL] Health check FAILED: {e}", flush=True)
            return False

    def probe_single(
        self,
        attr_obj,
        category: str,
        dev_name: str,
        dev_id: str,
        attr_name: str,
        chan_name: Optional[str] = None,
    ) -> ProbeResult:
        """Probe one attribute with pre-logging to pinpoint crashes."""
        chan_str = f", Channel: '{chan_name}'" if chan_name else ""
        target_desc = (
            f"Device: '{dev_name}' ({dev_id}){chan_str} | {category.upper()}: '{attr_name}'"
        )

        if self.is_attr_skipped(attr_name):
            print(f"[PROBE SKIP ] {target_desc} (matches skip pattern)", flush=True)
            res = ProbeResult(
                device_name=dev_name,
                device_id=dev_id,
                channel_name=chan_name,
                category=category,
                attr_name=attr_name,
                status="SKIPPED",
            )
            self.results.append(res)
            return res

        # Pre-log before triggering the IIO read: if target crashes/hangs, this is the last line.
        print(f"[PROBE START] {target_desc} ...", flush=True)

        t0 = time.time()
        val = None
        err_str = None
        err_no = None
        status = "OK"

        try:
            if isinstance(attr_obj, str):
                val = attr_obj
            elif hasattr(attr_obj, "value"):
                val = attr_obj.value
            else:
                val = str(attr_obj)
            duration = time.time() - t0
            val_preview = (str(val)[:60] + "...") if len(str(val)) > 60 else str(val)
            # Replace newlines in preview
            val_preview = val_preview.replace("\n", " ").replace("\r", "")
            print(
                f"[PROBE OK   ] {target_desc} = '{val_preview}' ({duration:.3f}s)",
                flush=True,
            )
        except OSError as e:
            duration = time.time() - t0
            status = "ERROR"
            err_no = e.errno
            err_str = f"[Errno {e.errno}] {e.strerror}"
            print(f"[PROBE ERR  ] {target_desc} -> {err_str} ({duration:.3f}s)", flush=True)
        except Exception as e:
            duration = time.time() - t0
            status = "ERROR"
            err_str = f"{type(e).__name__}: {e}"
            print(f"[PROBE ERR  ] {target_desc} -> {err_str} ({duration:.3f}s)", flush=True)

        res = ProbeResult(
            device_name=dev_name,
            device_id=dev_id,
            channel_name=chan_name,
            category=category,
            attr_name=attr_name,
            status=status,
            value=val,
            error=err_str,
            errno=err_no,
            duration=duration,
        )
        self.results.append(res)

        # Health check to catch delayed crashes or bus hangs immediately
        if self.health_check and not self.check_alive():
            res.status = "CRASH"
            print(
                f"\n[ALARM] TARGET FROZE OR DISCONNECTED AFTER READING: {target_desc}\n",
                flush=True,
            )
            raise ConnectionError(
                f"Target stopped responding after reading {category} attribute '{attr_name}' on '{dev_name}'"
            )

        return res

    def run_sweep(self) -> List[ProbeResult]:
        """Execute full or filtered sweep matching `iio_info` order."""
        print(f"\n{'='*70}")
        print(f"IIO Attribute Diagnostic Sweep (Category: {self.category})")
        print(f"Backend Description: {getattr(self.ctx, 'description', 'N/A')}")
        print(f"{'='*70}\n", flush=True)

        # 1. Context Attributes
        if self.is_category_enabled("context"):
            for attr_name, attr_obj in getattr(self.ctx, "attrs", {}).items():
                self.probe_single(
                    attr_obj=attr_obj,
                    category="context",
                    dev_name="context",
                    dev_id="ctx",
                    attr_name=attr_name,
                )

        # 2. Iterate Devices
        for dev in self.ctx.devices:
            dev_name = dev.name or dev.id
            if not self.is_device_match(dev_name):
                continue

            # Channels & Channel Attributes
            if self.is_category_enabled("channel"):
                for chan in dev.channels:
                    chan_label = chan.name or chan.id
                    for attr_name, attr_obj in chan.attrs.items():
                        self.probe_single(
                            attr_obj=attr_obj,
                            category="channel",
                            dev_name=dev_name,
                            dev_id=dev.id,
                            attr_name=attr_name,
                            chan_name=chan_label,
                        )

            # Device Attributes
            if self.is_category_enabled("device"):
                for attr_name, attr_obj in dev.attrs.items():
                    self.probe_single(
                        attr_obj=attr_obj,
                        category="device",
                        dev_name=dev_name,
                        dev_id=dev.id,
                        attr_name=attr_name,
                    )

            # Buffer Attributes (e.g. streaming / sniffer)
            if self.is_category_enabled("buffer"):
                for attr_name, attr_obj in dev.buffer_attrs.items():
                    self.probe_single(
                        attr_obj=attr_obj,
                        category="buffer",
                        dev_name=dev_name,
                        dev_id=dev.id,
                        attr_name=attr_name,
                    )

            # Debug Attributes (e.g. JESD204 / direct_reg_access)
            if self.is_category_enabled("debug"):
                for attr_name, attr_obj in dev.debug_attrs.items():
                    self.probe_single(
                        attr_obj=attr_obj,
                        category="debug",
                        dev_name=dev_name,
                        dev_id=dev.id,
                        attr_name=attr_name,
                    )

        return self.results

    def print_summary(self):
        """Print a structured breakdown of tested attributes and outcomes."""
        total = len(self.results)
        ok_count = sum(1 for r in self.results if r.status == "OK")
        err_count = sum(1 for r in self.results if r.status == "ERROR")
        skip_count = sum(1 for r in self.results if r.status == "SKIPPED")
        crash_count = sum(1 for r in self.results if r.status == "CRASH")

        print(f"\n{'-'*70}")
        print("DIAGNOSTIC SUMMARY REPORT")
        print(f"{'-'*70}")
        print(f"Total attributes probed : {total}")
        print(f"  Passed (OK)           : {ok_count}")
        print(f"  Handled Errors (ERR)  : {err_count}")
        print(f"  Skipped (SKIP)        : {skip_count}")
        print(f"  Target Crashes (CRASH): {crash_count}")
        print(f"{'-'*70}")

        # Breakdown by category
        categories = ["context", "device", "channel", "buffer", "debug"]
        for cat in categories:
            cat_results = [r for r in self.results if r.category == cat]
            if cat_results:
                c_ok = sum(1 for r in cat_results if r.status == "OK")
                c_err = sum(1 for r in cat_results if r.status == "ERROR")
                c_skip = sum(1 for r in cat_results if r.status == "SKIPPED")
                print(f"  {cat.capitalize():<8}: Total={len(cat_results):<3} | OK={c_ok:<3} | ERR={c_err:<3} | SKIP={c_skip:<3}")

        # List failing attributes grouped by device
        if err_count > 0:
            print(f"\n{'-'*70}")
            print("ERROR DETAILS (Attributes returning errno / exceptions):")
            print(f"{'-'*70}")
            for r in self.results:
                if r.status in ("ERROR", "CRASH"):
                    chan = f" [{r.channel_name}]" if r.channel_name else ""
                    print(
                        f"  [{r.status}] {r.device_name}{chan} -> ({r.category}) {r.attr_name}: {r.error}"
                    )
        print(f"{'-'*70}\n", flush=True)


# ==============================================================================
# Pytest Test Suite
# ==============================================================================

def _make_runner(iio_context, iio_filter_config, forced_category=None) -> IIOProbeRunner:
    cat = forced_category if forced_category else iio_filter_config["category"]
    return IIOProbeRunner(
        ctx=iio_context,
        category=cat,
        device_filter=iio_filter_config["dev_filter"],
        skip_patterns=iio_filter_config["skip_patterns"],
        health_check=iio_filter_config["health_check"],
    )


def test_iio_context_attributes(iio_context, iio_filter_config):
    """Test reading context attributes safely."""
    runner = _make_runner(iio_context, iio_filter_config, forced_category="context")
    results = runner.run_sweep()
    runner.print_summary()
    assert not any(r.status == "CRASH" for r in results), "Context attribute reading crashed target!"


def test_iio_device_attributes(iio_context, iio_filter_config):
    """Test reading device attributes across devices."""
    runner = _make_runner(iio_context, iio_filter_config, forced_category="device")
    results = runner.run_sweep()
    runner.print_summary()
    assert not any(r.status == "CRASH" for r in results), "Device attribute reading crashed target!"


def test_iio_channel_attributes(iio_context, iio_filter_config):
    """Test reading channel attributes across all channels."""
    runner = _make_runner(iio_context, iio_filter_config, forced_category="channel")
    results = runner.run_sweep()
    runner.print_summary()
    assert not any(r.status == "CRASH" for r in results), "Channel attribute reading crashed target!"


def test_iio_buffer_attributes(iio_context, iio_filter_config):
    """Test reading buffer-specific attributes (isolates fftsniffer / DMA buffer issues)."""
    runner = _make_runner(iio_context, iio_filter_config, forced_category="buffer")
    results = runner.run_sweep()
    runner.print_summary()
    assert not any(r.status == "CRASH" for r in results), "Buffer attribute reading crashed target!"


def test_iio_debug_attributes(iio_context, iio_filter_config):
    """Test reading debug attributes (isolates JESD204 / register access issues)."""
    runner = _make_runner(iio_context, iio_filter_config, forced_category="debug")
    results = runner.run_sweep()
    runner.print_summary()
    assert not any(r.status == "CRASH" for r in results), "Debug attribute reading crashed target!"


def test_iio_info_full_emulation(iio_context, iio_filter_config):
    """Emulate full iio_info attribute traversal and verify board stability."""
    runner = _make_runner(iio_context, iio_filter_config, forced_category="all")
    results = runner.run_sweep()
    runner.print_summary()
    assert not any(r.status == "CRASH" for r in results), "iio_info emulation crashed target!"


# ==============================================================================
# Standalone CLI Entrypoint
# ==============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Probe and diagnose IIO attributes on ADSY1100 (emulating iio_info)"
    )
    parser.add_argument(
        "--uri",
        default=os.environ.get("IIO_URI_OVERRIDE", ""),
        help="Target IIO URI (e.g. ip:192.168.2.1, xml:path/to/adsy1100.xml)",
    )
    parser.add_argument(
        "--category",
        "-c",
        default="all",
        choices=["all", "context", "device", "channel", "buffer", "debug"],
        help="Attribute category to probe (default: all)",
    )
    parser.add_argument(
        "--device",
        "-d",
        default="",
        help="Device filter pattern (e.g. *sniffer* or axi-ad9084*)",
    )
    parser.add_argument(
        "--skip",
        "-s",
        default="",
        help="Comma-separated attribute names or patterns to skip",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Probe board health after each attribute read",
    )

    args = parser.parse_args()

    target_uri = args.uri
    if not target_uri:
        if os.path.exists(DEFAULT_XML_PATH):
            target_uri = f"xml:{DEFAULT_XML_PATH}"
            print(f"[INFO] No URI supplied. Defaulting to mock XML: {target_uri}")
        else:
            print("[ERROR] Please provide --uri (e.g. --uri ip:192.168.2.1)", file=sys.stderr)
            sys.exit(1)

    print(f"Connecting to IIO Context: {target_uri} ...")
    if target_uri.startswith("xml:"):
        ctx = iio.XMLContext(target_uri[4:])
    else:
        ctx = iio.Context(target_uri)

    skip_list = [p.strip() for p in args.skip.split(",") if p.strip()]
    runner = IIOProbeRunner(
        ctx=ctx,
        category=args.category,
        device_filter=args.device,
        skip_patterns=skip_list,
        health_check=args.health_check,
    )

    try:
        runner.run_sweep()
        runner.print_summary()
    except KeyboardInterrupt:
        print("\n[ABORTED] Sweep interrupted by user.", flush=True)
        runner.print_summary()
        sys.exit(130)
    except Exception as e:
        print(f"\n[EXCEPTION] Fatal error during sweep: {e}", flush=True)
        runner.print_summary()
        sys.exit(1)
