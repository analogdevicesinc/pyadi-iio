import paramiko
import time
import re
import sys

# ====== CONFIG ======
HOST = "192.168.1.1"
PORT = 22
USERNAME = "root"
PASSWORD = "analog"

THRESHOLD = 85.0          # °C threshold for alert
POLL_INTERVAL = 0.25      # seconds between checks

# Temperature interpretation depends on operating/bias condition (RESET vs RX vs TX).
# Choose which mapping you want to use for conversion:
TEMP_MODE = "rx"          # "reset", "rx", or "tx"

# --- Calibration points (code -> temperature) ---
# Fill these from datasheet Figure 81 for your selected TEMP_MODE.
# Two points are enough to define a line: (code1 at T1), (code2 at T2).
# Example placeholders below are NOT authoritative.
CAL_POINTS = {
    "reset": {"T1": -40.0, "C1": 98.0,   "T2": 85.0, "C2": 190.0},
    "rx":    {"T1": -40.0, "C1": 107.0,   "T2": 85.0, "C2": 202.0},
    "tx":    {"T1": -40.0, "C1": 109.0,   "T2": 85.0, "C2": 206.0},
}

# Read temp0 directly per context instead of dumping "." and grepping
# We'll discover contexts via a shell glob on the target.
LIST_CONTEXTS_CMD = r"ls -1 /sys/bus/iio/devices 2>/dev/null | sed -n 's/^iio:device//p' | head -n 200"
# Fallback context glob (works when iio_attr supports wildcard contexts):
CONTEXT_GLOB = "adar1000_csb*"

# If your iio_attr supports wildcard -c, this is the simplest/cleanest:
# It should output one block per device context (depending on your iio_attr build).
READ_ALL_TEMPS_CMD = f"iio_attr -c '{CONTEXT_GLOB}' temp0 2>/dev/null"
# =====================


def build_line_from_points(mode: str):
    """Return (slope_codes_per_C, offset_code_at_0C) from two (T, code) points."""
    pts = CAL_POINTS.get(mode, None)
    if not pts:
        raise ValueError(f"Unknown TEMP_MODE '{mode}'")

    T1, C1 = float(pts["T1"]), float(pts["C1"])
    T2, C2 = float(pts["T2"]), float(pts["C2"])

    if T2 == T1:
        raise ValueError("Calibration temperatures must be different.")
    if C2 == C1:
        raise ValueError("Calibration codes must be different (otherwise slope is 0).")

    slope = (C2 - C1) / (T2 - T1)      # codes per °C
    offset = C1 - slope * T1           # code at 0°C
    return slope, offset


def adc_code_to_celsius(code: float, mode: str):
    """Convert 8-bit ADC code to °C using a line derived from CAL_POINTS."""
    slope, offset = build_line_from_points(mode)
    return (code - offset) / slope


def parse_iio_attr_output(output: str):
    """
    Parse output of: iio_attr -c 'adar1000_csb*' temp0
    Tries to return dict {context_name: code}.
    Falls back to list of codes if context names aren't visible.
    """
    # Common patterns seen in iio_attr output include context identifiers and "value '...'"
    # We'll try to bind code to the nearest context token.
    results = {}

    # Split into lines and look for context + value on the same line
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        # Try: "... adar1000_csb_0_1_1 ... value '123' ..."
        m = re.search(r"(adar1000_csb[^\s:]*).*value\s+'([0-9]+(?:\.[0-9]+)?)'", line)
        if m:
            ctx = m.group(1)
            code = float(m.group(2))
            results[ctx] = code
            continue

        # Try: "adar1000_csb_0_1_1: temp0 value '123'"
        m = re.search(r"^(adar1000_csb[^\s:]*).*value\s+'([0-9]+(?:\.[0-9]+)?)'", line)
        if m:
            ctx = m.group(1)
            code = float(m.group(2))
            results[ctx] = code
            continue

    if results:
        return results

    # Fallback: just collect all value '###' and return them as an indexed dict
    codes = [float(x) for x in re.findall(r"value\s+'([0-9]+(?:\.[0-9]+)?)'", output)]
    return {f"device_{i+1}": code for i, code in enumerate(codes)}


def get_remote_temp_codes(ssh):
    """Run remote command and return dict of context->raw ADC code."""
    try:
        stdin, stdout, stderr = ssh.exec_command(READ_ALL_TEMPS_CMD)
        output = stdout.read().decode(errors="ignore").strip()
        error = stderr.read().decode(errors="ignore").strip()

        if error and not output:
            print(f"SSH Error: {error}")
            return {}

        if not output:
            print("Warning: empty temp read output.")
            return {}

        return parse_iio_attr_output(output)

    except Exception as e:
        print(f"Error reading temperatures: {e}")
        return {}


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Precompute line parameters once (fails fast if CAL_POINTS not set)
        _ = build_line_from_points(TEMP_MODE)

        print(f"Connecting to {HOST}...")
        ssh.connect(hostname=HOST, port=PORT, username=USERNAME, password=PASSWORD)
        print(f"Connected. Monitoring ADAR1000 temp0 (mode='{TEMP_MODE}', threshold={THRESHOLD:.1f}°C)")

        while True:
            codes_by_dev = get_remote_temp_codes(ssh)

            if not codes_by_dev:
                print("Warning: Could not read temperatures.")
                time.sleep(POLL_INTERVAL)
                continue

            # Sanity check: ADAR1000 ADC is 8-bit -> expect 0..255 codes
            # If outside range, warn that parsing or attribute selection may be wrong.
            bad = {d: c for d, c in codes_by_dev.items() if (c < 0 or c > 255)}
            if bad:
                print("⚠️  Warning: Some readings are not 8-bit ADC codes (expected 0..255).")
                for d, c in bad.items():
                    print(f"    {d}: raw={c}")
                print("    Check iio_attr output/attribute selection; conversion skipped this cycle.")
                time.sleep(POLL_INTERVAL)
                continue

            temps_by_dev = {}
            for dev, code in codes_by_dev.items():
                t_c = adc_code_to_celsius(code, TEMP_MODE)
                temps_by_dev[dev] = t_c

            temps = list(temps_by_dev.values())
            max_temp = max(temps)
            avg_temp = sum(temps) / len(temps)

            # Print a compact status line plus per-device breakdown
            print(f"→ Max: {max_temp:.1f} °C | Avg: {avg_temp:.1f} °C | Devices: {len(temps)}")
            for dev in sorted(temps_by_dev.keys()):
                print(f"    {dev}: code={codes_by_dev[dev]:.0f}  temp={temps_by_dev[dev]:.1f}°C")

            # Datasheet operating max is +85°C, but your threshold can be set independently.
            if max_temp > THRESHOLD:
                print("🔥 ALERT: A device exceeded threshold! 🔥")
                sys.stdout.write('\a')
                sys.stdout.flush()

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except Exception as e:
        print(f"Connection failed or configuration error: {e}")
    finally:
        try:
            ssh.close()
        except Exception:
            pass
        print("SSH connection closed.")


if __name__ == "__main__":
    main()