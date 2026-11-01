"""Load the integration in a real Home Assistant with a stand-in calendar and themes."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from freezegun.api import FrozenDateTimeFactory
from homeassistant import config_entries
from homeassistant.components.frontend import DATA_THEMES
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import parse_yaml
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_component,
)

from custom_components.dungeon_season.const import ALIAS_THEME, DOMAIN
from custom_components.dungeon_season.seasons import FALL, named

THEMES = """
Dungeon Crawl:
  primary-color: "#fallback"
Dungeon Crawl Fall:
  primary-color: "#fall"
  lovelace-background: 'center / cover url("https://example.com/wall.jpg")'
  dc-banner: 'url("https://example.com/banner-fall.png")'
Dungeon Crawl Halloween:
  primary-color: "#halloween"
Dungeon Crawl Christmas:
  primary-color: "#christmas"
"""
for number in range(1, 21):
    THEMES += f'Dungeon Crawl Birthday {number:02}:\n  primary-color: "#birthday{number}"\n'


@pytest.fixture(autouse=True)
def enable_custom(enable_custom_integrations):
    """Let Home Assistant load the integration."""


@pytest.fixture
def events() -> list[dict]:
    """Return the stand-in calendar's events."""
    return []


@pytest.fixture
async def setup(hass: HomeAssistant, events: list[dict]):
    """Stand in for the frontend and calendar, reading themes the way HA does."""
    await hass.config.async_set_time_zone("America/Vancouver")
    mock_component(hass, "frontend")
    hass.data[DATA_THEMES] = dict(parse_yaml(THEMES))
    reloads = []

    async def reload_themes(call: ServiceCall) -> None:
        reloads.append(call)
        path = Path(hass.config.path("themes/dungeon_season/season.yaml"))
        written = parse_yaml(path.read_text(encoding="utf-8"))
        hass.data[DATA_THEMES] = {**dict(parse_yaml(THEMES)), **written}

    async def get_events(call: ServiceCall) -> dict:
        return {"calendar.birthdays": {"events": list(events)}}

    hass.services.async_register("frontend", "reload_themes", reload_themes)
    hass.services.async_register(
        "calendar", "get_events", get_events, supports_response=SupportsResponse.ONLY
    )

    async def start() -> list[ServiceCall]:
        entry = MockConfigEntry(domain=DOMAIN, data={"calendar": "calendar.birthdays"})
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return reloads

    return start


def at(*args) -> datetime:
    return datetime(*args, tzinfo=ZoneInfo("America/Vancouver"))


async def test_config_flow(hass: HomeAssistant) -> None:
    mock_component(hass, "frontend")
    hass.data[DATA_THEMES] = {}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"calendar": "calendar.birthdays"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Dungeon Season"


async def test_halloween_is_copied_into_the_alias(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 10, 31, 15))
    reloads = await setup()
    state = hass.states.get("sensor.dungeon_season")
    assert state.state == "halloween"
    assert state.attributes["title"] == "Halloween Season"
    assert state.attributes["solemn"] is False
    assert state.attributes["next_season"] == "remembrance_day"
    assert state.attributes["next_date"] == "2026-11-11"
    assert hass.data[DATA_THEMES][ALIAS_THEME]["primary-color"] == "#halloween"
    assert hass.states.get("sensor.dungeon_birthday").state == "none"
    assert len(reloads) == 1


async def test_an_ordinary_day_uses_the_real_season_and_its_named_banner(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 11, 3, 15))
    await setup()
    season = named(FALL, 2026)
    state = hass.states.get("sensor.dungeon_season")
    assert state.state == "fall"
    assert state.attributes["title"] == season.title
    theme = hass.data[DATA_THEMES][ALIAS_THEME]
    assert theme["primary-color"] == "#fall"
    assert theme["lovelace-background"] == 'center / cover url("https://example.com/wall.jpg")'
    assert theme["dc-banner"] == f'url("https://example.com/banner-fall-{season.banner:02}.png")'


async def test_a_season_with_no_installed_theme_falls_back(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 5, 1, 15))
    await setup()
    assert hass.states.get("sensor.dungeon_season").state == "spring"
    assert hass.data[DATA_THEMES][ALIAS_THEME]["primary-color"] == "#fallback"


