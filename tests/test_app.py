import unittest
from unittest.mock import patch

from app import app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_and_search(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        data = self.client.get('/api/search?q=Gilgeous').get_json()
        self.assertTrue(any(p['name'] == 'Shai Gilgeous-Alexander' for p in data))

    @patch('app.teams_playing', return_value=(['OKC'], None, True))
    @patch('app.project_players', return_value=({1628983: {'team': 'OKC', 'stats': {'pts': 30}}}, []))
    def test_daily_nba_response(self, *_):
        response = self.client.post('/api/day', json={'date': '2026-10-17', 'player_ids': [1628983]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['playing_teams'], ['OKC'])
        self.assertTrue(response.get_json()['stats_available'])

    @patch('app.app.logger.exception')
    @patch('app.teams_playing', side_effect=TimeoutError('schedule timed out'))
    @patch('app.project_players', side_effect=TimeoutError('stats timed out'))
    def test_nba_provider_failure_returns_manual_fallback(self, *_):
        response = self.client.post('/api/day', json={'date': '2026-10-20', 'player_ids': [1628983], 'refresh': True})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['stats_available'])
        self.assertFalse(data['schedule_available'])
        self.assertEqual(data['players'], {})
        self.assertEqual(len(data['warnings']), 2)

    @patch('nba_source.scheduleleaguev2.ScheduleLeagueV2', side_effect=TimeoutError('schedule blocked'))
    @patch('nba_source.leaguedashplayerstats.LeagueDashPlayerStats', side_effect=TimeoutError('stats blocked'))
    def test_live_nba_outage_uses_bundled_stats_and_schedule(self, *_):
        response = self.client.post('/api/day', json={'date': '2026-10-20', 'player_ids': [1628983], 'refresh': True})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['stats_available'])
        self.assertTrue(data['schedule_available'])
        self.assertIn('OKC', data['playing_teams'])
        self.assertEqual(len(data['warnings']), 2)

    def test_invalid_matchup_values_rejected(self):
        response = self.client.post('/api/plan', json={'players': [], 'mine': {'pts': -3}})
        self.assertEqual(response.status_code, 400)

    def test_oversized_roster_rejected(self):
        response = self.client.post('/api/plan', json={'players': [{}] * 19})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
