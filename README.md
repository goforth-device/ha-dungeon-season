# Dungeon Season

A small Home Assistant integration that changes the [Dungeon Crawl theme](https://github.com/goforth-device/ha-dungeon-crawl-theme) with the calendar, for dashboards in British Columbia.

Dashboards set their theme to `Dungeon Crawl Season`. Every hour the integration works out today's look and copies it into `themes/dungeon_season/season.yaml`, then reloads themes, so open dashboards change without a refresh.

| Look | When |
|---|---|
| Christmas | December 1 to 26 |
| Easter | Palm Sunday to the Tuesday after Easter |
| Thanksgiving | Saturday to Monday of Canadian Thanksgiving |
| Halloween | October 31 |
| New Year, Family Day, Victoria Day, Canada Day, BC Day, Labour Day, Truth and Reconciliation, Remembrance Day | On the day |
| Birthday | On the day. A birthday wins over any season, and the look changes every hour |
| Winter, Spring, Summer, Fall | Every other day, from December 21, March 20, June 21 and September 22 |

Each winter, spring, summer and fall gets its own name, such as Frostbite Season or Gourd Season. There are 12 names for each, used in turn, so a name doesn't come back for 12 years.

## Pictures

The theme's pictures ship inside this integration, in `custom_components/dungeon_season/images`, and Home Assistant serves them at `/dungeon_season/images/<name>`. When the integration copies a look, it points every picture link at that path instead of GitHub, so the dashboards show the art with no internet connection. Cards can use the same path, such as `/dungeon_season/images/cat-mood-calm.gif`. New art reaches the dashboards with a new release of this integration.

## Birthdays

Birthdays live in a Home Assistant calendar, never in this repository. Add a [Local Calendar](https://www.home-assistant.io/integrations/local_calendar/) called Birthdays, then add one all-day event for each person that repeats yearly, titled with their name and birth year, such as `Sam 1990`. Leave the year off to show the name with no age.

## Entities

- `sensor.dungeon_season`: today's season, with `title`, `solemn`, `theme`, `next_season` and `next_date` attributes.
- `sensor.dungeon_birthday`: today's names or `none`, with a `people` attribute holding each name and age.
- `select.dungeon_season_preview`: shows any look now. It goes back to `auto` at midnight.

## Install

Add this repository to HACS as a custom integration, install it, then add Dungeon Season from Settings, Devices & services. The themes folder must be included in `configuration.yaml`:

```yaml
frontend:
  themes: !include_dir_merge_named themes
```
