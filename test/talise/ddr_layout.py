"""PL DDR4 layout of the ADRV9009-ZU11EG production builds (adrv2crr_fmc_production).

Each of the two PL MIGs drives two x16 DDR4 parts. A build parameter
(PL_DDR0_MAP / PL_DDR1_MAP in the HDL) narrows a MIG to one part:

    0 - both parts, 32-bit interface, 2 GB
    1 - lower part only (dq[15:0]),  16-bit, 1 GB
    2 - upper part only (dq[31:16]), 16-bit, 1 GB

With a W-byte DDR data bus, byte ``k`` of each W-byte beat is carried on byte
lane ``k`` (MIG maps the AXI data bytes onto DQ in order), so a PS byte
address ``a`` lands on lane ``a % W``. Lanes 0-1 are the lower part, 2-3 the
upper part. This module has no dependencies so it can also be pushed to the
target and imported by the memory test helper.
"""

# Physical parts per MIG, indexed by byte lane pair (0: lanes 0-1, 1: lanes 2-3)
MIG_PARTS = {0: ("U30", "U31"), 1: ("U41", "U42")}

# Build configuration name -> PL_DDR0_MAP / PL_DDR1_MAP
CONFIG_MAPS = {
    "full": (0, 0),
    "ddr_lo": (1, 1),
    "ddr_hi": (2, 2),
}

# MIG 0 is reachable by the PS through M_AXI_HPM0_FPD at this address
MIG0_BASE = 0x4_0000_0000

# ddr_calib_gpio: bit 0 = MIG 0 init_calib_complete, bit 1 = MIG 1. On ZynqMP the
# ADI CPU interconnect sits on M_AXI_HPM0_LPD, so the nominal 0x43A0_0000 is
# 0x83A0_0000 for the PS (ad_cpu_interconnect adds 0x4000_0000).
CALIB_GPIO_ADDR = 0x83A0_0000
# axi_sysid (nominal 0x4500_0000), same offset
SYSID_ADDR = 0x8500_0000

# Project names written in the axi_sysid ROM (the field is truncated to 21
# characters, so ddr_lo and ddr_hi cannot be told apart from it).
SYSID_PROJECT_PREFIX = "adrv2crr_fmc_prod"


def is_production_design(sysid_strings):
    """True if the axi_sysid ROM strings name the production project.

    The ROM fields are split on non-printable bytes when read back (e.g.
    "adrv2crr_fmc prod"), so compare with separators removed.
    """
    import re

    flat = re.sub(r"[^a-z0-9]", "", (sysid_strings or "").lower())
    return re.sub(r"[^a-z0-9]", "", SYSID_PROJECT_PREFIX) in flat


def mig_map(config, mig):
    """Map value (0/1/2) of ``mig`` in build ``config``."""
    try:
        return CONFIG_MAPS[config][mig]
    except KeyError:
        raise ValueError(
            f"unknown config {config!r}, expected one of {sorted(CONFIG_MAPS)}"
        )


def bus_bytes(map_value):
    """DDR data bus width in bytes for a map value."""
    return 4 if map_value == 0 else 2


def mig_size(map_value):
    """MIG address space in bytes for a map value."""
    return (2 if map_value == 0 else 1) << 30


def active_parts(config, mig):
    """Parts driven by ``mig`` in build ``config``, lowest lane first."""
    lo, hi = MIG_PARTS[mig]
    return {0: (lo, hi), 1: (lo,), 2: (hi,)}[mig_map(config, mig)]


def lane_part(config, mig, lane):
    """Physical part that carries byte ``lane`` of ``mig`` in build ``config``."""
    m = mig_map(config, mig)
    nbytes = bus_bytes(m)
    if not 0 <= lane < nbytes:
        raise ValueError(f"lane {lane} out of range for a {nbytes * 8}-bit bus")
    parts = active_parts(config, mig)
    return parts[lane // 2] if m == 0 else parts[0]


def byte_lane(address_offset, map_value):
    """Byte lane carrying the byte at ``address_offset`` from the MIG base."""
    return address_offset % bus_bytes(map_value)


def describe(config, mig):
    """Human readable 'MIG n (Uxx[+Uyy])' for messages."""
    return f"MIG {mig} ({'+'.join(active_parts(config, mig))})"
