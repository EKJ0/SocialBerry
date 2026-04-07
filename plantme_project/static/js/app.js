document.addEventListener('DOMContentLoaded', () => {
  // Demo-only buttons (opt-in). Real buttons must not be hijacked.
  document.querySelectorAll('button.btn[data-demo="true"]').forEach((button) => {
    button.addEventListener('click', () => {
      const original = button.textContent;
      button.textContent = 'Demo only';
      setTimeout(() => {
        button.textContent = original;
      }, 1200);
    });
  });

  const checkinForm = document.querySelector('[data-checkin-form="true"]');
  if (!checkinForm) return;

  const statusEl = document.querySelector('[data-checkin-status="true"]');
  const riskEl = document.querySelector('[data-risk-output="true"]');
  const patternsEl = document.querySelector('[data-patterns-output="true"]');

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function renderRisk(data) {
    if (!riskEl) return;
    riskEl.innerHTML = '';

    const wrap = document.createElement('div');
    wrap.className = 'risk-grid';

    const nextHour = document.createElement('div');
    nextHour.className = `risk-pill risk-${data?.risk_next_hour?.level ?? 'unknown'}`;
    nextHour.innerHTML = `<strong>Next hour</strong><span>${data?.risk_next_hour?.level ?? '—'}</span><small>${data?.risk_next_hour?.explanation ?? ''}</small>`;

    const nextDay = document.createElement('div');
    nextDay.className = `risk-pill risk-${data?.risk_next_day?.level ?? 'unknown'}`;
    nextDay.innerHTML = `<strong>Next day</strong><span>${data?.risk_next_day?.level ?? '—'}</span><small>${data?.risk_next_day?.explanation ?? ''}</small>`;

    wrap.append(nextHour, nextDay);
    riskEl.appendChild(wrap);
  }

  function renderPatterns(data) {
    if (!patternsEl) return;
    patternsEl.innerHTML = '';
    const patterns = data?.patterns ?? [];
    if (!patterns.length) {
      patternsEl.textContent = 'No personal patterns yet — keep logging for a few days.';
      return;
    }
    const ul = document.createElement('ul');
    ul.className = 'check-list';
    patterns.forEach((p) => {
      const li = document.createElement('li');
      li.textContent = p;
      ul.appendChild(li);
    });
    patternsEl.appendChild(ul);
  }

  async function postJson(url, payload) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const message = data?.error || `Request failed (${res.status})`;
      throw new Error(message);
    }
    return data;
  }

  checkinForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    setStatus('Saving check-in…');

    const fd = new FormData(checkinForm);
    const payload = Object.fromEntries(fd.entries());

    // Coerce numeric fields.
    ['anxiety_level', 'sleep_hours', 'caffeine_mg', 'heart_rate_bpm', 'breathing_rate_bpm', 'food_level'].forEach((k) => {
      if (payload[k] === '' || payload[k] == null) return;
      payload[k] = Number(payload[k]);
    });

    try {
      const result = await postJson('/api/anxiety/checkin', payload);
      renderRisk(result);
      renderPatterns(result);
      setStatus('Saved. Updated your risk + insights.');
    } catch (err) {
      setStatus(`Couldn’t save check-in: ${err.message}`);
    }
  });

  const episodeBtn = document.querySelector('[data-log-episode="true"]');
  if (episodeBtn) {
    episodeBtn.addEventListener('click', async () => {
      setStatus('Logging episode…');
      try {
        const result = await postJson('/api/anxiety/episode', {});
        renderRisk(result);
        renderPatterns(result);
        setStatus('Episode logged. Take a slow breath — you’re not alone.');
      } catch (err) {
        setStatus(`Couldn’t log episode: ${err.message}`);
      }
    });
  }
});
