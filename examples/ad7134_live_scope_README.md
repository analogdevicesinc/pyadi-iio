# ad7134_live_scope.py

Live display of the raw data from all 8 channels of a dual AD7134, with a
continuous device-to-device phase readout, for a run length you choose.

Its main job is to answer one question: **does issuing the multidevice sync
bring the two dies inside the +/-10 ns device-to-device spec, and do they stay
there?** It does that by capturing for N minutes unsynced, issuing one
`DIG_IF_RESET` broadcast, capturing for another N minutes, and comparing.


## 1. Prerequisites

Copy **both** of these into the same directory - the scope imports its DSP from
the drift monitor:

```
ad7134_live_scope.py
ad7134_drift_monitor.py
```

Optional, for replaying saved files offline:

```
ad7134_phase_from_csv.py
```

You need `numpy`, `matplotlib` and `pylibiio`, and **a display**. The script
runs on your PC and reaches the board over the network, so either run it
locally or use `ssh -X` / `ssh -Y`. If no interactive backend is available it
exits at startup with a clear message rather than drawing to nothing.

### Signal generator

Drive all 8 inputs from a **20 kHz** sine.

Do not use 250 kHz. The phase measurement is a cross-correlation, so it is only
unambiguous over half an alias period, `P = ODR / f_tone`. At 20 kHz and
1.4 MSPS, `P` is 65 samples - plenty of room. At 250 kHz it is 5.2 samples,
which makes the `lag` column meaningless and wraps `cross` every 4 us.


## 2. Check the board is reachable

```bash
iio_info -u ip:<board-ip>
```

You should see both `adc_0` and `adc_1`. Substitute your own board address for
`<board-ip>` everywhere below.


## 3. The command

```bash
cd pyadi-iio/examples

python3 ad7134_live_scope.py ip:<board-ip> \
        --odr 1400000 \
        --sync-compare \
        --minutes 5
```

That is the whole thing. Everything else has a sensible default.

- 5 minutes unsynced, one `DIG_IF_RESET` broadcast, 5 minutes synced
- **the die-to-die phase logged continuously for both phases**, ~6400 rows each
  at 1.4 MSPS (one row per buffer - see section 5 for the arithmetic)
- **one buffer of raw counts saved immediately before the sync, and one
  immediately after it** - 65536 samples, 4.3 MB each
- total run ~10 min, ~10 MB on disk

The run makes its own folder in whatever directory you launched from, and
prints the path on the first line:

```
saving to /home/you/pyadi-iio/examples/ad7134_20260903_115337/

ad7134_20260903_115337/
    before_sync_phase.csv
    before_sync_raw.csv
    after_sync_phase.csv
    after_sync_raw.csv
```

Two runs never mix, and there is no filename to choose. Add `--outdir
/path/to/somewhere` if you want the folder created somewhere other than the
current directory.

`--odr 1400000` is the rate that validated at 10/10 pass, +7.9 ns. The ODR
sweep is periodic rather than monotonic, so do not assume a nearby rate behaves
the same.

`--window` is the buffer size, and it sets the length of the raw files too - one
buffer either side of the sync. 65536 samples is the default and gives 4.3 MB
per file; `--window 262144` gives 17.6 MB. Nothing else runs during a dump, so
each file is contiguous with no gaps inside it.


## 4. The display

```
+--------------------------------------------------+
|  ch0..ch7 raw counts, ~3 tone cycles              |  blue = die A (ch0-3)
|                                                   |  red  = die B (ch4-7)
+--------------------------------------------------+
|  cross delay vs t, +/-10 ns spec band shaded      |  continuous across
|  red dashed line marks the sync                   |  both phases
+--------------------------------------------------+
 [AFTER]  t  31.0 s  ODR 1.2973 MSPS  tone 20000.3 Hz  SNR 64.1 dB  frames 129
 cross (die B - die A)  +8.0 ns   spread 0.0 ns   lag +0 samples
 per-ch vs ch0:  +0.0  +0.0  -0.0  -0.0  |  +8.0  +8.0  +8.0  +8.0
```

Before the sync the red traces are visibly offset from the blue ones and the
history strip sits above the green spec band. After the sync the traces overlay
and the strip drops into the band.

### Keys

| key | action |
|---|---|
| `s` | save a raw grab right now |
| `p` | pause / unpause the display (capture pauses too) |
| `q` | quit early - the phase is closed cleanly and still summarised |


