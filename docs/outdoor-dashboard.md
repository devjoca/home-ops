# Outdoor forecast and air quality

The dashboard combines a 12-hour temperature and precipitation-probability chart
with today's low/high, apparent temperature and total precipitation forecast.
Indoor measured PM2.5 appears beside an outdoor CAMS model estimate. The model
estimate does not measure conditions at the house.

## Sources and files

- [Open-Meteo weather API](https://open-meteo.com/en/docs) supplies weather.
- [CAMS via Open-Meteo](https://open-meteo.com/en/docs/air-quality-api) supplies outdoor PM2.5.
- `scripts/outdoor_sample.py` fetches either source and prints normalized JSON.
- `frontend/outdoor-forecast-card.js` renders the weather chart without external libraries.

The collector accepts `weather` or `air` and requires `--location PATH`.
The private JSON location file has numeric `latitude` and `longitude` fields and
an IANA `timezone` string. Obtain these from HA's configured location. Keep this
file outside Git and restrict its permissions to the HA runtime user.

## HA deployment

Copy the collector into HA's config directory and the card into its `www/`
directory. Register the card as a JavaScript module dashboard resource, with a
version query when changing it. The deployed YAML and location mapping stay private.

The existing command-line integration runs weather every 30 minutes and air
quality hourly, with a 25-second command timeout. Both raw sensors use
`sampled_at` as their timestamp state. The weather sensor exposes `model_time`,
`temperature`, `feels_like`, `today` and `hourly` as JSON attributes. The air
sensor exposes `model_time` and `pm2_5`. Exclude raw samples from recorder so hourly
forecast arrays do not fill history.

Point a `custom:outdoor-forecast-card` at the weather sample entity. It displays
Celsius and millimetres and uses HA's timezone for labels. Forecasts expire after
90 minutes; yesterday's daily summary is hidden. Rain chance refers to
precipitation, including drizzle.

A template PM2.5 sensor exposes the air sample concentration in µg/m³. Its
availability requires a numeric value, a fetch less than two hours old and a model
timestamp less than three hours old. Both ages must be nonnegative. Show the
outdoor value as a model estimate and retain its source attribution.

Archive affected configuration before deployment. Run HA's configuration check,
inspect its output, then reload the affected command-line and template domains.
Refresh the dashboard and verify live values and the mobile layout. Keep archives
and device-specific rollback details private.

## Local checks

```sh
python3 -m unittest discover -s tests
node --check frontend/outdoor-forecast-card.js
```
