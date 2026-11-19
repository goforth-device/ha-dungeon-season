"""The Peak Saver look, without Home Assistant."""

from custom_components.dungeon_season.peak import DIMMER, PALETTE, peak_saver_look

FALL = {
    "primary-color": "#ff8a3c",
    "dc-danger": "#ff3b30",
    "dc-banner": 'url("/dungeon_season/images/banner-fall-03.png")',
    "lovelace-background": 'center / cover no-repeat fixed url("/dungeon_season/images/fall-wall.jpg")',
}


def test_the_palette_replaces_todays_colours() -> None:
    look = peak_saver_look(FALL)
    assert look["primary-color"] == PALETTE["primary-color"]
    assert look["dc-loot"] == PALETTE["dc-loot"]


def test_todays_art_and_danger_colour_stay() -> None:
    look = peak_saver_look(FALL)
    assert look["dc-banner"] == FALL["dc-banner"]
    assert look["dc-danger"] == FALL["dc-danger"]


def test_the_wallpaper_is_dimmed_not_replaced() -> None:
    look = peak_saver_look(FALL)
    assert look["lovelace-background"] == f"{DIMMER}, {FALL['lovelace-background']}"


def test_dimming_twice_does_not_stack() -> None:
    once = peak_saver_look(FALL)
    assert peak_saver_look(once)["lovelace-background"] == once["lovelace-background"]


def test_a_theme_without_wallpaper_gets_none() -> None:
    assert "lovelace-background" not in peak_saver_look({"primary-color": "#fff"})


def test_the_original_theme_is_untouched() -> None:
    before = dict(FALL)
    peak_saver_look(FALL)
    assert before == FALL
