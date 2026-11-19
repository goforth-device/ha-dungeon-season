"""The Peak Saver look. No Home Assistant imports, so it tests on its own.

During a BC Hydro Peak Saver event the dashboards keep today's art (season,
holiday or birthday) but dim it and switch to an electric blue and yellow
palette, so every display shows at a glance that it is time to use less power.
"""

from __future__ import annotations

from typing import Any

# Laid over the wallpaper, so the season's art stays recognisable but darker.
DIMMER = "linear-gradient(rgba(0, 8, 24, 0.62), rgba(0, 8, 24, 0.62))"

PALETTE: dict[str, str] = {
    "primary-color": "#4bc8ff",
    "rgb-primary-color": "75, 200, 255",
    "accent-color": "#ffe14a",
    "rgb-accent-color": "255, 225, 74",
    "warning-color": "#ffe14a",
    "state-active-color": "#ffe14a",
    "ha-card-header-color": "#ffe14a",
    "ha-card-background": "rgba(4, 8, 16, 0.9)",
    "app-header-text-color": "#ffe14a",
    "app-header-selection-bar-color": "#4bc8ff",
    "sidebar-selected-text-color": "#4bc8ff",
    "sidebar-selected-icon-color": "#4bc8ff",
    "sidebar-selected-background-color": "#4bc8ff",
    "dc-system": "#4bc8ff",
    "dc-system-glow": "rgba(75, 200, 255, 0.4)",
    "dc-loot": "#ffe14a",
    "dc-loot-glow": "rgba(255, 225, 74, 0.45)",
    "dc-accent": "#2f7bff",
    "dc-accent-glow": "rgba(47, 123, 255, 0.45)",
}


def peak_saver_look(theme: dict[str, Any]) -> dict[str, Any]:
    """Return today's theme recoloured for a Peak Saver event.

    Everything the palette doesn't name, such as the mascot, the loot box,
    the banner and the danger colour, stays as today's look has it.
    """
    look = {**theme, **PALETTE}
    background = theme.get("lovelace-background")
    if isinstance(background, str) and background and DIMMER not in background:
        look["lovelace-background"] = f"{DIMMER}, {background}"
    return look