## 5. Output files

Everything lands in one folder per run, `ad7134_<timestamp>/`, named
`<when>_sync_<what>.csv` so the four files sort into two obvious pairs:

| file | content |
|---|---|
| `before_sync_phase.csv` | **die-to-die phase vs time, whole unsynced phase** |
| `after_sync_phase.csv`  | **die-to-die phase vs time, whole synced phase** |
| `before_sync_raw.csv` | raw counts, the last buffer before the sync |
| `after_sync_raw.csv`  | raw counts, the first buffer after the sync |
| `before_sync_raw_NNN.csv` | extra raw, only if you use `--grab-every` or `s` |

`_phase` is the continuous record, one row per refill, covering every moment of
the run. `_raw` is the waveform evidence at the sync instant: one `--window`
buffer either side of the `DIG_IF_RESET` with nothing running in between, so the
two can be diffed directly.

How many rows to expect in a `_phase.csv`:

```
rows = ODR / --window x --minutes x 60

1.3 MSPS, 65536, 5 min  ->  19.8 rows/s x 300 s  =  ~5950
1.4 MSPS, 65536, 5 min  ->  21.4 rows/s x 300 s  =  ~6400
```

That is the acquisition-limited ceiling and there is headroom to reach it -
processing costs ~27 ms per frame against a ~50 ms buffer. A materially lower
count means the network could not keep up; see section 11. The `t_s` column is
wall-clock seconds from the start of the phase, so the real rate is visible in
the file itself.

Single-phase mode has no sync boundary, so it writes only `run_phase.csv`.

`_phase.csv` columns:

```
t_s,cross_ns,intra_die_spread_ns,coarse_lag,tone_hz,snr_db,ch0_ns,...,ch7_ns
0.000,7.9994,0.0266,0,20000.298,64.12,0.0000,0.0034,...,8.0096
```

This file is flushed to disk every 2 s while the run is in progress, so an
interrupted run still leaves usable data.

Every `_raw` file is eight columns of signed integer counts, one row per sample,
no header, `--window` rows long. This is the same layout iio-oscilloscope
exports, so existing tooling reads it directly:

```
-2441447,-2438507,-2441179,-2440649,-2446806,-2446192,-2444038,-2446271
```


## 6. Reading the result

At the end you get a per-phase summary and a comparison:

```
  metric                        before         after        change
  --------------------------------------------------------------
  cross mean (ns)               778.99          8.00       -770.99
  cross std (ns)                  0.01          0.01         +0.00
  cross span (ns)                 0.04          0.04         -0.00
  intra-die spread (ns)           0.03          0.03         -0.00
  coarse lag range              -1..-1        +0..+0
  --------------------------------------------------------------

  sync moved the mean offset +778.99 -> +8.00 ns (-770.99 ns)
  before: OUTSIDE spec        after: WITHIN spec
```

What to look for after the sync:

- **cross mean** inside +/-10 ns
- **intra-die spread** around 1.5 ns - this is the four channels within one die,
  and it should be small whatever the two dies are doing relative to each other
- **coarse lag** constant for the whole phase

A `coarse_lag` that changes value part-way through a run is a whole-ODR-period
frame slip, not a fine phase error. The two are separate failure modes: the
fine error moves `cross` by tens of ns, a slip moves it by ~729 ns at once.
That is why the summary reports the lag range and not just its mean.

Each phase also reports why it ended:

```
  ended         : reached the full 5 min
  ended         : CUT SHORT at 4.7 s - 'q' pressed
  ended         : CUT SHORT at 4.7 s - plot window was closed
```

If a phase was cut short its numbers cover less time than the other one, and
the comparison table says so. If the *first* phase is cut short, no sync is
issued and the second phase is skipped, so you never get a comparison built on
unequal runs.


## 7. Variants

A longer raw record either side of the sync - 262144 samples, 17.6 MB per file:

```bash
python3 ad7134_live_scope.py ip:<board-ip> --odr 1400000 --sync-compare \
        --minutes 10 --window 262144
```

Also dump raw periodically *during* each phase, on top of the two around the
sync - here one buffer every 60 s:

```bash
python3 ad7134_live_scope.py ip:<board-ip> --odr 1400000 --sync-compare \
        --minutes 10 --grab-every 60
```

One long synced run, no before/after comparison. There is no sync boundary in
this mode, so no raw is written unless you press `s`:

