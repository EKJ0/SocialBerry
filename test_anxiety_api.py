import unittest

from plantme_project.app import app


class AnxietyApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_checkin_requires_anxiety_level(self) -> None:
        res = self.client.post('/api/anxiety/checkin', json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn('error', data)

    def test_checkin_returns_risk_and_patterns(self) -> None:
        res = self.client.post(
            '/api/anxiety/checkin',
            json={
                'anxiety_level': 6,
                'sleep_hours': 6.0,
                'caffeine_mg': 120,
                'heart_rate_bpm': 88,
                'context': 'work',
                'food_level': 6,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('risk_next_hour', data)
        self.assertIn('risk_next_day', data)
        self.assertIn('patterns', data)
        self.assertIn(data['risk_next_hour']['level'], {'low', 'medium', 'high'})

    def test_episode_endpoint_works(self) -> None:
        res = self.client.post('/api/anxiety/episode', json={})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('risk_next_hour', data)


if __name__ == '__main__':
    unittest.main()

