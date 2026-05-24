"""Output directory + manifest accumulator.

Layout on disk:
  <out>/
    boot.log, dmesg_pre.log, ... (run-level artifacts)
    cases/
      <safe_test_id>/<filename>
    manifest.json
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")
# ext4/xfs cap a single path component at 255 bytes; some encrypted FS at 143.
# Leave headroom for parametrize ids that explode after sanitization.
_MAX_SAFE_ID_LEN = 200


def _safe_test_id(nodeid: str) -> str:
    sanitized = _UNSAFE.sub("_", nodeid) or "case"
    if len(sanitized) > _MAX_SAFE_ID_LEN:
        digest = hashlib.blake2b(nodeid.encode(), digest_size=4).hexdigest()
        # Reserve room for "_<8 hex chars>" suffix and rebuild.
        head_len = _MAX_SAFE_ID_LEN - len(digest) - 1
        sanitized = sanitized[:head_len] + "_" + digest
    return sanitized


@dataclass
class _CaseEntry:
    case_nodeid: str
    artifacts: list[dict] = field(default_factory=list)


class OutputDir:
    """On-disk layout owner for one prism-report run.

    Single-writer: not thread-safe. Pytest drives writes serially today; if
    a future caller pushes work to a ThreadPoolExecutor, add locking around
    the accumulator dicts/lists before doing so.

    Known v1 limitation: two distinct ``case_nodeid`` values that sanitize
    to the same safe-id (e.g. ``t::x[a/b]`` and ``t::x[a_b]``) and use the
    same ``filename`` will silently overwrite each other on disk. The
    manifest will list both case entries with identical ``rel_path``. In
    practice pytest parametrize ids almost never trip this. Fix when it
    actually shows up: append a short content hash of the nodeid to the
    safe-id directory name.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self._run_artifacts: list[dict] = []
        self._cases: dict[str, _CaseEntry] = {}
        self._initialized = False

    def initialize(self) -> None:
        if self.root.exists():
            children = list(self.root.iterdir())
            if children:
                sys.stderr.write(
                    f"prism-report: refusing to write to non-empty dir "
                    f"{self.root}; pass a fresh path or remove it\n"
                )
                raise SystemExit(4)
        else:
            self.root.mkdir(parents=True)
        (self.root / "cases").mkdir(exist_ok=True)
        self._initialized = True

    def write_run_artifact(self, filename: str, content: bytes, *,
                           kind: str) -> None:
        if not self._initialized:
            raise RuntimeError("OutputDir.initialize() must be called first")
        path = self.root / filename
        path.write_bytes(content)
        self._run_artifacts.append({
            "filename": filename, "kind": kind, "size": len(content),
        })

    def write_case_artifact(self, *, case_nodeid: str, filename: str,
                            content: bytes, kind: str) -> None:
        if not self._initialized:
            raise RuntimeError("OutputDir.initialize() must be called first")
        safe = _safe_test_id(case_nodeid)
        case_dir = self.root / "cases" / safe
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / filename).write_bytes(content)
        entry = self._cases.setdefault(case_nodeid, _CaseEntry(case_nodeid))
        entry.artifacts.append({
            "filename": filename, "kind": kind, "size": len(content),
            "rel_path": f"cases/{safe}/{filename}",
        })

    def finalize(self, *, run_meta: dict) -> dict:
        manifest = {
            "version": 1,
            "run_meta": run_meta,
            "run_artifacts": list(self._run_artifacts),
            "cases": [
                {"case_nodeid": e.case_nodeid, "artifacts": list(e.artifacts)}
                for e in self._cases.values()
            ],
        }
        (self.root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        return manifest
