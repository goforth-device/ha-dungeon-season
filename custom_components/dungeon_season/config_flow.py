"""Config flow for Dungeon Season."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig
import voluptuous as vol

from . import DungeonSeasonConfigEntry
from .const import CONF_CALENDAR, DEFAULT_CALENDAR, DOMAIN


def _schema(calendar: str) -> vol.Schema:
    """Return the form with the birthday calendar filled in."""
    return vol.Schema(
        {
            vol.Required(CONF_CALENDAR, default=calendar): EntitySelector(
                EntitySelectorConfig(domain="calendar")
            )
        }
    )


class DungeonSeasonConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up the single Dungeon Season entry."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        entry: DungeonSeasonConfigEntry,
    ) -> DungeonSeasonOptionsFlow:
        """Return the options flow."""
        return DungeonSeasonOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask which calendar holds the birthdays."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input:
            return self.async_create_entry(title="Dungeon Season", data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema(DEFAULT_CALENDAR))


class DungeonSeasonOptionsFlow(OptionsFlowWithReload):
    """Change the birthday calendar."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the form."""
        if user_input:
            return self.async_create_entry(data=user_input)
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(current[CONF_CALENDAR])
        )
