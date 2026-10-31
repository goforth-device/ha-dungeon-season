"""Dungeon Season: changes the dashboard theme with the holidays and birthdays."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .manager import SeasonManager

PLATFORMS = [Platform.SELECT, Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DungeonSeasonConfigEntry = ConfigEntry[SeasonManager]


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
