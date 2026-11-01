"""Which season a date falls in. No Home Assistant imports, so it tests on its own."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
import re

BIRTHDAY_LOOKS = 20
MONDAY = 0
SATURDAY = 5


@dataclass(frozen=True)
class Season:
    """A look the dashboards can wear."""

    key: str
    title: str
    theme: str
    solemn: bool = False
    banner: int = 0


WINTER = Season("winter", "Winter", "Dungeon Crawl Winter")
SPRING = Season("spring", "Spring", "Dungeon Crawl Spring")
SUMMER = Season("summer", "Summer", "Dungeon Crawl Summer")
FALL = Season("fall", "Fall", "Dungeon Crawl Fall")
NEW_YEAR = Season("new_year", "Happy New Year", "Dungeon Crawl New Year")
FAMILY_DAY = Season("family_day", "Family Day", "Dungeon Crawl Family Day")
EASTER = Season("easter", "Easter Season", "Dungeon Crawl Easter")
VICTORIA_DAY = Season("victoria_day", "Victoria Day", "Dungeon Crawl Victoria Day")
CANADA_DAY = Season("canada_day", "Canada Day", "Dungeon Crawl Canada Day")
BC_DAY = Season("bc_day", "BC Day", "Dungeon Crawl BC Day")
LABOUR_DAY = Season("labour_day", "Labour Day", "Dungeon Crawl Labour Day")
TRUTH_DAY = Season(
    "truth_and_reconciliation",
    "National Day for Truth and Reconciliation",
    "Dungeon Crawl Truth and Reconciliation",
    solemn=True,
)
THANKSGIVING = Season("thanksgiving", "Thanksgiving Weekend", "Dungeon Crawl Thanksgiving")
HALLOWEEN = Season("halloween", "Halloween Season", "Dungeon Crawl Halloween")
REMEMBRANCE_DAY = Season(
    "remembrance_day", "Remembrance Day", "Dungeon Crawl Remembrance Day", solemn=True
)
CHRISTMAS = Season("christmas", "Christmas Season", "Dungeon Crawl Christmas")

SEASONS = (
    WINTER,
    SPRING,
    SUMMER,
    FALL,
    NEW_YEAR,
    FAMILY_DAY,
    EASTER,
    VICTORIA_DAY,
    CANADA_DAY,
    BC_DAY,
    LABOUR_DAY,
    TRUTH_DAY,
    THANKSGIVING,
    HALLOWEEN,
    REMEMBRANCE_DAY,
    CHRISTMAS,
)

# The day each season starts, in the order they fall in a year.
SEASON_STARTS = ((3, 20, SPRING), (6, 21, SUMMER), (9, 22, FALL), (12, 21, WINTER))

# Each name and the line under it on the banner. A name comes round again only
# after the whole list has been used, so 12 names means 12 years between repeats.
NAMES = {
    "winter": (
        ("Frostbite", "Keep your toes"),
        ("Black Ice", "Watch your step"),
        ("Long Night", "Bring a torch"),
        ("Snow Day", "School is cancelled"),
        ("Deep Freeze", "Floor closed for ice"),
        ("Cold Snap", "Pants now advised"),
        ("Storm Watch", "Waves bigger than the boss"),
        ("Hot Cocoa", "Health potion restored"),
        ("Ice Cavern", "Slippery when crawled"),
        ("Wool Sock", "+5 to warmth"),
        ("Whiteout", "Map not available"),
        ("Toque", "+2 ear protection"),
    ),
    "spring": (
        ("Mud", "Boots off at the door"),
        ("Pollen", "Sneeze to attack"),
        ("Thaw", "Floor now squishy"),
        ("Blossom", "Petal storm incoming"),
        ("Rain Boot", "Puddle damage +2"),
        ("Seedling", "Level one plant"),
        ("Dandelion", "The weeds will rise"),
        ("Budbreak", "New growth unlocked"),
        ("Moss", "The roof remembers"),
        ("First Mow", "Lawn boss awakens"),
        ("Drizzle", "Chance of loot"),
        ("Slug", "Slow but deadly"),
    ),
    "summer": (
        ("Sunburn", "Reapply every floor"),
        ("Heat Wave", "Fire floor unlocked"),
        ("Barbecue", "Grill boss battle"),
        ("Long Day", "Solar loot bonus"),
        ("Sprinkler", "Water elemental spotted"),
        ("Popsicle", "Cold damage +3"),
        ("Beach", "Sand in every slot"),
        ("Mosquito", "Swarm incoming"),
        ("Tent", "Save point at the lake"),
        ("Flip Flop", "Toe defence -1"),
        ("Lawn Chair", "Rest at camp"),
        ("Sunbeam", "Cat buff active"),
    ),
    "fall": (
        ("Leaf Pile", "Hidden cat trap"),
        ("Gourd", "Gourd loot drop"),
        ("Sweater", "+3 cozy"),
        ("Windstorm", "Hold on to your roof"),
        ("Harvest", "Full pantry bonus"),
        ("Rain Tax", "Pay at the gutter"),
        ("Fog", "Visibility one tile"),
        ("Acorn", "Squirrel raid event"),
        ("Gutter", "Clean or be cleaned"),
        ("Mushroom", "Forage at own risk"),
        ("Spice", "Latte buff active"),
        ("Early Dark", "Lights on at five"),
    ),
}


def easter_sunday(year: int) -> date:
    """Return Easter Sunday, using the anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l) // 433
    month = (h + l - 7 * m + 90) // 25
    day = (h + l - 7 * m + 33 * month + 19) % 32
    return date(year, month, day)


