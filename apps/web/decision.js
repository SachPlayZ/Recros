'use strict';
const $ = id => document.getElementById(id);
const esc = text => String(text ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names = {movie:'movie',book:'book',music:'song'};
let items = [], current = null, token = null, busy = false;
async function api(path, body) {
  const response = await fetch('/api/decision/' + path, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check the required fields.');
  return data;
}
async function attempt(fn) {
  if (busy) return;
  busy = true; $('error').hidden = true;
  document.querySelectorAll('button').forEach(b => b.disabled = true);
  try { await fn(); } catch (e) { $('error').textContent = e.message; $('error').hidden = false; }
  finally { busy = false; document.querySelectorAll('button').forEach(b => b.disabled = false); if (current?.rated) $('ratings').querySelector('button').disabled = true; }
}
function settings() {
  const source = items.find(i => i.id === $('seed').value);
  if (!source) return;
  for (const opt of $('target').options) opt.disabled = opt.value === source.domain;
  if ($('target').value === source.domain) $('target').value = [...$('target').options].find(o => !o.disabled).value;
  $('source-description').textContent = source.description;
  const previous = $('initial').value;
  $('initial').innerHTML = source.themes.map(t => `<option value="${esc(t)}">${esc(t)}</option>`).join('');
  if (source.themes.includes(previous)) $('initial').value = previous;
  const personal = $('mode').value === 'personal';
  $('personal-options').hidden = !personal; $('demo-options').hidden = personal;
  $('initial-wrap').hidden = !['item_fact_unknown','both_known'].includes($('condition').value);
}
function card(c) {
  if (!c.title) return `<article><p class="eyebrow">Candidate ${esc(c.alias)}</p><h3>Evidence not yet inspected</h3><p class="muted">One candidate supports each theme. Their identities are hidden in this controlled task until we inspect the evidence.</p></article>`;
  return `<article><p class="eyebrow">Candidate ${esc(c.alias)} · ${esc(c.concept)}</p><h3>${esc(c.title)}</h3><p>${esc(c.description)}</p><blockquote>“${esc(c.quote)}”</blockquote><a class="small" href="${esc(c.source_url)}" target="_blank" rel="noopener noreferrer">Source for the summary ↗</a></article>`;
}
function explanation(s) {
  if (s.status === 'outside_model') return s.suggested.reason;
  if (s.status !== 'active') return s.suggested.kind === 'recommend' ? 'Both the preference and the candidate evidence support this choice within our two-theme model.' : 'The available budget did not justify a choice under this model.';
  const n = s.possible_worlds.length;
  if (n === 4 && s.remaining_actions >= 2) return 'Both kinds of information are missing. Either action alone leaves the choice unresolved; planning for two actions can resolve it.';
  if (n > 1 && s.remaining_actions < 2 && !s.known_preference && !s.evidence_inspected) return 'One answer alone cannot settle this task. With this budget, stopping is less costly than paying for an unresolved choice.';
  if (!s.known_preference) return 'The evidence is available, but we still need to know which direction you want.';
  if (!s.evidence_inspected) return 'Your preference is known. We need to inspect which candidate supports it.';
  return 'The remaining uncertainty does not change which candidate matches the stated theme.';
}
function render(s) {
  current = s; $('trial').hidden = false;
  const kind = s.suggested.kind;
  const labels = {ask_user:'Ask about your preference',inspect_evidence:'Inspect the item evidence',recommend:'Make the recommendation',abstain:'Stop without recommending'};
  let action = '';
  if (s.status === 'active') {
    if (kind === 'ask_user') action = `<p><strong>${esc(s.question)}</strong></p><div class="actions">${s.themes.map(t => `<button data-answer="${esc(t)}">${esc(t)}</button>`).join('')}<button class="secondary" data-answer="none">Neither / another reason</button></div>`;
    else action = `<div class="actions"><button id="next">${labels[kind]} →</button></div>`;
  }
  const terminalTitle = kind === 'recommend' ? `Recommend candidate ${s.suggested.item}` : 'No recommendation';
  $('trial').innerHTML = `<div class="panel"><div class="section-title"><span class="number">02</span><h2>${s.status === 'active' ? 'Find the missing information' : 'The decision'}</h2></div>
    <div class="status"><strong>${esc(s.source.title)} → ${names[s.target_domain]}</strong><span>${s.remaining_actions} information actions left</span></div>
    <p class="decision">${s.status === 'active' ? labels[kind] : terminalTitle}</p><p>${esc(explanation(s))}</p>
    ${s.known_preference ? `<p><strong>Your stated direction:</strong> ${esc(s.known_preference)}</p>` : ''}
    <div class="grid">${(s.evaluation_candidates || s.candidates).map(card).join('')}</div>${action}
    ${s.observations.length ? `<h3>What happened</h3><ol class="trace">${s.observations.map(h => `<li>${esc({ask_user:'Asked you: ' + (h.answer === 'none' ? 'neither theme' : h.answer),inspect_evidence:'Retrieved the cached, attributed item passages.',recommend:'Recommended candidate ' + h.item,abstain:'Stopped without a recommendation.'}[h.kind])}</li>`).join('')}</ol>` : ''}
    <p class="small muted">${esc(s.certificate_note)}</p>
    ${s.mode === 'demo' ? `<details><summary>Inspect the decision model and its counterexample</summary><p class="small">Utility is a hypothetical theme match (0 or 1). Costs: question 0.04, evidence 0.02, abstention 0.45. These are assumptions, not measured satisfaction, prices, or calibrated confidence.</p><pre>${esc(JSON.stringify({possible_worlds:s.possible_worlds,counterexample:s.current_counterexample,chosen_plan:s.suggested},null,2))}</pre></details>` : ''}
    ${s.status !== 'active' ? '<div class="actions"><button class="secondary" id="export">Export this trial as JSON</button><button class="secondary" id="another">Set up another trial</button></div>' : ''}</div>`;
  $('next')?.addEventListener('click', () => step({kind,item:s.suggested.item}));
  document.querySelectorAll('[data-answer]').forEach(b => b.addEventListener('click', () => step({kind:'ask_user',answer:b.dataset.answer})));
  $('export')?.addEventListener('click', () => attempt(async () => {
    const data = await api(`sessions/${token}/export`);
    const url = URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
    const a = document.createElement('a'); a.href=url; a.download=`recros-${s.mode}-trial.json`; a.click(); URL.revokeObjectURL(url);
  }));
  $('another')?.addEventListener('click', () => { $('setup').scrollIntoView({behavior:'smooth'}); $('start').focus(); });
  $('rating-section').hidden = s.status === 'active' || s.mode !== 'personal';
  if (!$('rating-section').hidden && !s.rated) {
    $('rating-cards').innerHTML = s.evaluation_candidates.map(c => `<article><h3>${esc(c.title)}</h3><label>Your interest<select id="interest-${c.alias}" required><option value="">Choose…</option>${[1,2,3,4,5].map(n => `<option value="${n}">${n}${n===1?' · Not interested':n===5?' · Very interested':''}</option>`).join('')}</select></label><label>Familiarity<select id="familiarity-${c.alias}" required><option value="">Choose…</option><option value="unfamiliar">Unfamiliar</option><option value="familiar">Know about it</option><option value="consumed">Watched / read / heard it</option></select></label></article>`).join('');
  }
  if (s.rated) { $('saved').textContent='Saved locally. Export the trial to keep a copy.'; $('ratings').querySelectorAll('button,select,textarea').forEach(e => e.disabled=true); }
}
function step(data) { return attempt(async () => render(await api(`sessions/${token}/actions`,{...data,expected_revision:current.revision}))); }
$('setup').addEventListener('submit', e => { e.preventDefault(); attempt(async () => {
  const personal = $('mode').value === 'personal';
  const condition = personal ? 'both_unknown' : $('condition').value;
  const s = await api('sessions',{seed_id:$('seed').value,target:$('target').value,mode:$('mode').value,condition,budget:personal?2:Number($('budget').value),initial_preference:['both_known','item_fact_unknown'].includes(condition)?$('initial').value:null,source_familiarity:personal?$('source-familiarity').value:'unknown',source_liking:personal&&$('source-liking').value?Number($('source-liking').value):null});
  token = s.token; sessionStorage.setItem('recros-decision-token',token);
  $('ratings').reset(); $('ratings').querySelectorAll('button,select,textarea').forEach(e => e.disabled=false); $('saved').textContent='';
  render(s); $('trial').scrollIntoView({behavior:'smooth',block:'start'});
}); });
$('ratings').addEventListener('submit', e => { e.preventDefault(); attempt(async () => {
  const values = Object.fromEntries(['A','B'].map(a => [a,{interest:Number($(`interest-${a}`).value),familiarity:$(`familiarity-${a}`).value}]));
  render(await api(`sessions/${token}/ratings`,{...values,expected_revision:current.revision,theme_fit:$('theme-fit').value,feedback:$('feedback').value}));
}); });
['seed','target','mode','condition'].forEach(id => $(id).addEventListener('change',settings));
attempt(async () => {
  items = (await api('catalog')).items;
  $('seed').innerHTML = items.map(i => `<option value="${esc(i.id)}">${esc(i.title)} · ${names[i.domain]}</option>`).join('');
  $('seed').value = 'movie:manchester'; settings();
  const savedToken = sessionStorage.getItem('recros-decision-token');
  if (savedToken) { try { token=savedToken; render(await api(`sessions/${token}`)); } catch { sessionStorage.removeItem('recros-decision-token'); } }
});
