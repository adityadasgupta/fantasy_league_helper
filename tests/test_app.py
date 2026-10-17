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

    @patch('app.teams_playing', return_value=(['OKC'], None))
    @patch('app.project_players', return_value=({1628983: {'team': 'OKC', 'stats': {'pts': 30}}}, []))
    def test_daily_nba_response(self, *_):
        response = self.client.post('/api/day', json={'date': '2026-10-17', 'player_ids': [1628983]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['playing_teams'], ['OKC'])
        self.assertTrue(response.get_json()['stats_available'])

    def test_invalid_matchup_values_rejected(self):
        response = self.client.post('/api/plan', json={'players': [], 'mine': {'pts': -3}})
        self.assertEqual(response.status_code, 400)

    def test_oversized_roster_rejected(self):
        response = self.client.post('/api/plan', json={'players': [{}] * 19})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