```bash
python3 ad7134_live_scope.py ip:<board-ip> --odr 1400000 --sync --minutes 10
```

Try the display with no hardware at all - synthesises 8 channels with a known
inter-die delay, so you can check the window, the keys and the file output
before going near the bench:

```bash
python3 ad7134_live_scope.py --demo --sync-compare --minutes 0.5 \
        --demo-delay-ns 779 --demo-delay-after-ns 8
```

It fakes a 779 ns offset before the sync and 8 ns after, so you can see what a
successful sync looks like on the display, and it writes the two 4.3 MB
`_sync_raw.csv` files so you can practise the replay step below on them.


## 8. Replaying a saved grab

```bash
cd ad7134_20260903_115337

python3 ../ad7134_phase_from_csv.py before_sync_raw.csv 1400000
python3 ../ad7134_phase_from_csv.py after_sync_raw.csv  1400000
```

Run it on both files and you get the offline confirmation of the whole test:
the first should report roughly the pre-sync offset, the second something
inside +/-10 ns.

The sample rate is a **positional** argument, not a flag. This is a completely
independent code path from the live measurement, so it is a genuine check on
the live numbers rather than a restatement of them.


## 9. Options

```
  --minutes N        duration of EACH capture phase (default 5)
  --sync-compare     run --minutes, sync once, run --minutes again
  --sync             single-phase mode: sync once before starting
  --odr HZ           set sampling_frequency before the run
  --interval S       seconds between printed delay rows (default 10)
  --grab-every S     also dump raw every S seconds during a phase;
                     0 (default) = only around the sync and on the 's' key
  --outdir DIR       parent of the per-run ad7134_<stamp>/ folder
                     (default: the current directory)
  --window N         buffer size in samples: the refill size AND the length
                     of every raw dump (default 65536 = 4.3 MB per dump)
  --fps N            display refresh cap (default 5)
  --cycles N         tone cycles shown in the trace panel (default 3)
  --crc              24-bit+CRC decode (shift=8)
  --min-snr DB       freeze the phase readout below this SNR (default 30)
  --demo             synthetic source, no hardware
```

`--window` is the one knob for how much raw you get. Keep it a power of two:
65536 makes the per-frame FFTs about 3x faster than the 65534 the other scripts
in this family use. The DMA caps a transfer at 16 MB = 524288 samples. Raising
it gives longer raw files but fewer refills per second, so the history strip and
the `_phase.csv` get coarser - 65536 is the right default unless you specifically
need a longer record either side of the sync.


## 10. Things that are expected, not faults

**Each raw dump pauses the display** while the file is written - about 0.2 s
for the default 65536 samples, 0.6 s for 262144. The script prints the pause
duration at startup. The samples inside one file are still contiguous; the gap
is around the dump, not inside it.

**The disk budget is checked before the run starts.** If the dumps will not
fit, it refuses to start rather than hitting ENOSPC nine minutes in. Lower
`--window`, raise `--grab-every`, or pick another `--outdir`.

**A "sampling_frequency" KeyError does not happen here.** Older kernels expose
that attribute on the channels rather than the device; this script checks both.


## 11. Network throughput

The script runs on your PC and streams over libiio, so a 1.4 MSPS 8-channel
capture needs **about 358 Mbit/s sustained** (1.4e6 x 8 ch x 4 B = 44.8 MB/s).

Please check this before committing to a 10-minute run:

```bash
iperf3 -c <board-ip>
```

This is the one number that could not be verified here, because no board was
reachable from the development machine.

If the link cannot keep up, the per-buffer delay measurements stay valid - each
one is self-contained within a single refill - but the refill rate drops, so
there is more wall-clock time between the last unsynced buffer and the first
synced one. Each raw file is exactly one refill, so it cannot be torn by a slow
link whatever you set `--window` to.


## 12. If something looks wrong

| symptom | likely cause |
|---|---|
| `lag` jumps around, `cross` wraps | generator at 250 kHz - use 20 kHz |
| phase readout freezes | SNR below `--min-snr`; check the generator is on and all 8 inputs are driven |
| `NOTE: no tone on channel(s) [...]` | those inputs are not driven; the script falls back from the per-die 4-channel average to a single ch4-ch0 pair |
| `cross` far outside spec after sync | check `iio_reg adc_0 0x15` reads `0x01` (master PLL locked) |
| refill rate much below 20/s | network throughput - see section 11 |
