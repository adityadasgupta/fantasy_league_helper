from datetime import date
import unittest
from unittest.mock import patch

from nba_source import project_players, teams_playing


class NbaSourceTests(unittest.TestCase):
    @patch('nba_source.cached')
    def test_preseason_games_are_excluded(self, cached):
        cached.return_value = [
            {'gameDate': '10/16/2026 00:00:00', 'gameId': '0012600001',
             'homeTeam_teamTricode': 'OKC', 'awayTeam_teamTricode': 'BOS'},
            {'gameDate': '10/20/2026 00:00:00', 'gameId': '0022600001',
             'homeTeam_teamTricode': 'OKC', 'awayTeam_teamTricode': 'SAS'},
        ]
        self.assertEqual(teams_playing(date(2026, 10, 16)), ([], None))
        self.assertEqual(teams_playing(date(2026, 10, 20)), (['OKC', 'SAS'], None))

    @patch('nba_source.league_stats')
    def test_current_stats_blend_with_prior_season(self, league_stats):
        previous = {'PLAYER_ID': 1, 'TEAM_ABBREVIATION': 'OLD', 'GP': 50,
                    'FGM': 200, 'FGA': 500, 'FTM': 50, 'FTA': 100, 'FG3M': 100,
                    'PTS': 500, 'REB': 250, 'AST': 100, 'STL': 50, 'BLK': 25, 'TOV': 50}
        current = {'PLAYER_ID': 1, 'TEAM_ABBREVIATION': 'NEW', 'GP': 2,
                   'FGM': 10, 'FGA': 20, 'FTM': 4, 'FTA': 5, 'FG3M': 4,
                   'PTS': 28, 'REB': 12, 'AST': 8, 'STL': 2, 'BLK': 1, 'TOV': 3}
        league_stats.side_effect = [[previous], [current]]
        projections, errors = project_players([1], date(2026, 11, 1))
        self.assertEqual(errors, [])
        self.assertEqual(projections[1]['team'], 'NEW')
        self.assertAlmostEqual(projections[1]['stats']['pts'], (10 * 10 + 2 * 14) / 12, places=3)


if __name__ == '__main__':
    unittest.main()
