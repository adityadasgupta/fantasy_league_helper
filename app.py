"""Daily fantasy basketball planner web app."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
import math

from flask import Flask, jsonify, render_template, request
from nba_api.stats.static import players as nba_players

from nba_source import project_players, teams_playing
from planner import optimize
from roster import initial_roster, STAT_KEYS

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html", initial_roster=initial_roster())


@app.post("/api/day")
def day_data():
    payload = request.get_json(silent=True) or {}
    try:
        day = date.fromisoformat(payload["date"])
        ids = [int(value) for value in payload.get("player_ids", [])]
        if not 0 < len(ids) <= 18:
            raise ValueError("Select 1 to 18 players")
    except (ValueError, TypeError, KeyError):
        return jsonify(error="Enter a valid date and roster."), 400
    refresh = payload.get("refresh") is True
    with ThreadPoolExecutor(max_workers=2) as executor:
        stats_future = executor.submit(project_players, ids, day, refresh)
        schedule_future = executor.submit(teams_playing, day, refresh)
        try:
            projections, errors = stats_future.result()
        except Exception:
            app.logger.exception("NBA player projection failed")
            projections, errors = {}, ["NBA player stats unavailable; using saved roster averages."]
        try:
            teams, schedule_error, schedule_available = schedule_future.result()
        except Exception:
            app.logger.exception("NBA schedule lookup failed")
            teams, schedule_error, schedule_available = [], "NBA schedule unavailable; mark today's games manually.", False
    if schedule_error:
        errors.append(schedule_error)
    return jsonify(players=projections, playing_teams=teams,
                   schedule_available=schedule_available, warnings=errors,
                   stats_available=bool(projections))


@app.post("/api/plan")
def plan():
    payload = request.get_json(silent=True) or {}
    players = payload.get("players", [])
    if not isinstance(players, list) or len(players) > 18:
        return jsonify(error="A roster can have at most 18 players."), 400
    try:
        for player in players:
            player["id"] = int(player["id"])
            if not isinstance(player["positions"], list):
                raise ValueError()
            player["positions"] = [p for p in player["positions"] if p in ("PG", "SG", "SF", "PF", "C")]
            if not player["positions"]:
                raise ValueError()
            player["stats"] = {key: _number(player.get("stats", {}).get(key, 0)) for key in STAT_KEYS}
        mine = {key: _number((payload.get("mine") or {}).get(key, 0)) for key in STAT_KEYS}
        opponent = {key: _number((payload.get("opponent") or {}).get(key, 0)) for key in STAT_KEYS}
    except (ValueError, TypeError, KeyError, AttributeError):
        return jsonify(error="Roster or matchup totals contain invalid values."), 400
    result = optimize(players, mine, opponent, bool(payload.get("use_matchup")))
    return jsonify(result)


@app.get("/api/search")
def search_players():
    query = request.args.get("q", "").strip().casefold()
    if len(query) < 3:
        return jsonify([])
    matches = [p for p in nba_players.get_players() if query in p["full_name"].casefold()]
    return jsonify([{"id": p["id"], "name": p["full_name"]} for p in matches[:12]])


def _number(value):
    number = float(value or 0)
    if not math.isfinite(number) or number < 0 or number > 100000:
        raise ValueError()
    return number


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