async def test_midnight_changes_the_season_without_a_restart(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 11, 30, 23, 59))
    await setup()
    assert hass.data[DATA_THEMES][ALIAS_THEME]["primary-color"] == "#fall"
    freezer.move_to(at(2026, 12, 1, 0, 0, 5))
    async_fire_time_changed(hass, dt_util.now())
    await hass.async_block_till_done()
    assert hass.states.get("sensor.dungeon_season").state == "christmas"
    assert hass.data[DATA_THEMES][ALIAS_THEME]["primary-color"] == "#christmas"


async def test_the_theme_is_only_rewritten_when_it_changes(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 11, 3, 15))
    reloads = await setup()
    freezer.move_to(at(2026, 11, 3, 16, 0, 5))
    async_fire_time_changed(hass, dt_util.now())
    await hass.async_block_till_done()
    assert len(reloads) == 1


async def test_birthday_beats_the_season_and_rotates_hourly(
    hass: HomeAssistant, setup, events: list[dict], freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 12, 25, 9))
    events.append({"summary": "Sam 1990", "start": "2026-12-25", "end": "2026-12-26"})
    await setup()
    state = hass.states.get("sensor.dungeon_birthday")
    assert state.state == "Sam"
    assert state.attributes["people"] == [{"name": "Sam", "age": 36}]
    first = hass.data[DATA_THEMES][ALIAS_THEME]["primary-color"]
    assert first.startswith("#birthday")
    assert hass.states.get("sensor.dungeon_season").state == "christmas"

    freezer.move_to(at(2026, 12, 25, 10, 0, 5))
    async_fire_time_changed(hass, dt_util.now())
    await hass.async_block_till_done()
    second = hass.data[DATA_THEMES][ALIAS_THEME]["primary-color"]
    assert second.startswith("#birthday")
    assert second != first


async def test_two_birthdays_on_one_day(
    hass: HomeAssistant, setup, events: list[dict], freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 3, 4, 9))
    events.extend(
        [
            {"summary": "Sam 1990", "start": "2026-03-04", "end": "2026-03-05"},
            {"summary": "Alex", "start": "2026-03-04", "end": "2026-03-05"},
        ]
    )
    await setup()
    state = hass.states.get("sensor.dungeon_birthday")
    assert state.state == "Sam and Alex"
    assert state.attributes["people"] == [
        {"name": "Sam", "age": 36},
        {"name": "Alex", "age": None},
    ]


async def test_yesterdays_all_day_event_is_ignored(
    hass: HomeAssistant, setup, events: list[dict], freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 3, 5, 9))
    events.append({"summary": "Sam 1990", "start": "2026-03-04", "end": "2026-03-05"})
    await setup()
    assert hass.states.get("sensor.dungeon_birthday").state == "none"


async def test_preview_shows_a_look_and_clears_at_midnight(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 11, 3, 15))
    await setup()
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.dungeon_season_preview", "option": "christmas"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.dungeon_season").state == "christmas"
    assert hass.data[DATA_THEMES][ALIAS_THEME]["primary-color"] == "#christmas"
    assert hass.states.get("select.dungeon_season_preview").state == "christmas"

    freezer.move_to(at(2026, 11, 4, 0, 0, 5))
    async_fire_time_changed(hass, dt_util.now())
    await hass.async_block_till_done()
    assert hass.states.get("select.dungeon_season_preview").state == "auto"
    assert hass.states.get("sensor.dungeon_season").state == "fall"


async def test_preview_of_a_season_shows_its_name(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 12, 3, 15))
    await setup()
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.dungeon_season_preview", "option": "fall"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.dungeon_season").attributes["title"] == named(FALL, 2026).title
    assert "banner-fall-" in hass.data[DATA_THEMES][ALIAS_THEME]["dc-banner"]


async def test_birthday_preview_shows_a_made_up_person(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 11, 3, 15))
    await setup()
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.dungeon_season_preview", "option": "birthday"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.dungeon_birthday").state == "Preview"
    assert hass.data[DATA_THEMES][ALIAS_THEME]["primary-color"].startswith("#birthday")


async def test_a_missing_calendar_is_not_a_failure(
    hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to(at(2026, 11, 3, 15))
    hass.services.async_remove("calendar", "get_events")
    await setup()
    assert hass.states.get("sensor.dungeon_birthday").state == "none"
    assert hass.states.get("sensor.dungeon_season").state == "fall"