def nth_weekday(year: int, month: int, weekday: int, nth: int) -> date:
    """Return the nth given weekday of a month, counting from 1."""
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (nth - 1))


def victoria_day(year: int) -> date:
    """Return the last Monday before May 25."""
    may_24 = date(year, 5, 24)
    return may_24 - timedelta(days=may_24.weekday())


def windows(year: int) -> list[tuple[date, date, Season]]:
    """Return each season's first and last day in a year, in date order."""
    easter = easter_sunday(year)
    thanksgiving = nth_weekday(year, 10, MONDAY, 2)
    days = [
        (date(year, 1, 1), date(year, 1, 1), NEW_YEAR),
        (nth_weekday(year, 2, MONDAY, 3),) * 2 + (FAMILY_DAY,),
        (easter - timedelta(days=7), easter + timedelta(days=2), EASTER),
        (victoria_day(year),) * 2 + (VICTORIA_DAY,),
        (date(year, 7, 1), date(year, 7, 1), CANADA_DAY),
        (nth_weekday(year, 8, MONDAY, 1),) * 2 + (BC_DAY,),
        (nth_weekday(year, 9, MONDAY, 1),) * 2 + (LABOUR_DAY,),
        (date(year, 9, 30), date(year, 9, 30), TRUTH_DAY),
        (thanksgiving - timedelta(days=2), thanksgiving, THANKSGIVING),
        (date(year, 10, 31), date(year, 10, 31), HALLOWEEN),
        (date(year, 11, 11), date(year, 11, 11), REMEMBRANCE_DAY),
        (date(year, 12, 1), date(year, 12, 26), CHRISTMAS),
    ]
    return sorted(days, key=lambda window: window[0])


def named(season: Season, year: int) -> Season:
    """Give a real season this year's name. Holidays keep the name they have."""
    names = NAMES.get(season.key)
    if names is None:
        return season
    number = year % len(names)
    return replace(season, title=f"{names[number][0]} Season", banner=number + 1)


def real_season(day: date) -> Season:
    """Return the winter, spring, summer or fall a date is in.

    A winter counts as the year it started in, so one winter keeps one name
    across New Year.
    """
    year, current = day.year - 1, WINTER
    for month, first, season in SEASON_STARTS:
        if (day.month, day.day) >= (month, first):
            year, current = day.year, season
    return named(current, year)


def season_for(day: date) -> Season:
    """Return the holiday a date falls in, or else the real season."""
    for first, last, season in windows(day.year):
        if first <= day <= last:
            return season
    return real_season(day)


def next_change(day: date) -> tuple[date, Season]:
    """Return the next holiday season to start after a date."""
    for first, _, season in windows(day.year) + windows(day.year + 1):
        if first > day:
            return first, season
    raise ValueError(day)


@dataclass(frozen=True)
class Person:
    """Someone with a birthday today."""

    name: str
    age: int | None = None


def person_from_title(title: str, year: int) -> Person:
    """Read a calendar title such as "Sam 1990" or "Sam's birthday (1990)"."""
    text = re.sub(r"['’]?s? +birthday", "", title.strip(), flags=re.IGNORECASE)
    match = re.fullmatch(r"(.*?)[\s,(]+(\d{4})\)?", text.strip())
    if match is None:
        return Person(text.strip())
    return Person(match[1].strip(), year - int(match[2]))


def birthday_look(names: list[str], day: date, hour: int) -> int:
    """Return which birthday look to show, from 1, moving on every hour.

    Starting from the names and the year gives each person a different run of
    looks each year, so 20 looks last a long time.
    """
    start = sum(ord(letter) for name in names for letter in name) + day.year * 7
    return (start + hour) % BIRTHDAY_LOOKS + 1
