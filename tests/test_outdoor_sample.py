"""Guard the forecast boundaries that would otherwise display misleading data."""
import copy
import unittest
from scripts.outdoor_sample import normalize


class OutdoorSampleTest(unittest.TestCase):
    def setUp(self):
        self.data = {'current': {'time': 7200, 'temperature_2m': 21.5, 'apparent_temperature': 22.5},
                     'hourly': {'time': list(range(0, 24 * 3600, 3600)), 'temperature_2m': [20] * 24,
                                'precipitation_probability': [0] * 24},
                     'daily': {'time': [0], 'temperature_2m_max': [24], 'temperature_2m_min': [18],
                               'precipitation_sum': [0], 'precipitation_probability_max': [0]}}

    def test_elapsed_hours_removed_and_zero_rain_retained(self):
        result = normalize(self.data, 'weather', 'sample-time')
        self.assertEqual(result['hourly'][0], {'time': 7200, 'temperature': 20, 'rain_chance': 0})
        self.assertEqual(result['today']['precipitation_sum'], 0)

    def test_missing_or_invalid_rain_is_not_reported_as_zero(self):
        for value in (None, float('nan'), 101, -1, True):
            with self.subTest(value=value):
                data = copy.deepcopy(self.data)
                data['hourly']['precipitation_probability'][2] = value
                with self.assertRaises(ValueError):
                    normalize(data, 'weather', 'sample-time')

    def test_short_or_mismatched_forecast_rejected(self):
        for key in ('time', 'temperature_2m', 'precipitation_probability'):
            data = copy.deepcopy(self.data)
            data['hourly'][key] = data['hourly'][key][:5]
            with self.assertRaises(ValueError):
                normalize(data, 'weather', 'sample-time')

    def test_air_sample_keeps_model_time_and_rejects_missing_pm25(self):
        result = normalize({'current': {'time': 7200, 'pm2_5': 16.1}}, 'air', 'sample-time')
        self.assertEqual(result, {'sampled_at': 'sample-time', 'model_time': 7200, 'pm2_5': 16.1})
        for value in (None, -1, float('inf')):
            with self.assertRaises(ValueError):
                normalize({'current': {'time': 7200, 'pm2_5': value}}, 'air', 'sample-time')


if __name__ == '__main__':
    unittest.main()
