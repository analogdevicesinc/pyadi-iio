# prism_report — pytest plugin

Annotates pyadi-iio test runs with genalyzer-derived spectra and DUT context,
writes them to a local directory and/or uploads to a Prism instance.

See the spec: `docs/superpowers/specs/2026-04-30-pyadi-prism-report-design.md`.

## Quick start (local export)

```bash
pip install -e ".[prism_report]"
pytest --prism-report --prism-out=./reports/run-001 \
       test/test_ad9364_p.py::test_ad9364_sfdr
```

## Quick start (upload to Prism)

```bash
PRISM_URL=http://prism.lab.local:8000 \
PRISM_EMAIL=test-bot@lab \
PRISM_PASSWORD=••• \
pytest --prism-report --prism-project=pluto-bringup \
       --prism-labgrid-place=pluto-bench-1 \
       test/test_ad9364_p.py
```

## Vendored prism client

`_prism_client.py` is a **verbatim copy** of `prism/scripts/_prism_client.py`
at upstream commit `ef5c531ec7afd35cc82aba9075391c940fa0e0d9`.

Re-sync (when prism's API changes):

```bash
# from pyadi-iio repo root
cp ../prism/scripts/_prism_client.py test/plugins/prism_report/_prism_client.py
# Then update the SHA above and run:
pytest test/plugins/prism_report/tests/ -v
```

Do NOT edit the vendored file. If a fix is needed, fix it in prism and re-sync.

## Full flag reference

| Flag | Env | Default |
|---|---|---|
| `--prism-report` | `PRISM_REPORT=1` | off (master switch) |
| `--prism-out` | `PRISM_OUT` | `./prism-report-<utc-ts>/` if no upload |
| `--prism-url` | `PRISM_URL` | unset |
| `--prism-email` | `PRISM_EMAIL` | unset |
| `--prism-password` | `PRISM_PASSWORD` | unset |
| `--prism-project` | `PRISM_PROJECT` | unset (required for upload) |
| `--prism-run-name` | `PRISM_RUN_NAME` | `<host>-<utc-iso>` |
| `--prism-tag k=v` | — | repeatable |
| `--prism-labgrid-place` | `PRISM_LABGRID_PLACE` | unset → labgrid skipped |
| `--prism-no-labgrid` | `PRISM_NO_LABGRID=1` | off |
| `--prism-dmesg-via` | `PRISM_DMESG_VIA` | `auto` (ssh→console) |
| `--prism-dmesg-ssh-user` | `PRISM_DMESG_SSH_USER` | `root` |
| `--prism-dmesg-ssh-key` | `PRISM_DMESG_SSH_KEY` | system default |
| `--prism-fail-on-upload-error` | `PRISM_FAIL_ON_UPLOAD_ERROR=1` | off |

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| `refusing to write to non-empty dir` | Pass a fresh `--prism-out` path or remove the existing one. |
| Spectrum plot has no annotations | `genalyzer` not installed, or `expected_tones` not provided. Plot still emitted; install genalyzer to enable FA. |
| `boot.log` missing | `--prism-labgrid-place` not given, or labgrid coordinator unreachable. Check `labgrid-client places`. |
| `dmesg_pre.log` missing | Both SSH and labgrid-console paths failed. `--prism-dmesg-via=ssh` plus a working SSH key into the DUT is the most reliable path. |
| Upload failed but tests pass | By design — local export is preserved at the printed path. Re-upload manually with prism's `scripts/upload_run.py` from that path, or pass `--prism-fail-on-upload-error` to make pytest non-zero. |

## What gets attached where

| Artifact | Owner |
|---|---|
| `junit.xml` | Run (Prism uses it to create `TestRun` + `TestSuite` + `TestCase` rows) |
| `boot.log`, `dmesg_pre.log`, `dmesg_post.log`, `dmesg_diff.log`, `iio_info.txt`, `run_meta.json` | Run |
| `cases/<safe_id>/spectrum.html`, `iq.npz`, `metrics.json` | Per-case |
