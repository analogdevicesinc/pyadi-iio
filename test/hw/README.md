# HW smoke tests (`test/hw/`)

Minimal pyadi-iio tests that run against real boards held by a labgrid
coordinator. Wired into CI by `.github/workflows/hardware-test.yml`,
which calls the shared `hw-matrix` reusable workflow in
`tfcollins/labgrid-plugins`.

This suite is **independent** of the historic `test/test_*.py` files
under `test/` (which use the `pytest-libiio` plugin and a host_map). It
exists so the new GH Actions HW pipeline has something to run while the
existing suite stays on Jenkins during the migration.

## Layout

```
test/hw/
├── conftest.py            # iio_uri fixture: labgrid place → ip:URI
├── env/
│   ├── pluto.yaml         # coord-mode env for the 'pluto' place
│   └── fmcomms2_zcu102.yaml
├── test_pluto_smoke.py    # smoke for adi.Pluto
└── test_ad9361_smoke.py   # smoke for adi.ad9361 (FMComms2/3 carrier)
```

## How a test resolves a URI

`conftest.py::iio_uri` (session-scoped) returns an `ip:...` URI by:

1. **`--iio-uri-override <uri>`** or **`IIO_URI_OVERRIDE` env var** — bypass
   labgrid entirely (for laptop runs against a known-good DUT).
2. **`LG_COORDINATOR` + `LG_PLACE`** — set by the HW workflow. The
   workflow's acquire-place composite has already acquired the place
   before pytest starts; conftest runs `labgrid-client show` and parses
   the first `address:` / `host:` / `ipaddr:` line under the held
   `NetworkService` resource.

If neither source is set, every test under `test/hw/` is skipped.

## Running locally

```bash
# Without labgrid (point at an iiod yourself)
pytest -v test/hw/test_pluto_smoke.py --iio-uri-override ip:192.168.2.1

# Against the lab coordinator
LG_COORDINATOR=10.0.0.41:20408 LG_PLACE=pluto \
  pytest -v test/hw/test_pluto_smoke.py
```

## Adding a new board

1. Add an entry to `.github/hw-nodes.json` (place + runner_label + the
   test files to run for that place; `legs: coord` for now).
2. Create `test/hw/env/<place>.yaml` mirroring the structure of the
   existing files — only the `RemotePlace.name` needs to change.
3. Write `test/hw/test_<board>_smoke.py`. Take the `iio_uri` fixture,
   instantiate the right `adi.<class>(uri=iio_uri)`, exercise one or
   two attributes plus a buffer. Don't reuse the heavyweight fixtures
   from `test/conftest.py`.

## Running alongside Jenkins

The existing `JenkinsfileHW` is unchanged. Both pipelines run on every
PR for at least 2 weeks; if results diverge, open a tracking issue
before disabling either one.
