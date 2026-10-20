"""Fetch Open-Meteo weather or CAMS PM2.5 using a private location file."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import urlopen


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Missing numeric forecast value')
    return value


def normalize(data, kind, sampled_at):
    current = data['current']
    result = {'sampled_at': sampled_at, 'model_time': number(current['time'])}
    if kind == 'air':
        result['pm2_5'] = number(current['pm2_5'])
        if result['pm2_5'] < 0:
            raise ValueError('Negative particulate concentration')
        return result
    result['temperature'] = number(current['temperature_2m'])
    result['feels_like'] = number(current['apparent_temperature'])
    daily = data['daily']
    result['today'] = {key: number(daily[key][0]) for key in (
        'time', 'temperature_2m_max', 'temperature_2m_min',
        'precipitation_sum', 'precipitation_probability_max')}
    hourly = data['hourly']
    times = hourly['time']
    if any(len(hourly[key]) != len(times) for key in ('temperature_2m', 'precipitation_probability')):
        raise ValueError('Mismatched hourly arrays')
    result['hourly'] = [
        {'time': number(t), 'temperature': number(temp), 'rain_chance': number(rain)}
        for t, temp, rain in zip(times, hourly['temperature_2m'], hourly['precipitation_probability'])
        if t >= current['time'] - current['time'] % 3600
    ][:36]
    if len(result['hourly']) < 12 or any(not 0 <= h['rain_chance'] <= 100 for h in result['hourly']):
        raise ValueError('Incomplete or invalid hourly forecast')
    return result


def fetch(location, kind):
    params = {'latitude': location['latitude'], 'longitude': location['longitude'],
              'timezone': location['timezone'], 'timeformat': 'unixtime', 'forecast_days': 3}
    if kind == 'weather':
        endpoint = 'https://api.open-meteo.com/v1/forecast'
        params.update(current='temperature_2m,apparent_temperature',
                      hourly='temperature_2m,precipitation_probability',
                      daily='temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max')
    else:
        endpoint = 'https://air-quality-api.open-meteo.com/v1/air-quality'
        params.update(current='pm2_5')
    with urlopen(endpoint + '?' + urlencode(params), timeout=20) as response:
        data = json.load(response)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    return normalize(data, kind, now)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['weather', 'air'])
    parser.add_argument('--location', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = fetch(json.loads(args.location.read_text()), args.kind)
    except Exception as error:
        # Network exception text can contain the private coordinates in its URL.
        print(f'Outdoor {args.kind} update failed: {type(error).__name__}', file=sys.stderr)
        return 1
    print(json.dumps(result, separators=(',', ':'), allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
