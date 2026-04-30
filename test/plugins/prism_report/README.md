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
