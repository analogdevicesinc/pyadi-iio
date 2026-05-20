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
├── conftest.py             # iio_uri fixture: boot board → ip:URI
├── env/
│   ├── mini2.yaml          # ZCU102 + AD9081 (SD-mux boot)
│   ├── bq.yaml             # ZC706 + ADRV9371 (TFTP boot)
│   └── nemo.yaml           # ZC706 + ADRV9009 (TFTP boot)
├── test_ad9081_smoke.py
├── test_ad9371_smoke.py
└── test_adrv9009_smoke.py
```

## How a test resolves a URI

`conftest.py::iio_uri` (session-scoped) returns an `ip:...` URI by:

1. **`--iio-uri-override <uri>`** or **`IIO_URI_OVERRIDE` env var** — bypass
   labgrid entirely (for laptop runs against a known-good, already-up DUT).
2. **`--uri <uri>`** (pytest-libiio's option) — the hw-matrix CI prologue
   boots the board out-of-band via `boot-and-discover-uri.py` and passes
   the URI through this flag; smoke tests honor it so CI doesn't re-boot.
3. **`LG_ENV` + `LG_COORDINATOR`** — load the env yaml, transition the
   declared Strategy to ``shell`` (booting the board if needed), then
   read the DUT's actual eth0 IP via the serial-console ADIShellDriver.
   The exporter's static `NetworkService.address` is **not** used: DUTs
   DHCP a fresh IP every boot, so the post-boot shell is the source of
   truth.

Whichever path produces the URI, the fixture then polls `iio.Context(uri)`
until a libiio context opens cleanly (up to 60s for labgrid path, 30s for
override paths). eth0 having an IP doesn't mean iiod is ready — userspace
iiod races kernel-module IIO probing for ~5-15s after the shell login. The
wait catches this without spurious first-test failures.

The labgrid path additionally retries once on any bootstrap failure
(serial char drop, JTAG flake, power-controller blip). Retry reconstructs
the labgrid Environment so the Strategy's ``broken`` state resets — a
fresh Strategy walks the full ``powered_off → ... → shell`` chain, which
is effectively a cold cycle.

If no source is set, every test under `test/hw/` fails fast (we
deliberately don't `skip` — a silent green CI run with no HW work is
worse than a red one with a clear message).

## Running locally

```bash
# Without labgrid (point at an iiod yourself; no boot)
pytest -v test/hw/test_ad9081_smoke.py --iio-uri-override ip:10.0.0.211

# Against the lab coordinator (boots the board, ~80–120s).
# You must acquire the place first — the conftest does NOT acquire.
labgrid-client -x 10.0.0.41:20408 -p mini2 acquire
LG_COORDINATOR=10.0.0.41:20408 \
LG_PLACE=mini2 \
LG_ENV=test/hw/env/mini2.yaml \
  pytest -v test/hw/test_ad9081_smoke.py
labgrid-client -x 10.0.0.41:20408 -p mini2 release
```

`adi-labgrid-plugins[kuiper]` must be installed in the active venv for
the local path — the CI workflow's `venv_install_cmd` does this.

## Adding a new board

1. Add an entry to `.github/hw-nodes.json` (place + runner_label + the
   test files to run for that place; `legs: coord` for now).
2. Create `test/hw/env/<place>.yaml` declaring `RemotePlace`, the
   driver stack, and the right boot Strategy for that carrier
   (BootFPGASoC for ZCU102/SD-mux, BootFPGASoCTFTP for ZC706/TFTP,
   BootFabric for VCU118/JTAG). Mirror one of the existing files.
3. Write `test/hw/test_<board>_smoke.py`. Take the `iio_uri` fixture,
   instantiate the right `adi.<class>(uri=iio_uri)`, exercise one or
   two attributes plus a buffer. Don't reuse the heavyweight fixtures
   from `test/conftest.py`.
4. Mark every test function with `@pytest.mark.iio_hardware("<board-tag>")`
   where `<board-tag>` matches the labgrid place's `daughter-board` tag
   (e.g. `ad9081`, `adrv9371`, `adrv9009`). CI's hw-matrix legs run
   `-m iio_hardware --board=<tag>` and deselect unmarked tests; without
   the marker your smoke test will silently never run in CI.

## Running alongside Jenkins

The existing `JenkinsfileHW` is unchanged. Both pipelines run on every
PR for at least 2 weeks; if results diverge, open a tracking issue
before disabling either one.
