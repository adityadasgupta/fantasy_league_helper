# Bundled NBA fallback data

These JSON files were fetched from the official NBA Stats API with `nba_api` on October 16, 2026 (Pacific time):

- `stats_2025-26.json`: completed 2025–26 regular-season `LeagueDashPlayerStats` totals for 582 players.
- `schedule_regular_2026-27.json`: 2026–27 `ScheduleLeagueV2` schedule, including preseason entries that the app filters out.

They provide historical player averages and scheduled teams if live NBA endpoints time out on a hosted service. The app still requests current-season stats and an updated schedule on each cache refresh. These snapshots can become stale after schedule changes and do not substitute for current-season game results.
