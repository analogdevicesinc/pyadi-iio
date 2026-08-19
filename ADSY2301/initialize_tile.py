"""
Standalone script to initialize an ADAR1000-based BFC tile and optionally
configure individual Rx/Tx channels.  Works for both:
  - single tile  (4 chips  / 16 elements, channels 1-16)
  - quad   tile  (16 chips / 64 elements, channels 1-64)

---- Init-only (all bias defaults) ----------------------------------------
  python initialize_tile.py --mode single --ip 192.168.2.1
  python initialize_tile.py --mode quad   --ip 192.168.2.1

---- Init with custom bias values ------------------------------------------
  python initialize_tile.py --mode quad --ip 192.168.2.1 \
      --pa-off -4.8 --pa-on -4.8 --lna-off -4.8 --lna-on -4.8

---- Configure Rx on channels 1, 3 and 5 -----------------------------------
  python initialize_tile.py --mode single --ip 192.168.2.1 \
      --rx-channels 1 3 5 \
      --rx-gain 127 --rx-attenuation 0 --rx-phase 45.0 \
      --lna-bias -1.0 --rx-enable

---- Configure Tx on channels 2 and 4 -------------------------------------
  python initialize_tile.py --mode single --ip 192.168.2.1 \
      --tx-channels 2 4 \
      --tx-gain 127 --tx-attenuation 0 --tx-phase 90.0 \
      --pa-bias -2.0 --tx-enable --external-tr

---- Apply the same Rx AND Tx settings to every channel --------------------
  python initialize_tile.py --mode quad --ip 192.168.2.1 \
      --rx-channels all --rx-gain 100 --rx-phase 0.0 --rx-enable \
      --tx-channels all --tx-gain 100 --tx-phase 0.0 --tx-enable
"""

import argparse
import sys
import adi


# ---------------------------------------------------------------------------
# Default chip IDs
# ---------------------------------------------------------------------------

# SINGLE_TILE_DEFAULT_CHIP_IDS = [
#     "adar1000_csb_0_1_1",
#     "adar1000_csb_0_1_2",
#     "adar1000_csb_0_1_3",
#     "adar1000_csb_0_1_4",
# ]
SINGLE_TILE_DEFAULT_CHIP_IDS = [
    "adar1000_csb_0_1_1",
    "adar1000_csb_0_1_2",
    "adar1000_csb_0_1_3",
    "adar1000_csb_0_1_4",
]

QUAD_TILE_DEFAULT_CHIP_IDS = [
    "adar1000_csb_0_1_1", "adar1000_csb_0_1_2", "adar1000_csb_0_1_3", "adar1000_csb_0_1_4",
    "adar1000_csb_0_2_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
    "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
    "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4",
]

# Total element counts per tile type
ELEMENT_COUNT = {"single": 16, "quad": 64}


# ---------------------------------------------------------------------------
# Connect helpers
# ---------------------------------------------------------------------------

def connect_single_tile(ip: str, chip_ids: list) -> adi.adar1000_array:
    """Connect to a single BFC tile (4 chips, 16 elements)."""
    if len(chip_ids) != 4:
        raise ValueError(f"Single tile requires exactly 4 chip IDs, got {len(chip_ids)}.")

    dev = adi.adar1000_array(
        f"ip:{ip}",
        chip_ids=chip_ids,
        device_map=[
            [2, 1],
            [3, 4],
        ],
        element_map=[
            [1,  2,  5,  6],
            [3,  4,  7,  8],
            [9,  10, 13, 14],
            [11, 12, 15, 16],
        ],
        device_element_map={
            1: [6, 8, 7, 5],
            2: [2, 4, 3, 1],
            3: [11, 9, 10, 12],
            4: [15, 13, 14, 16],
        },
    )
    print(f"[INFO] Single tile connected  (ip:{ip})")
    return dev


