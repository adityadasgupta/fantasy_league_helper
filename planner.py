"""Exact nine-category daily lineup search for the Yahoo slots in this league."""

from itertools import combinations

from roster import STAT_KEYS

SLOTS = ("PG", "SG", "G", "SF", "PF", "F", "C", "UTIL1", "UTIL2")
COUNT_STATS = ("threes", "pts", "reb", "ast", "stl", "blk")
ALL_STATS = STAT_KEYS


def eligible(position, slot):
    if slot.startswith("UTIL"):
        return True
    if slot == "G":
        return any(p in position for p in ("PG", "SG"))
    if slot == "F":
        return any(p in position for p in ("SF", "PF"))
    return slot in position


def assignment(players):
    """Return player ID by slot, or None if this subset cannot fit."""
    ordered = sorted(players, key=lambda p: sum(eligible(p["positions"], s) for s in SLOTS))
    used = set()
    result = {}

    def search(index):
        if index == len(ordered):
            return True
        player = ordered[index]
        for slot in SLOTS:
            if slot not in used and eligible(player["positions"], slot):
                used.add(slot)
                result[slot] = player["id"]
                if search(index + 1):
                    return True
                used.remove(slot)
                del result[slot]
        return False

    return result if search(0) else None


def totals(players, baseline=None):
    result = {key: float((baseline or {}).get(key, 0) or 0) for key in ALL_STATS}
    for player in players:
        for key in ALL_STATS:
            result[key] += float(player["stats"].get(key, 0) or 0)
    return result


def category_values(stats):
    return {
        "FG%": stats["fgm"] / stats["fga"] if stats["fga"] else 0,
        "FT%": stats["ftm"] / stats["fta"] if stats["fta"] else 0,
        "3PM": stats["threes"],
        "PTS": stats["pts"],
        "REB": stats["reb"],
        "AST": stats["ast"],
        "STL": stats["stl"],
        "BLK": stats["blk"],
        "TO": stats["tov"],
    }


def balanced_score(stats):
    # Replacement-level, volume-aware value used only when matchup targets are absent.
    return (
        (stats["fgm"] - 0.47 * stats["fga"]) * 1.5
        + (stats["ftm"] - 0.78 * stats["fta"]) * 1.5
        + stats["threes"] / 2
        + stats["pts"] / 20
        + stats["reb"] / 7
        + stats["ast"] / 5
        + stats["stl"]
        + stats["blk"]
        - stats["tov"] / 2
    )


def matchup_score(mine, theirs):
    mine_cat, their_cat = category_values(mine), category_values(theirs)
    wins = ties = 0
    margins = 0.0
    categories = []
    scales = {"FG%": 0.03, "FT%": 0.04, "3PM": 3, "PTS": 20, "REB": 8,
              "AST": 6, "STL": 2, "BLK": 2, "TO": 3}
    for category, value in mine_cat.items():
        opponent = their_cat[category]
        difference = (opponent - value) if category == "TO" else (value - opponent)
        if abs(difference) < 1e-9:
            ties += 1
            result = "tie"
        elif difference > 0:
            wins += 1
            result = "win"
        else:
            result = "loss"
        margins += max(-2, min(2, difference / scales[category]))
        categories.append({"name": category, "mine": round(value, 3),
                           "opponent": round(opponent, 3), "result": result})
    return (wins, ties, margins), categories


def optimize(players, mine=None, opponent=None, use_matchup=False):
    candidates = [p for p in players if p.get("available") and p.get("playing")]
    best = None
    best_key = None
    max_players = min(len(SLOTS), len(candidates))
    for count in range(max_players + 1):
        for subset in combinations(candidates, count):
            stats = totals(subset, mine)
            if use_matchup:
                score, categories = matchup_score(stats, totals([], opponent))
                key = (*score, balanced_score(totals(subset)), count)
            else:
                categories = None
                key = (balanced_score(totals(subset)), count)
            if best_key is not None and key <= best_key:
                continue
            slots = assignment(subset)
            if slots is None:
                continue
            best = {"slots": slots, "totals": {k: round(v, 2) for k, v in stats.items()},
                    "categories": categories, "active_ids": [p["id"] for p in subset],
                    "bench_ids": [p["id"] for p in players if p["id"] not in slots.values()],
                    "matchup_wins": score[0] if use_matchup else None,
                    "matchup_ties": score[1] if use_matchup else None}
            best_key = key
    return best
