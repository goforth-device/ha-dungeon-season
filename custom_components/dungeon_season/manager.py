"""Works out today's look and copies it into the theme the dashboards use."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import DATA_THEMES
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceNotFound
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import dump

from .const import (
    ALIAS_THEME,
    AUTO,
    BIRTHDAY_PREVIEW,
    BIRTHDAY_THEME,
    CONF_CALENDAR,
    DEFAULT_CALENDAR,
    FALLBACK_THEME,
    THEME_FILE,
)
from .seasons import (
    SEASONS,
    Person,
    Season,
    birthday_look,
    named,
    next_change,
    person_from_title,
    season_for,
)

_LOGGER = logging.getLogger(__name__)
SEASONS_BY_KEY = {season.key: season for season in SEASONS}


def _write_theme(path: Path, content: str) -> None:
    """Write the theme file, making its folder the first time."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _with_banner(theme: dict[str, Any], number: int) -> dict[str, Any]:
    """Point a theme at the banner with this season's name on it."""
    banner = theme.get("dc-banner")
    if not banner or not number:
        return theme
    return {**theme, "dc-banner": banner.replace(".png", f"-{number:02}.png")}


class SeasonManager:
    """Keep the season, the birthdays and the theme up to date."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Start on today's season until the first refresh."""
        self.hass = hass
        self.calendar: str = {**entry.data, **entry.options}.get(
            CONF_CALENDAR, DEFAULT_CALENDAR
        )
        self.preview = AUTO
        self.season: Season = season_for(dt_util.now().date())
        self.people: list[Person] = []
        self.theme = self.season.theme
        self.next_date: date | None = None
        self.next_season: Season | None = None
        self._today: date | None = None
        self._listeners: list[Callable[[], None]] = []

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Tell an entity when anything changes."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    @callback
    def async_start(self) -> Callable[[], None]:
        """Refresh on the hour and when the birthday calendar changes."""
        unsubscribe = [
            async_track_time_change(self.hass, self._async_tick, minute=0, second=5),
            async_track_state_change_event(
                self.hass, [self.calendar], self._async_calendar_changed
            ),
        ]
        if self.hass.state is not CoreState.running:
            unsubscribe.append(
                self.hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STARTED, self._async_started
                )
            )

        @callback
        def stop() -> None:
            for cancel in unsubscribe:
                cancel()

        return stop

    async def _async_tick(self, now: datetime) -> None:
        await self.async_refresh()

    async def _async_started(self, event: Event) -> None:
        await self.async_refresh()

    async def _async_calendar_changed(self, event: Event) -> None:
        await self.async_refresh()

    async def async_set_preview(self, option: str) -> None:
        """Show a look now. It goes back to automatic at midnight."""
        self.preview = option
        await self.async_refresh()

    async def async_refresh(self) -> None:
        """Work out today's look and apply it."""
        now = dt_util.now()
        today = now.date()
        if self._today not in (None, today):
            self.preview = AUTO
        self._today = today

        self.season = season_for(today)
        self.people = await self._async_birthdays(now)
        if self.preview == BIRTHDAY_PREVIEW:
            self.people = [Person("Preview", 42)]
        elif self.preview != AUTO:
            self.season = named(SEASONS_BY_KEY[self.preview], today.year)
            self.people = []
        self.next_date, self.next_season = next_change(today)

        if self.people:
            look = birthday_look([p.name for p in self.people], today, now.hour)
            self.theme = BIRTHDAY_THEME.format(look)
        else:
            self.theme = self.season.theme
        await self._async_apply_theme()
        for listener in self._listeners:
            listener()

    async def _async_birthdays(self, now: datetime) -> list[Person]:
        """Read today's birthdays from the calendar, which stays in Home Assistant."""
        start = dt_util.start_of_local_day(now)
        try:
            response = await self.hass.services.async_call(
                "calendar",
                "get_events",
                {
                    "entity_id": self.calendar,
                    "start_date_time": start.isoformat(),
                    "end_date_time": (start + timedelta(days=1)).isoformat(),
                },
                blocking=True,
                return_response=True,
            )
        except (ServiceNotFound, HomeAssistantError, ValueError) as err:
            _LOGGER.debug("Birthday calendar not ready: %s", err)
            return []
        events: list[dict[str, Any]] = (response or {}).get(self.calendar, {}).get(
            "events", []
        )
        today = now.date().isoformat()
        return [
            person_from_title(event["summary"], now.year)
            for event in events
            if str(event["start"]).startswith(today)
        ]

    async def _async_apply_theme(self) -> None:
        """Copy the chosen look into the theme the dashboards name."""
        themes = self.hass.data.get(DATA_THEMES, {})
        source = themes.get(self.theme)
        if source is not None:
            source = _with_banner(source, 0 if self.people else self.season.banner)
        else:
            source = themes.get(FALLBACK_THEME)
        if source is None:
            _LOGGER.warning("Theme %s is not installed", self.theme)
            return
        if themes.get(ALIAS_THEME) == source:
            return
        path = Path(self.hass.config.path(*THEME_FILE))
        content = dump({ALIAS_THEME: source})
        await self.hass.async_add_executor_job(_write_theme, path, content)
        await self.hass.services.async_call(
            "frontend", "reload_themes", blocking=True
        )