def connect_quad_tile(ip: str, chip_ids: list) -> adi.adar1000_array:
    """Connect to a quad BFC tile (16 chips, 64 elements)."""
    if len(chip_ids) != 16:
        raise ValueError(f"Quad tile requires exactly 16 chip IDs, got {len(chip_ids)}.")

    dev = adi.adar1000_array(
        f"ip:{ip}",
        chip_ids=chip_ids,
        device_map=[
            [2,  1,  6,  5],
            [3,  4,  7,  8],
            [10, 9,  14, 13],
            [11, 12, 15, 16],
        ],
        element_map=[
            [1,  9,  17, 25, 33, 41, 49, 57],
            [2,  10, 18, 26, 34, 42, 50, 58],
            [3,  11, 19, 27, 35, 43, 51, 59],
            [4,  12, 20, 28, 36, 44, 52, 60],
            [5,  13, 21, 29, 37, 45, 53, 61],
            [6,  14, 22, 30, 38, 46, 54, 62],
            [7,  15, 23, 31, 39, 47, 55, 63],
            [8,  16, 24, 32, 40, 48, 56, 64],
        ],
        device_element_map={
            1:  [25, 17, 18, 26],
            2:  [2,  10, 9,  1],
            3:  [4,  12, 11, 3],
            4:  [27, 19, 20, 28],
            5:  [57, 49, 50, 58],
            6:  [34, 42, 41, 33],
            7:  [36, 44, 43, 35],
            8:  [59, 51, 52, 60],
            9:  [29, 21, 22, 30],
            10: [6,  14, 13, 5],
            11: [8,  16, 15, 7],
            12: [31, 23, 24, 32],
            13: [61, 53, 54, 62],
            14: [38, 46, 45, 37],
            15: [40, 48, 47, 39],
            16: [63, 55, 56, 64],
        },
    )
    print(f"[INFO] Quad tile connected  (ip:{ip})")
    return dev


# ---------------------------------------------------------------------------
# Initialize  (identical logic for both tile types)
# ---------------------------------------------------------------------------

def initialize(dev: adi.adar1000_array,
               pa_off: float,
               pa_on: float,
               lna_off: float,
               lna_on: float) -> None:
    """Mirror the Initialize() method from BFC_Tile / Quad_BFC_Tile."""
    dev.initialize_devices(pa_off, pa_on, lna_off, lna_on)

    for device in dev.devices.values():
        device.mode = "rx"
        device.bias_dac_mode = "on"
        for channel in device.channels:
            channel.rx_enable = True

    print("[INFO] Initialization complete.")


# ---------------------------------------------------------------------------
# Per-channel Rx configuration
# ---------------------------------------------------------------------------

def configure_rx_channels(dev: adi.adar1000_array,
                           channels: list,
                           gain: int,
                           attenuation: bool,
                           phase: float,
                           lna_bias: float,
                           enable: bool) -> None:
    """
    Apply Rx settings to each requested element index then latch.

    Parameters
    ----------
    channels    : list of 1-based element indices to configure
    gain        : rx_gain value  (0-127)
    attenuation : rx_attenuator  (True = attenuator in, False = out)
    phase       : rx_phase in degrees
    lna_bias    : per-device LNA bias voltage (V) applied to the owning device
    enable      : rx_enable flag
    """
    for ch in channels:
        element = dev.elements[ch]
        element.rx_gain       = gain
        element.rx_attenuator = attenuation
        element.rx_phase      = phase
        element.rx_enable     = enable
        print(f"[INFO]   Rx ch {ch:3d} | gain={gain}  atten={attenuation}  "
              f"phase={phase}°  enable={enable}")

    # Apply LNA bias to every device that owns at least one configured channel
    if lna_bias is not None:
        configured_elements = {dev.elements[ch] for ch in channels}
        for device in dev.devices.values():
            if any(ch in configured_elements for ch in device.channels):
                device.lna_bias_on = lna_bias

    for device in dev.devices.values():
        device.latch_rx_settings()
    print(f"[INFO] Rx settings latched for {len(channels)} channel(s).")


# ---------------------------------------------------------------------------
# Per-channel Tx configuration
# ---------------------------------------------------------------------------

