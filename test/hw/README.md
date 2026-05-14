# HW smoke tests (`test/hw/`)

Minimal pyadi-iio tests that run against real boards held by a labgrid
coordinator. Wired into CI by `.github/workflows/hardware-test.yml`,
which calls the shared **discovery-driven** `hw-matrix-v2.yml` reusable
workflow in `tfcollins/labgrid-plugins`.

This suite is **independent** of the historic `test/test_*.py` files
under `test/` (which use the `pytest-libiio` plugin and a host_map). It
exists so the new GH Actions HW pipeline has something to run while the
existing suite stays on Jenkins during the migration.

## How the matrix is built (v2 model)

The reusable workflow doesn't read any per-repo manifest. Instead, on
every run it:

1. Queries the coordinator for live places (each tagged with `carrier`,
   `daughter-board`, `boot-strategy`).
2. Runs `pytest --collect-only -m iio_hardware` against this repo and
   harvests every test's `@pytest.mark.iio_hardware([...])` and optional
   `@pytest.mark.iio_carrier([...])` markers.
3. Builds one matrix shard per (place, daughter-board) intersection —
   per-shard pytest runs `pytest -m "iio_hardware and <daughter>"`.

If a place isn't live, its shard doesn't appear. If we mark a test for
hardware that no live place advertises, the workflow emits a clear
"no overlap right now" annotation instead of failing.

## Layout

```
test/hw/
├── conftest.py             # iio_uri fixture: labgrid place → ip:URI
├── test_ad9081_smoke.py    # @pytest.mark.iio_hardware(["ad9081"])
├── test_ad9371_smoke.py    # @pytest.mark.iio_hardware(["adrv9371", "ad9371"])
└── test_adrv9009_smoke.py  # @pytest.mark.iio_hardware(["adrv9009"])
```

No per-place env yamls. The reusable workflow renders the labgrid env
yaml on the fly from each place's `boot-strategy` tag.

## How a test resolves a URI

`conftest.py::iio_uri` (session-scoped) returns an `ip:...` URI by:

1. **`--iio-uri-override <uri>`** or **`IIO_URI_OVERRIDE` env var** —
   bypass labgrid entirely (for laptop runs against a known-good DUT).
2. **`LG_COORDINATOR` + `LG_PLACE`** — set by the HW workflow before
   pytest starts. Conftest queries the coordinator and extracts the
   place's `NetworkService.address`.

If neither source is set, every test under `test/hw/` is skipped.

## Running locally

```bash
# Without labgrid (point at an iiod yourself)
pytest -v test/hw/test_ad9081_smoke.py --iio-uri-override ip:10.0.0.23

# Against the lab coordinator (acquires + shows the place)
LG_COORDINATOR=10.0.0.41:20408 LG_PLACE=mini2 \
  pytest -v test/hw/test_ad9081_smoke.py
```

## Adding a new board family

1. Write `test/hw/test_<board>_smoke.py`. Take the `iio_uri` fixture,
   instantiate the right `adi.<class>(uri=iio_uri)`, exercise one or
   two attributes plus a buffer.
2. Decorate each test with `@pytest.mark.iio_hardware([<board>])`. Use
   the same name the coordinator's `daughter-board` tag uses (or a list
   that includes aliases).
3. (Optional) Add `@pytest.mark.iio_carrier(["zcu102"])` if the test
   only works on a specific carrier.
4. (Lab admin) Ensure the live coordinator has at least one place
   tagged `daughter-board=<board>` and `boot-strategy=<one of the
   adi_lg_plugins.strategies class names>`.

No workflow edit needed. The discover step picks the new tests up on
the next run.

## Running alongside Jenkins

The existing `JenkinsfileHW` is unchanged. Both pipelines run on every
PR for at least 2 weeks; if results diverge, open a tracking issue
before disabling either one.
