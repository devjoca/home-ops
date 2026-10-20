/* Open-Meteo forecast, styled with the active HA theme. No external dependencies. */
class OutdoorForecastCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error('A forecast entity is required');
    this.config = config;
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
  }
  set hass(hass) {
    this._hass = hass;
    const state = hass.states[this.config.entity];
    const key = `${state?.last_updated}:${Math.floor(Date.now() / 60000)}:${hass.locale.language}`;
    if (key === this._key) return;
    this._key = key;
    this.render(state, hass);
  }
  getCardSize() { return 5; }
  render(state, hass) {
    const a = state?.attributes;
    const age = (Date.now() - Date.parse(state?.state)) / 60000;
    const fresh = Number.isFinite(age) && age >= -5 && age < 90;
    const date = t => new Intl.DateTimeFormat(hass.locale.language, {
      hour: '2-digit', hour12: false, timeZone: hass.config.time_zone
    }).format(new Date(t * 1000));
    const day = t => new Intl.DateTimeFormat('en-CA', {
      year: 'numeric', month: '2-digit', day: '2-digit', timeZone: hass.config.time_zone
    }).format(new Date(t * 1000));
    const fmt = v => Number.isFinite(v) ? new Intl.NumberFormat(hass.locale.language, {maximumFractionDigits: 1}).format(v) : '—';
    const hours = (a?.hourly || []).filter(h => h.time >= Math.floor(Date.now() / 3600000) * 3600).slice(0, 12);
    const valid = fresh && hours.length === 12;
    let body = '<p class="empty">Forecast unavailable or out of date. Waiting for an update.</p>';
    if (valid) {
      const low = Math.floor(Math.min(...hours.map(h => h.temperature))) - 1;
      const high = Math.ceil(Math.max(...hours.map(h => h.temperature))) + 1;
      const x = i => 40 + i * 38;
      const y = v => 105 - (v - low) / (high - low) * 78;
      const points = hours.map((h, i) => `${x(i)},${y(h.temperature)}`).join(' ');
      const grid = [low, (low + high) / 2, high].map(v => `<line x1="24" x2="478" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="20" y="${y(v)+4}" text-anchor="end">${fmt(v)}°</text>`).join('');
      const marks = hours.map((h, i) => `<g><title>${date(h.time)}: ${fmt(h.temperature)} °C, ${fmt(h.rain_chance)}% precipitation chance</title><circle cx="${x(i)}" cy="${y(h.temperature)}" r="3" class="temp"/><rect x="${x(i)-10}" y="${167-h.rain_chance*.38}" width="20" height="${h.rain_chance*.38}" rx="3" class="rain"/><text x="${x(i)}" y="186" text-anchor="middle">${fmt(h.rain_chance)}%</text>${i%2===0 || i===11 ? `<text x="${x(i)}" y="207" text-anchor="middle">${date(h.time)}</text>` : ''}</g>`).join('');
      const today = a.today;
      const todayFresh = today && day(today.time) === day(Date.now()/1000);
      body = `<div class="summary"><div><span>Today low / high</span><strong>${todayFresh ? `${fmt(today.temperature_2m_min)}° / ${fmt(today.temperature_2m_max)}°` : '—'}</strong></div><div><span>Feels like now</span><strong>${fmt(a.feels_like)}°</strong></div><div><span>Precipitation today</span><strong>${todayFresh ? `${fmt(today.precipitation_sum)} mm` : '—'}</strong></div></div>
      <div class="legend"><span><i class="temp"></i>Temperature · °C</span><span><i class="rain"></i>Rain chance · %</span></div>
      <svg viewBox="0 0 484 218" role="img" aria-label="Temperature and precipitation probability for the next twelve hours">${grid}<polyline points="${points}" class="line"/>${marks}</svg>
      <details><summary>Hourly values</summary><table><thead><tr><th>Time</th><th>Temperature</th><th>Rain chance</th></tr></thead><tbody>${hours.map(h=>`<tr><td>${date(h.time)}:00</td><td>${fmt(h.temperature)} °C</td><td>${fmt(h.rain_chance)}%</td></tr>`).join('')}</tbody></table></details>`;
    }
    this.shadowRoot.innerHTML = `<style>
      :host{display:block}ha-card{padding:18px;color:var(--primary-text-color);font-family:var(--ha-font-family-body,inherit)}
      h2{font-size:18px;font-weight:600;margin:0 0 18px}.summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:22px}
      .summary span{display:block;font-size:12px;color:var(--secondary-text-color);line-height:1.5}.summary strong{display:block;font-size:20px;font-weight:500;font-variant-numeric:tabular-nums;margin-top:4px;white-space:nowrap}
      .legend{display:flex;gap:18px;font-size:12px;color:var(--secondary-text-color)}.legend span{display:flex;align-items:center;gap:6px}i{width:9px;height:9px;border-radius:50%;display:inline-block}
      .temp{fill:var(--primary-color);background:var(--primary-color)}.rain{fill:var(--forecast-rain-color,#187f91);background:var(--forecast-rain-color,#187f91)}
      svg{display:block;width:100%;height:auto;margin-top:8px;overflow:visible}svg text{font-size:12px;fill:var(--secondary-text-color);font-variant-numeric:tabular-nums}.grid{stroke:var(--divider-color);stroke-width:1}.line{fill:none;stroke:var(--primary-color);stroke-width:2.5;stroke-linejoin:round}
      .source,.empty{font-size:12px;color:var(--secondary-text-color);line-height:1.6}.source{margin-top:12px}.source a{color:inherit}summary{font-size:12px;color:var(--secondary-text-color);cursor:pointer;padding:8px 0}summary:focus-visible{outline:2px solid var(--primary-color)}table{width:100%;font-size:12px;text-align:left;border-collapse:collapse}th,td{padding:6px;border-bottom:1px solid var(--divider-color)}
      @media(max-width:600px){.summary{grid-template-columns:repeat(2,minmax(0,1fr))}.summary>div:first-child{grid-column:1/-1}.summary strong{font-size:20px}.legend{gap:12px}}
    </style><ha-card><h2>Today & next 12 hours</h2>${body}<div class="source"><a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a> · ${fresh ? 'Updated '+new Intl.DateTimeFormat(hass.locale.language,{hour:'2-digit',minute:'2-digit',timeZone:hass.config.time_zone}).format(new Date(state.state)) : 'Update overdue'}<br>Rain chance includes any precipitation, including drizzle.</div></ha-card>`;
  }
}
if (!customElements.get('outdoor-forecast-card')) customElements.define('outdoor-forecast-card', OutdoorForecastCard);