def configure_tx_channels(dev: adi.adar1000_array,
                           channels: list,
                           gain: int,
                           attenuation: bool,
                           phase: float,
                           pa_bias: float,
                           enable: bool,
                           external_tr: bool) -> None:
    """
    Apply Tx settings to each requested element index then latch.

    Parameters
    ----------
    channels    : list of 1-based element indices to configure
    gain        : tx_gain value  (0-127)
    attenuation : tx_attenuator  (True = attenuator in, False = out)
    phase       : tx_phase in degrees
    pa_bias     : per-element PA bias voltage (V)
    enable      : tx_enable flag
    external_tr : True  -> tr_source="external", bias_dac_mode="toggle"
                  False -> tr_source="spi",      bias_dac_mode="on"
    """
    for ch in channels:
        element = dev.elements[ch]
        element.tx_gain       = gain
        element.tx_attenuator = attenuation
        element.tx_phase      = phase
        element.tx_enable     = enable
        if pa_bias is not None:
            element.pa_bias_on = pa_bias
        print(f"[INFO]   Tx ch {ch:3d} | gain={gain}  atten={attenuation}  "
              f"phase={phase}°  enable={enable}  pa_bias={pa_bias}")

    # TR source is a per-device setting; update every device that owns a
    # configured channel
    if channels:
        configured_elements = {dev.elements[ch] for ch in channels}
        for device in dev.devices.values():
            if any(ch in configured_elements for ch in device.channels):
                if external_tr:
                    device.tr_source      = "external"
                    device.bias_dac_mode  = "toggle"
                else:
                    device.tr_source      = "spi"
                    device.bias_dac_mode  = "on"

    for device in dev.devices.values():
        device.latch_tx_settings()
    print(f"[INFO] Tx settings latched for {len(channels)} channel(s).")


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _channel_list(values: list, total: int) -> list:
    """
    Expand a list of strings that may contain 'all' into a sorted list of
    integer element indices (1-based).
    """
    if values is None:
        return []
    if "all" in values:
        return list(range(1, total + 1))
    indices = [int(v) for v in values]
    invalid = [i for i in indices if not (1 <= i <= total)]
    if invalid:
        raise ValueError(
            f"Channel indices {invalid} are out of range 1-{total} for this tile."
        )
    return sorted(set(indices))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Initialize a BFC tile (single or quad) and optionally configure "
            "individual Rx / Tx channels."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ---- Connection ---------------------------------------------------------
    conn = parser.add_argument_group("Connection")
    conn.add_argument(
        "--mode", "-m",
        choices=["single", "quad"],
        required=True,
        help="Tile configuration: 'single' (4 chips / 16 ch) or 'quad' (16 chips / 64 ch).",
    )
    conn.add_argument("--ip", default="10.75.161.150", help="IP address of the target hardware.")
    # conn.add_argument("--ip", default="10.75.161.115", help="IP address of the target hardware.")
    conn.add_argument(
        "--chip-ids",
        nargs="+",
        default=None,
        metavar="ID",
        help="Override chip IDs (4 for single, 16 for quad). Defaults used when omitted.",
    )

    # ---- Init bias ----------------------------------------------------------
    bias = parser.add_argument_group("Init bias voltages")
    bias.add_argument("--pa-off",  type=float, default=-4.8, metavar="V", help="PA bias when off.")
    bias.add_argument("--pa-on",   type=float, default=-4.8, metavar="V", help="PA bias when on.")
    bias.add_argument("--lna-off", type=float, default=-4.8, metavar="V", help="LNA bias when off.")
    bias.add_argument("--lna-on",  type=float, default=-4.8, metavar="V", help="LNA bias when on.")

    # ---- Rx channel settings ------------------------------------------------
    rx = parser.add_argument_group(
        "Rx channel settings",
        "Applied after init. Use 'all' to target every channel on the tile.",
    )
    rx.add_argument(
        "--rx-channels", nargs="+", default=None, metavar="N",
        help="1-based element indices to configure for Rx, or 'all'.",
    )
    rx.add_argument("--rx-gain",        type=int,   default=0,    metavar="0-127", help="Rx gain.")
    rx.add_argument("--rx-attenuation", type=int,   default=1,    choices=[0, 1],  help="Rx attenuator (1=in, 0=out).")
    rx.add_argument("--rx-phase",       type=float, default=0.0,  metavar="DEG",   help="Rx phase in degrees.")
    rx.add_argument("--lna-bias",       type=float, default=None, metavar="V",     help="LNA bias voltage (V).")
    rx.add_argument("--rx-enable",      action="store_true",                       help="Enable Rx on configured channels.")

    # ---- Tx channel settings ------------------------------------------------
    tx = parser.add_argument_group(
        "Tx channel settings",
        "Applied after init. Use 'all' to target every channel on the tile.",
    )
    tx.add_argument(
        "--tx-channels", nargs="+", default=None, metavar="N",
        help="1-based element indices to configure for Tx, or 'all'.",
    )
    tx.add_argument("--tx-gain",        type=int,   default=0,    metavar="0-127", help="Tx gain.")
    tx.add_argument("--tx-attenuation", type=int,   default=1,    choices=[0, 1],  help="Tx attenuator (1=in, 0=out).")
    tx.add_argument("--tx-phase",       type=float, default=0.0,  metavar="DEG",   help="Tx phase in degrees.")
    tx.add_argument("--pa-bias",        type=float, default=None, metavar="V",     help="Per-element PA bias voltage (V).")
    tx.add_argument("--tx-enable",      action="store_true",                       help="Enable Tx on configured channels.")
    tx.add_argument("--external-tr",    action="store_true",                       help="Use external TR source (toggles bias_dac_mode). Default: SPI.")

    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None):
    args = parse_args(argv)

    total_channels = ELEMENT_COUNT[args.mode]

    
    # Resolve chip IDs
    if args.chip_ids is not None:
        chip_ids = args.chip_ids
    elif args.mode == "single":
        chip_ids = SINGLE_TILE_DEFAULT_CHIP_IDS
    else:
        chip_ids = QUAD_TILE_DEFAULT_CHIP_IDS

    print(f"[INFO] Mode        : {args.mode} tile ({total_channels} channels)")
    print(f"[INFO] IP          : {args.ip}")
    print(f"[INFO] PA  off/on  : {args.pa_off} V / {args.pa_on} V")
    print(f"[INFO] LNA off/on  : {args.lna_off} V / {args.lna_on} V")
    print(f"[INFO] Chip IDs    : {chip_ids}")

    # ------------------------------------------------------------------
    # Connect
    # ------------------------------------------------------------------
    try:
        if args.mode == "single":
            dev = connect_single_tile(args.ip, chip_ids)
        else:
            dev = connect_quad_tile(args.ip, chip_ids)
    except Exception as exc:
        print(f"[ERROR] Connection failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Initialize
    # ------------------------------------------------------------------
    try:
        initialize(dev, args.pa_off, args.pa_on, args.lna_off, args.lna_on)
    except Exception as exc:
        print(f"[ERROR] Initialization failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Rx channel configuration  (optional)
    # ------------------------------------------------------------------
    try:
        rx_channels = _channel_list(args.rx_channels, total_channels)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    if rx_channels:
        print(f"[INFO] Configuring Rx on {len(rx_channels)} channel(s): {rx_channels}")
        try:
            configure_rx_channels(
                dev,
                channels    = rx_channels,
                gain        = args.rx_gain,
                attenuation = bool(args.rx_attenuation),
                phase       = args.rx_phase,
                lna_bias    = args.lna_bias,
                enable      = args.rx_enable,
            )
        except Exception as exc:
            print(f"[ERROR] Rx configuration failed: {exc}", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Tx channel configuration  (optional)
    # ------------------------------------------------------------------
    try:
        tx_channels = _channel_list(args.tx_channels, total_channels)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    if tx_channels:
        print(f"[INFO] Configuring Tx on {len(tx_channels)} channel(s): {tx_channels}")
        try:
            configure_tx_channels(
                dev,
                channels    = tx_channels,
                gain        = args.tx_gain,
                attenuation = bool(args.tx_attenuation),
                phase       = args.tx_phase,
                pa_bias     = args.pa_bias,
                enable      = args.tx_enable,
                external_tr = args.external_tr,
            )
        except Exception as exc:
            print(f"[ERROR] Tx configuration failed: {exc}", file=sys.stderr)
            sys.exit(1)

    print("[INFO] Done.")


if __name__ == "__main__":
    main()
