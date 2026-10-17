"""NBA schedule and per-game projections through swar/nba_api."""

from datetime import date, datetime, timedelta
import json
from pathlib import Path
import time

from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import leaguedashplayerstats, scheduleleaguev2

from roster import STAT_KEYS

CACHE_DIR = Path(__file__).parent / ".cache"


def season_for(day):
    year = day.year if day.month >= 10 else day.year - 1
    return f"{year}-{str(year + 1)[-2:]}"


def previous_season(season):
    year = int(season[:4]) - 1
    return f"{year}-{str(year + 1)[-2:]}"


def cached(name, ttl_seconds, producer, force=False):
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"{name}.json"
    if not force and path.exists() and time.time() - path.stat().st_mtime < ttl_seconds:
        return json.loads(path.read_text())
    data = producer()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data))
    temporary.replace(path)
    return data


def league_stats(season, refresh=False):
    def download():
        frame = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season, season_type_all_star="Regular Season", timeout=15
        ).league_dash_player_stats.get_data_frame()
        columns = ("PLAYER_ID", "TEAM_ABBREVIATION", "GP", "FGM", "FGA", "FTM",
                   "FTA", "FG3M", "PTS", "REB", "AST", "STL", "BLK", "TOV")
        return frame[list(columns)].to_dict("records")

    return cached(f"stats_{season}", 4 * 3600, download, refresh)


def project_players(player_ids, day, refresh=False):
    season = season_for(day)
    errors = []
    seasons = {}
    for which in (previous_season(season), season):
        try:
            seasons[which] = {int(row["PLAYER_ID"]): row for row in league_stats(which, refresh)}
        except Exception as exc:
            errors.append(f"{which} player stats unavailable: {type(exc).__name__}")
    projected = {}
    columns = ("FGM", "FGA", "FTM", "FTA", "FG3M", "PTS", "REB", "AST", "STL", "BLK", "TOV")
    for player_id in player_ids:
        previous = seasons.get(previous_season(season), {}).get(player_id)
        current = seasons.get(season, {}).get(player_id)
        rows = [(row, max(0, int(row.get("GP") or 0))) for row in (previous, current) if row is not None]
        rows = [(row, gp) for row, gp in rows if gp]
        if not rows:
            continue
        if len(rows) == 2:
            # Ten prior-season games stabilize a small current-season sample.
            weights = (10.0, float(rows[1][1]))
        else:
            weights = (1.0,)
        denominator = sum(weights)
        stats = {}
        for key, column in zip(STAT_KEYS, columns):
            stats[key] = round(sum(float(row.get(column) or 0) / gp * weight
                                   for (row, gp), weight in zip(rows, weights)) / denominator, 3)
        projected[player_id] = {"stats": stats, "team": current.get("TEAM_ABBREVIATION") if current else None,
                                "games_sample": sum(gp for _, gp in rows)}
    return projected, errors


def _parse_game_day(value):
    raw = str(value).split("T")[0].split(" ")[0]
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return datetime.strptime(raw, "%m/%d/%Y").date()


def teams_playing(day, refresh=False):
    season = season_for(day)

    def download():
        frame = scheduleleaguev2.ScheduleLeagueV2(season=season, timeout=15).season_games.get_data_frame()
        return frame[["gameDate", "gameId", "homeTeam_teamTricode", "awayTeam_teamTricode"]].to_dict("records")

    try:
        games = cached(f"schedule_regular_{season}", 12 * 3600, download, refresh)
        # 001 is preseason and 004 is playoffs; Yahoo weekly fantasy uses regular-season 002 games.
        return sorted({team for game in games if str(game["gameId"]).startswith("002") and _parse_game_day(game["gameDate"]) == day
                       for team in (game["homeTeam_teamTricode"], game["awayTeam_teamTricode"])}), None
    except Exception as exc:
        # The live endpoint covers today when the season schedule endpoint is unavailable.
        if day == date.today():
            try:
                games = scoreboard.ScoreBoard(timeout=10).get_dict()["scoreboard"]["games"]
                return sorted({team for game in games if str(game.get("gameId", "")).startswith("002") for team in
                               (game["homeTeam"]["teamTricode"], game["awayTeam"]["teamTricode"])}), None
            except Exception:
                pass
        return [], f"NBA schedule unavailable: {type(exc).__name__}"
