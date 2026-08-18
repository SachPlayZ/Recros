const state = { userId: Number(localStorage.getItem('recros_user_id')) || null, token: localStorage.getItem('recros_token') || '', domain: 'all' };
const groups = { domains: [], genres: [], themes: [], moods: [] };

const $ = (selector) => document.querySelector(selector);
const api = async (path, options = {}) => {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
};

document.querySelectorAll('[data-group]').forEach((group) => {
  group.addEventListener('click', (event) => {
    const button = event.target.closest('button');
    if (!button) return;
    const name = group.dataset.group;
    const value = button.dataset.value;
    button.classList.toggle('selected');
    groups[name] = [...group.querySelectorAll('.selected')].map((item) => item.dataset.value);
  });
});

$('#exploration').addEventListener('input', (event) => {
  const value = Number(event.target.value);
  $('#range-value').textContent = value < .35 ? 'familiar' : value > .65 ? 'adventurous' : 'balanced';
});

async function ensureUser() {
  if (state.userId) {
    try { await api(`/api/users/${state.userId}/profile`); return; } catch (_) { state.userId = null; }
  }
  const created = await api('/api/users', { method: 'POST' });
  state.userId = created.user_id;
  state.token = created.token;
  localStorage.setItem('recros_user_id', state.userId);
  localStorage.setItem('recros_token', state.token);
}

async function start() {
  await ensureUser();
  await api(`/api/users/${state.userId}/profile`, { method: 'PUT', body: JSON.stringify({
    preferred_domains: groups.domains, genres: groups.genres, themes: groups.themes, moods: groups.moods,
    exploration: Number($('#exploration').value), disliked_terms: [], seed_item_ids: [],
  }) });
  $('#onboarding').classList.add('hidden');
  $('#app').classList.remove('hidden');
  loadRecommendations();
}

function card(item) {
  const creator = item.creators || (item.domain === 'movie' ? 'Film' : item.domain === 'music' ? 'Artist' : 'Author');
  const title = item.title.length > 58 ? `${item.title.slice(0, 58)}…` : item.title;
  return `<article class="card" data-id="${item.id}"><div><div class="card-top"><span class="domain">${item.domain}</span><span class="card-year">${item.year || '—'}</span></div><h3>${escapeHtml(title)}</h3><div class="creator">${escapeHtml(creator)}</div><div class="reason">${escapeHtml(item.reason || '')}</div></div><div class="card-actions"><button class="action" data-action="like">♡ like</button><button class="action" data-action="save">+ save</button><button class="action" data-action="skip">skip →</button></div></article>`;
}

function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[char])); }

async function loadRecommendations() {
  $('#recommendations').innerHTML = '<div class="loading">Following the thread<span>…</span></div>';
  const data = await api(`/api/users/${state.userId}/recommendations?limit=12&domain=${state.domain}`);
  const p = data.profile;
  $('#profile-summary').textContent = `${p.genres.slice(0, 3).join(' · ') || 'Open curiosity'}${p.moods.length ? ` · ${p.moods.join(' · ')}` : ''}`;
  $('#recommendations').innerHTML = data.items.length ? data.items.map(card).join('') : '<div class="loading">No paths yet — try a different filter.</div>';
  document.querySelectorAll('.action').forEach((button) => button.addEventListener('click', async () => {
    const article = button.closest('.card');
    const action = button.dataset.action;
    await api(`/api/users/${state.userId}/feedback`, { method: 'POST', body: JSON.stringify({ item_id: article.dataset.id, action }) });
    button.classList.add('done');
    if (action === 'skip') setTimeout(loadRecommendations, 180);
  }));
}

$('#start').addEventListener('click', start);
$('#refresh').addEventListener('click', loadRecommendations);
$('#edit-profile').addEventListener('click', () => { $('#app').classList.add('hidden'); $('#onboarding').classList.remove('hidden'); });
document.querySelectorAll('#domain-tabs button').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('#domain-tabs button').forEach((item) => item.classList.remove('active'));
  button.classList.add('active'); state.domain = button.dataset.domain; loadRecommendations();
}));

(async () => {
  if (!state.userId) return;
  try {
    const profile = await api(`/api/users/${state.userId}/profile`);
    if (profile.genres.length || profile.preferred_domains.length || profile.moods.length) {
      $('#onboarding').classList.add('hidden'); $('#app').classList.remove('hidden'); loadRecommendations();
    }
  } catch (_) { localStorage.removeItem('recros_user_id'); localStorage.removeItem('recros_token'); state.userId = null; state.token = ''; }
})();
