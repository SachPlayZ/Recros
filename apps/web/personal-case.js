'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const token=location.pathname.split('/').pop();
$('discovery-link').href='/explore?case='+encodeURIComponent(token);
const keys=['hail_mary','horror_contrast','books','songs','transfer'];
let current=null,busy=false;
async function api(body,suffix='/clarifications'){const r=await fetch('/api/personal-case/'+encodeURIComponent(token)+(body?suffix:''),body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const d=await r.json();if(!r.ok)throw new Error(typeof d.detail==='string'?d.detail:'Check your inputs.');return d;}
function render(d){
 current=d;const p=d.profile,a=d.audit;const byId=Object.fromEntries(p.items.map(i=>[i.id,i]));
 const conflicts=a.representations.domain_and_concepts.conflicts;
 $('audit').innerHTML=`<h2>What the current model loses</h2><p>${a.records.length} confirmed works included; ${a.pending_identity_ids.length} title matches awaiting confirmation.</p>${conflicts.length?conflicts.map(g=>`<article style="margin:15px 0"><h3>Same stored tags, opposite preferences</h3><p><strong>You liked:</strong> ${g.positive_ids.map(id=>esc(byId[id].title)).join(', ')}.</p><p><strong>You disliked:</strong> ${g.negative_ids.map(id=>esc(byId[id].title)).join(', ')}.</p><p><strong>Representation:</strong> ${esc(g.feature_vector[0])} · ${esc(g.feature_vector[1].join(', ')||'no supported concepts in this vocabulary')}.</p><p>A deterministic classifier seeing only that representation must give these works the same prediction. It cannot reproduce all of your stated labels. ${g.contains_untagged_items?'Here, missing evidence or an inadequate vocabulary is part of the problem.':''}</p></article>`).join(''):'<p>No identical-tag conflict in the confirmed examples. That does not establish predictive quality.</p>'}<p class="small">Adding the available genres changes the number of unavoidable label errors from <strong>${a.representations.domain_and_concepts.unavoidable_label_errors}</strong> to <strong>${a.representations.domain_genres_concepts.unavoidable_label_errors}</strong> on these same examples. This is a representation check, not an improvement measured on new users or items.</p><details><summary>Exactly what is being checked</summary><p class="small">${esc(a.scope)}</p><p class="small">${esc(a.missingness_note)}</p></details>`;
 $('audit').innerHTML+=a.same_creator_with_opposite_labels.map(g=>`<article style="margin-top:15px"><h3>Same creator, different response</h3><p>${esc(g.creator)}: you liked ${g.positive_ids.map(id=>esc(byId[id].title)).join(', ')} and disliked ${g.negative_ids.map(id=>esc(byId[id].title)).join(', ')}.</p><p class="small">Creator identity alone cannot explain this distinction. The reasons for these song preferences have not been supplied.</p></article>`).join('');
 renderObservations(d.reason_evidence);
 for(const k of keys)$(k).value=p.reasons[k]||'';
 const pending=p.items.filter(i=>i.identity_status!=='matched');
 $('identities').innerHTML=pending.map(i=>`<label style="display:block"><input type="checkbox" value="${esc(i.id)}" class="identity"> Confirm “${esc(i.user_title)}” means <strong>${esc(i.title)}</strong>${i.creators?' by '+esc(i.creators):''}.</label>`).join('');
 const recs=Object.fromEntries(a.records.map(i=>[i.id,i]));
 $('works').innerHTML=p.items.map(i=>`<article><p class="eyebrow">${esc(i.domain)} · You said: ${esc(i.preference_label)}</p><h3>${esc(i.title)}</h3>${i.scope?`<p class="small">${esc(i.scope)}</p>`:''}<p>${esc(i.description||'No narrative description in the recovered catalog.')}</p><p class="small"><strong>Source:</strong> ${i.source_kind==='recovered_catalog'?'Recovered dataset':'Paraphrase of the linked source'} · <a href="${esc(i.source_url)}" target="_blank" rel="noopener noreferrer">Inspect source ↗</a></p>${(recs[i.id]?.facets||[]).map(f=>`<p class="small"><strong>${esc(f.concept)}</strong></p><blockquote>“${esc(f.quote)}”</blockquote>`).join('')||'<p class="small muted">No supported concept shown; do not infer mood or narrative from this gap.</p>'}</article>`).join('');
 $('provenance').textContent='Item annotation: '+d.annotation_provenance.requested_model+' ('+d.annotation_runs.length+' cached calls, with item membership recorded). Live audit and transfer check: local code; no online inference.';
}
function renderObservations(e){
 $('observations').innerHTML=e.observations.map(r=>`<article><p class="eyebrow">${esc(r.source_title)}</p><h3>${esc(r.criterion)}</h3><blockquote>“${esc(r.quote)}”</blockquote><p>${esc(r.experience)}</p><p class="small">${r.interpretation_status==='ambiguous'?'Meaning remains unresolved.':'Proposed interpretation; not confirmed as a general preference.'} ${esc(r.scope)}</p></article>`).join('')||'<p>No current structured observations. Your original reasons remain below.</p>';
 $('invalid-observations').textContent=e.invalidated.length?e.invalidated.length+' interpretation(s) need review because their supporting explanation or work changed.':'';
 $('observation').innerHTML=e.observations.map(r=>`<option value="${esc(r.id)}">${esc(r.criterion)} — ${esc(r.source_title)}</option>`).join('');
 $('check-transfer').disabled=!e.observations.length;
 updateTargets();
}
function clearRehearsal(){ $('intent-confirmed').checked=false;$('transfer-result').innerHTML=''; }
function updateTargets(){
 const source=current.reason_evidence.observations.find(r=>r.id===$('observation').value);
 $('target-work').innerHTML=current.profile.items.filter(i=>i.id!==source?.item_id).map(i=>`<option value="${esc(i.id)}">${esc(i.title)} · ${esc(i.domain)}</option>`).join('');
 clearRehearsal();
}
$('observation').addEventListener('change',updateTargets);
$('target-work').addEventListener('change',clearRehearsal);
$('intent-confirmed').addEventListener('change',()=>{$('transfer-result').innerHTML='';});
$('transfer-rehearsal').addEventListener('submit',e=>{e.preventDefault();attempt(async()=>{
 const d=await api({expected_revision:current.profile.revision,observation_id:$('observation').value,target_id:$('target-work').value,intent_confirmed:$('intent-confirmed').checked},'/transfer-rehearsal');
 const names={resolve_identity:'Resolve the title',clarify_meaning:'Clarify the meaning',ask_intent:'Confirm the intended experience',inspect_target:'Inspect target-specific evidence'};
 $('transfer-result').innerHTML=`<p class="eyebrow">${d.cross_domain?'Cross-domain':'Within-domain'} rehearsal · target rating excluded</p><h3>Next: ${esc(names[d.next_action])}</h3><ol class="trace">${d.obligations.map(o=>`<li>${esc(o.message)}</li>`).join('')}</ol><p><strong>Fit claim: not supported yet.</strong> ${esc(d.conclusion)}</p><details><summary>Current target evidence: ${esc(d.target.title)}</summary><p>${esc(d.target.description||'No narrative description in the recovered catalog.')}</p><p>This text has not been checked against the proposed experience criterion.</p><a href="${esc(d.target.source_url)}" target="_blank" rel="noopener noreferrer">Inspect the source ↗</a></details><p class="small">${esc(d.scope)}</p>`;
});});
async function attempt(fn){if(busy)return;busy=true;$('save').disabled=true;$('error').hidden=true;try{await fn();}catch(e){$('error').textContent=e.message;$('error').hidden=false;}finally{busy=false;$('save').disabled=false;}}
$('reasons').addEventListener('submit',e=>{e.preventDefault();attempt(async()=>{const reasons=Object.fromEntries(keys.map(k=>[k,$(k).value]));const confirm_identities=[...document.querySelectorAll('.identity:checked')].map(i=>i.value);render(await api({expected_revision:current.profile.revision,reasons,confirm_identities}));$('saved').textContent='Saved locally. These answers remain development evidence.';});});
attempt(async()=>render(await api()));
