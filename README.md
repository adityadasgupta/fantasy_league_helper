# Five Cat

A daily Yahoo 9-category basketball lineup planner. The starting roster and Yahoo position eligibility come from the supplied screenshot. The app uses [swar/nba_api](https://github.com/swar/nba_api) to pull the NBA regular-season schedule and updated player averages. Preseason games are excluded. It searches all feasible combinations for the league's PG, SG, G, SF, PF, F, C, Util, Util slots.

## Run

```bash
cd /workspace/fantasy_league_helper
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Open the app through your environment's port 5000 access. No Yahoo login or API token is required. The browser stores roster edits, manual game flags, and matchup inputs locally.

For live data, the environment must allow HTTPS to `stats.nba.com` and `cdn.nba.com`. NBA data is cached in `.cache/` for 4 hours (player stats) or 12 hours (schedule). **Refresh NBA data** bypasses that cache. If NBA access fails, the app shows screenshot averages and allows you to mark today's games manually.

## Daily use

1. Check the game date, your NBA team codes, Yahoo position eligibility, and player availability. Correct game checkboxes for late injury news or schedule errors.
2. Optionally enter both teams' current weekly totals from Yahoo and turn on **Use matchup totals**. Enter field-goal makes and attempts and free-throw makes and attempts, not just percentages.
3. Select **Optimize lineup**. The category view compares your totals plus today's projected lineup to the opponent totals supplied. Five projected wins is a target, not a guarantee of the final weekly result.

Without matchup totals, the app recommends a balanced lineup using all nine categories. NBA stats are season averages blended with ten prior-season games early in the season; they are projections, not guaranteed player output. Yahoo eligibility and injuries require your input. The app does not automatically import your Yahoo matchup, opponent roster, or future weekly games.

## Checks

```bash
.venv/bin/python -m unittest discover -s tests -v
```
