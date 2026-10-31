"""A selector for trying out any look before its date comes round."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DungeonSeasonConfigEntry
from .const import AUTO, BIRTHDAY_PREVIEW, DOMAIN
from .manager import SeasonManager
from .seasons import SEASONS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DungeonSeasonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the selector."""
    async_add_entities([SeasonPreview(entry.runtime_data)])


class SeasonPreview(SelectEntity):
    """Pick a look to preview. It goes back to automatic at midnight."""

    _attr_name = "Dungeon Season Preview"
    _attr_unique_id = f"{DOMAIN}_preview"
    _attr_icon = "mdi:palette"
    _attr_should_poll = False
    _attr_options = [AUTO, *(season.key for season in SEASONS), BIRTHDAY_PREVIEW]

    def __init__(self, manager: SeasonManager) -> None:
        """Remember the manager."""
        self.manager = manager

    @property
    def current_option(self) -> str:
        """Return the look being previewed, or auto."""
        return self.manager.preview

    async def async_added_to_hass(self) -> None:
        """Update whenever the manager does."""
        self.async_on_remove(
            self.manager.async_add_listener(self.async_write_ha_state)
        )

    async def async_select_option(self, option: str) -> None:
        """Show the chosen look."""
        await self.manager.async_set_preview(option)
