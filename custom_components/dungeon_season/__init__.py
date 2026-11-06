"""Dungeon Season: changes the dashboard theme with the holidays and birthdays."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, IMAGES_URL
from .manager import SeasonManager

PLATFORMS = [Platform.SELECT, Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DungeonSeasonConfigEntry = ConfigEntry[SeasonManager]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the theme's pictures from Home Assistant, once per start."""
    if hass.http is not None:
        # No cache headers: a picture redrawn under the same name shows up on the next load.
        await hass.http.async_register_static_paths(
            [StaticPathConfig(IMAGES_URL, str(Path(__file__).parent / "images"), False)]
        )
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: DungeonSeasonConfigEntry
) -> bool:
    """Set up Dungeon Season from a config entry."""
    manager = SeasonManager(hass, entry)
    entry.runtime_data = manager
    await manager.async_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(manager.async_start())
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: DungeonSeasonConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
