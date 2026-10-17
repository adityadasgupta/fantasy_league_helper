import unittest

from planner import assignment, category_values, matchup_score, optimize, totals
from roster import STAT_KEYS


def player(pid, positions, playing=True, **stats):
    return {"id": pid, "name": str(pid), "positions": positions, "available": True,
            "playing": playing, "stats": {key: stats.get(key, 0) for key in STAT_KEYS}}


class PlannerTests(unittest.TestCase):
    def test_yahoo_slots_reject_four_centers(self):
        centers = [player(i, ["C"]) for i in range(4)]
        self.assertIsNone(assignment(centers))
        self.assertIsNotNone(assignment(centers[:3]))

    def test_percentages_use_attempts_and_turnovers_are_lower_is_better(self):
        mine = totals([player(1, ["PG"], fgm=2, fga=2, ftm=1, fta=2, tov=1)],
                      {"fgm": 10, "fga": 20, "ftm": 8, "fta": 10, "tov": 1})
        self.assertAlmostEqual(category_values(mine)["FG%"], 12 / 22)
        opponent = totals([], {"fgm": 10, "fga": 20, "ftm": 8, "fta": 10, "tov": 3})
        _, categories = matchup_score(mine, opponent)
        self.assertEqual(next(c for c in categories if c["name"] == "TO")["result"], "win")

    def test_matchup_can_bench_player_to_preserve_wins(self):
        risky = player(1, ["PG"], fgm=1, fga=10, ftm=0, fta=4, tov=8)
        baseline = {"fgm": 20, "fga": 40, "ftm": 15, "fta": 20, "tov": 3}
        opponent = {"fgm": 18, "fga": 40, "ftm": 14, "fta": 20, "tov": 5}
        result = optimize([risky], baseline, opponent, True)
        self.assertEqual(result["active_ids"], [])
        self.assertEqual(result["matchup_wins"], 3)

    def test_only_available_playing_players_selected(self):
        result = optimize([player(1, ["PG"], pts=20), player(2, ["SG"], playing=False, pts=30)])
        self.assertEqual(result["active_ids"], [1])


if __name__ == "__main__":
    unittest.main()
