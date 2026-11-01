"""Date rules, checked against the holidays package for every year to 2060."""

from __future__ import annotations

from datetime import date, timedelta
import importlib.util
from pathlib import Path
import re
import sys

import pytest

PATH = Path(__file__).parents[1] / "custom_components" / "dungeon_season" / "seasons.py"
spec = importlib.util.spec_from_file_location("seasons", PATH)
seasons = importlib.util.module_from_spec(spec)
sys.modules["seasons"] = seasons
spec.loader.exec_module(seasons)

YEARS = range(2026, 2061)


def holiday_dates():
    """Return BC's statutory holidays by name from an independent source."""
    holidays = pytest.importorskip("holidays")
    found = {}
    for year in YEARS:
        for day, name in holidays.Canada(subdiv="BC", years=year, observed=False).items():
            found[(year, name)] = day
    return found


@pytest.mark.parametrize(
    ("name", "key"),
    [
        ("New Year's Day", "new_year"),
        ("Family Day", "family_day"),
        ("Good Friday", "easter"),
        ("Victoria Day", "victoria_day"),
        ("Canada Day", "canada_day"),
        ("British Columbia Day", "bc_day"),
        ("Labour Day", "labour_day"),
        ("National Day for Truth and Reconciliation", "truth_and_reconciliation"),
        ("Thanksgiving Day", "thanksgiving"),
        ("Remembrance Day", "remembrance_day"),
        ("Christmas Day", "christmas"),
    ],
)
def test_every_bc_stat_holiday_gets_its_season(name, key):
    days = {year: day for (year, label), day in holiday_dates().items() if label == name}
    assert sorted(days) == list(YEARS)
    for day in days.values():
        assert seasons.season_for(day).key == key, day


def test_no_bc_stat_holiday_is_left_out():
    for (_, name), day in holiday_dates().items():
        assert seasons.season_for(day).key not in seasons.NAMES, (name, day)


def test_christmas_runs_december_first_to_boxing_day():
    assert seasons.season_for(date(2026, 11, 30)).key == "fall"
    assert seasons.season_for(date(2026, 12, 1)).key == "christmas"
    assert seasons.season_for(date(2026, 12, 26)).key == "christmas"
    assert seasons.season_for(date(2026, 12, 27)).key == "winter"


def test_easter_runs_palm_sunday_to_tuesday_after():
    # Easter Sunday is April 5 in 2026 and March 28 in 2027
    for sunday in (date(2026, 4, 5), date(2027, 3, 28)):
        assert seasons.easter_sunday(sunday.year) == sunday
        assert seasons.season_for(sunday - timedelta(days=8)).key in seasons.NAMES
        assert seasons.season_for(sunday - timedelta(days=7)).key == "easter"
        assert seasons.season_for(sunday + timedelta(days=2)).key == "easter"
        assert seasons.season_for(sunday + timedelta(days=3)).key in seasons.NAMES


def test_thanksgiving_is_saturday_to_monday():
    # Thanksgiving Monday is October 12 in 2026
    assert seasons.season_for(date(2026, 10, 9)).key == "fall"
    assert seasons.season_for(date(2026, 10, 10)).key == "thanksgiving"
    assert seasons.season_for(date(2026, 10, 12)).key == "thanksgiving"
    assert seasons.season_for(date(2026, 10, 13)).key == "fall"


def test_one_day_holidays_end_the_next_day():
    assert seasons.season_for(date(2026, 10, 31)).key == "halloween"
    assert seasons.season_for(date(2026, 11, 1)).key == "fall"
    assert seasons.season_for(date(2026, 11, 12)).key == "fall"


def test_only_the_two_memorial_days_are_solemn():
    assert {s.key for s in seasons.SEASONS if s.solemn} == {
        "truth_and_reconciliation",
        "remembrance_day",
    }


def test_seasons_never_overlap():
    for year in YEARS:
        spans = seasons.windows(year)
        for (_, last, _), (first, _, _) in zip(spans, spans[1:]):
            assert last < first


def test_next_change_crosses_the_new_year():
    assert seasons.next_change(date(2026, 10, 31)) == (
        date(2026, 11, 11),
        seasons.REMEMBRANCE_DAY,
    )
    assert seasons.next_change(date(2026, 12, 20)) == (
        date(2027, 1, 1),
        seasons.NEW_YEAR,
    )


@pytest.mark.parametrize(
    ("day", "key"),
    [
        (date(2027, 3, 19), "winter"),
        (date(2027, 3, 20), "spring"),
        (date(2027, 6, 20), "spring"),
        (date(2027, 6, 21), "summer"),
        (date(2027, 9, 21), "summer"),
        (date(2027, 9, 22), "fall"),
        (date(2027, 12, 20), "fall"),
        (date(2027, 12, 21), "winter"),
    ],
)
def test_real_seasons_start_on_the_right_days(day, key):
    assert seasons.real_season(day).key == key


def test_every_day_has_a_look_of_its_own():
    day = date(2026, 1, 1)
    while day.year == 2026:
        assert seasons.season_for(day).theme.startswith("Dungeon Crawl ")
        day += timedelta(days=1)


def test_one_winter_keeps_its_name_across_new_year():
    assert seasons.real_season(date(2026, 12, 27)) == seasons.real_season(date(2027, 1, 2))


def test_every_season_has_twelve_names_and_none_are_shared():
    names = [name for options in seasons.NAMES.values() for name, _ in options]
    assert {len(options) for options in seasons.NAMES.values()} == {12}
    assert len(set(names)) == 48


@pytest.mark.parametrize("season", [seasons.WINTER, seasons.SPRING, seasons.SUMMER, seasons.FALL])
def test_a_name_does_not_repeat_for_twelve_years(season):
    titles = [seasons.named(season, year).title for year in YEARS]
    for start in range(len(titles) - 11):
        assert len(set(titles[start : start + 12])) == 12


def test_banner_lines_fit_the_banner():
    for options in seasons.NAMES.values():
        for name, line in options:
            assert len(name) <= 13
            assert len(line) <= 27
            assert re.fullmatch(r"[A-Za-z0-9+ -]+", name + line)


def test_a_named_season_points_at_its_banner():
    season = seasons.named(seasons.FALL, 2026)
    assert season.title == f"{seasons.NAMES['fall'][2026 % 12][0]} Season"
    assert season.banner == 2026 % 12 + 1
    assert seasons.named(seasons.CHRISTMAS, 2026) is seasons.CHRISTMAS


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Sam 1990", ("Sam", 36)),
        ("Sam, 1990", ("Sam", 36)),
        ("Sam (1990)", ("Sam", 36)),
        ("Sam's birthday 1990", ("Sam", 36)),
        ("Mary Jo 2000", ("Mary Jo", 26)),
        ("Sam", ("Sam", None)),
        ("Sam's Birthday", ("Sam", None)),
    ],
)
def test_person_from_title(title, expected):
    person = seasons.person_from_title(title, 2026)
    assert (person.name, person.age) == expected


def test_birthday_looks_stay_in_range_and_keep_moving():
    day = date(2026, 3, 4)
    looks = [seasons.birthday_look(["Sam"], day, hour) for hour in range(24)]
    assert all(1 <= look <= seasons.BIRTHDAY_LOOKS for look in looks)
    assert len(set(looks)) == 20
    assert looks[0] != seasons.birthday_look(["Sam"], day.replace(year=2027), 0)
    assert looks[0] != seasons.birthday_look(["Alex"], day, 0)
