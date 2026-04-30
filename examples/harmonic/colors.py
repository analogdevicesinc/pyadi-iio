# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic Design System color tokens.

Extracted from components/src/global/global.css (light) and
components/src/stories/assets/color-tokens-dark.json (dark)
in the harmonic repo.

Usage:
    from harmonic.colors import GRAY, BLUE, GREEN
"""

# ---------------------------------------------------------------------------
# Core palette — shared between light and dark
# ---------------------------------------------------------------------------

GRAY = {
    "white": "#FFFFFF",
    "100": "#F0F1F3",
    "200": "#D5D8DC",
    "300": "#B7BBC3",
    "400": "#9FA4AD",
    "500": "#848B95",
    "600": "#717984",
    "700": "#5E6773",
    "800": "#4B545D",
    "900": "#3A424B",
    "1000": "#293038",
    "black": "#101820",
}

BLUE = {
    "100": "#EDF3FC",
    "200": "#C6D8F6",
    "300": "#92BEFC",
    "400": "#6CA7EF",
    "500": "#3A8EE9",
    "600": "#0C79DF",
    "700": "#0067B9",
    "800": "#00549A",
    "900": "#00427A",
    "1000": "#00305B",
}

PURPLE = {
    "100": "#F6EEFC",
    "200": "#E5CEF6",
    "300": "#D4ADF0",
    "400": "#C48EEB",
    "500": "#B16EE0",
    "600": "#A451DF",
    "700": "#8E3DC7",
    "800": "#7531A5",
    "900": "#5D2287",
    "1000": "#431C5F",
}

GREEN = {
    "100": "#E4F6EF",
    "200": "#ABE3CD",
    "300": "#6FCEA6",
    "400": "#3DB885",
    "500": "#2E9E6F",
    "600": "#1F895E",
    "700": "#16744D",
    "800": "#115F3F",
    "900": "#114A32",
    "1000": "#0D3624",
}

ORANGE = {
    "100": "#FEEFE7",
    "200": "#FCCAB1",
    "300": "#FEA77C",
    "400": "#FB8246",
    "500": "#E76423",
    "600": "#CD5215",
    "700": "#AE4410",
    "800": "#91370B",
    "900": "#702C0A",
    "1000": "#551E03",
}

RED = {
    "100": "#FEEEEF",
    "200": "#FCCACE",
    "300": "#FFA3AB",
    "400": "#FE7B86",
    "500": "#F64C5A",
    "600": "#E13745",
    "700": "#C81A28",
    "800": "#A71420",
    "900": "#840D17",
    "1000": "#64060E",
}

PINK = {
    "100": "#FEECF8",
    "200": "#F9C7E8",
    "300": "#F7A1DA",
    "400": "#F07AC9",
    "500": "#E84DB4",
    "600": "#D3379F",
    "700": "#B32D87",
    "800": "#9A196F",
    "900": "#761A57",
    "1000": "#571140",
}

TEAL = {
    "100": "#E3F5FC",
    "200": "#A8DEF5",
    "300": "#68C6EE",
    "400": "#2CAFE8",
    "500": "#1694CA",
    "600": "#1981AE",
    "700": "#0E6D95",
    "800": "#07597E",
    "900": "#034663",
    "1000": "#053347",
}

# ---------------------------------------------------------------------------
# Typography (shared)
# ---------------------------------------------------------------------------

FONT_FAMILY_HEADING = "Barlow"
FONT_FAMILY_BODY = "Inter"
FONT_SIZE_SMALL = 12
FONT_SIZE_DEFAULT = 14
FONT_SIZE_MEDIUM = 16

# ---------------------------------------------------------------------------
# Dimensions (shared)
# ---------------------------------------------------------------------------

DM = {
    "0": 0,
    "25": 1,
    "50": 2,
    "100": 4,
    "200": 8,
    "300": 12,
    "400": 16,
    "500": 24,
    "600": 32,
    "700": 40,
    "800": 48,
    "900": 56,
    "1000": 64,
}

# ---------------------------------------------------------------------------
# Data visualization (shared — palette hues don't change, but the
# categorical series flips toward lighter shades on dark backgrounds)
# ---------------------------------------------------------------------------

CATEGORICAL_LIGHT = [
    TEAL["500"],  # #1694CA
    ORANGE["500"],  # #E76423
    PURPLE["700"],  # #8E3DC7
    GREEN["800"],  # #115F3F
    PINK["800"],  # #9A196F
    TEAL["1000"],  # #053347
]

CATEGORICAL_DARK = [
    TEAL["300"],  # #68C6EE
    ORANGE["300"],  # #FEA77C
    PURPLE["400"],  # #C48EEB
    GREEN["300"],  # #6FCEA6
    PINK["400"],  # #F07AC9
    TEAL["100"],  # #E3F5FC
]

_SEQUENTIAL_KEYS = (
    "100",
    "200",
    "300",
    "400",
    "500",
    "600",
    "700",
    "800",
    "900",
    "1000",
)

SEQUENTIAL = {
    hue: [ramp[k] for k in _SEQUENTIAL_KEYS]
    for hue, ramp in (
        ("teal", TEAL),
        ("orange", ORANGE),
        ("purple", PURPLE),
        ("green", GREEN),
        ("pink", PINK),
    )
}

INTENSITY = {
    "dark": [
        GRAY["black"],
        TEAL["1000"],
        TEAL["800"],
        TEAL["600"],
        TEAL["400"],
        GREEN["300"],
        ORANGE["300"],
        ORANGE["200"],
        GRAY["white"],
    ],
    "light": [
        GRAY["white"],
        ORANGE["100"],
        ORANGE["200"],
        ORANGE["300"],
        GREEN["400"],
        TEAL["500"],
        TEAL["700"],
        TEAL["900"],
    ],
    "ember": [
        GRAY["black"],
        PURPLE["1000"],
        PURPLE["800"],
        PINK["700"],
        RED["600"],
        ORANGE["500"],
        ORANGE["300"],
        ORANGE["100"],
    ],
    "flare": [
        GRAY["white"],
        ORANGE["100"],
        ORANGE["200"],
        ORANGE["300"],
        ORANGE["500"],
        RED["600"],
        RED["800"],
        RED["1000"],
    ],
    "dusk": [
        GRAY["white"],
        BLUE["100"],
        BLUE["200"],
        BLUE["400"],
        BLUE["600"],
        PURPLE["700"],
        PURPLE["800"],
        PURPLE["900"],
        PURPLE["1000"],
    ],
    "mono": [GRAY["black"], *(GRAY[k] for k in reversed(_SEQUENTIAL_KEYS)), GRAY["white"]],
    **{hue: [GRAY["black"], *reversed(ramp)] for hue, ramp in SEQUENTIAL.items()},
}
