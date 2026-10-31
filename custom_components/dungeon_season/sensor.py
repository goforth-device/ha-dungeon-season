"""Sensors showing today's season and birthdays."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DungeonSeasonConfigEntry
from .const import DOMAIN, NO_BIRTHDAY
from .manager import SeasonManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DungeonSeasonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors."""
    manager = entry.runtime_data
    async_add_entities([SeasonSensor(manager), BirthdaySensor(manager)])


class _ManagerSensor(SensorEntity):
    """A sensor the manager updates."""

    _attr_should_poll = False

    def __init__(self, manager: SeasonManager) -> None:
        """Remember the manager."""
        self.manager = manager

    async def async_added_to_hass(self) -> None:
        """Update whenever the manager does."""
        self.async_on_remove(
            self.manager.async_add_listener(self.async_write_ha_state)
        )


class SeasonSensor(_ManagerSensor):
    """Today's season, such as christmas or everyday."""

    _attr_name = "Dungeon Season"
    _attr_unique_id = f"{DOMAIN}_season"
    _attr_icon = "mdi:calendar-star"

    @property
    def native_value(self) -> str:
        """Return the season's key."""
        return self.manager.season.key

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return what the dashboards and automations can use."""
        manager = self.manager
        return {
            "title": manager.season.title,
            "solemn": manager.season.solemn,
            "theme": manager.theme,
            "preview": manager.preview,
            "next_season": manager.next_season.key if manager.next_season else None,
            "next_date": manager.next_date.isoformat() if manager.next_date else None,
        }


class BirthdaySensor(_ManagerSensor):
    """Who has a birthday today."""

    _attr_name = "Dungeon Birthday"
    _attr_unique_id = f"{DOMAIN}_birthday"
    _attr_icon = "mdi:cake-variant"

    @property
    def native_value(self) -> str:
        """Return today's names, or none."""
        names = [person.name for person in self.manager.people]
        return " and ".join(names) if names else NO_BIRTHDAY

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return each person's name and age."""
        return {
            "people": [
                {"name": person.name, "age": person.age}
                for person in self.manager.people
            ]
        }
