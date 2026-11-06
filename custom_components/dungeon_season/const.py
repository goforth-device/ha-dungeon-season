"""Constants for Dungeon Season."""

from __future__ import annotations

DOMAIN = "dungeon_season"

ALIAS_THEME = "Dungeon Crawl Season"
FALLBACK_THEME = "Dungeon Crawl"
BIRTHDAY_THEME = "Dungeon Crawl Birthday {:02}"
THEME_FILE = ("themes", "dungeon_season", "season.yaml")

# The theme's pictures ship inside this integration and Home Assistant serves them, so the dashboards don't need
# GitHub. Links to the theme repository's images are rewritten to this path when the look is copied.
IMAGES_URL = "/dungeon_season/images"
# The theme's two fonts, with a stylesheet to add as a dashboard resource in place of Google Fonts.
FONTS_URL = "/dungeon_season/fonts"
REMOTE_IMAGES = "https://raw.githubusercontent.com/goforth-device/ha-dungeon-crawl-theme/main/images/"

CONF_CALENDAR = "calendar"
DEFAULT_CALENDAR = "calendar.birthdays"

AUTO = "auto"
BIRTHDAY_PREVIEW = "birthday"
NO_BIRTHDAY = "none"
