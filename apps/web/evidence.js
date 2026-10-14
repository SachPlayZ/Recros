'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const caseToken=new URLSearchParams(location.search).get('case');
let metadata=null,profile=null,anchors=[],result=null,busy=false,removed=null;
async function request(url,body){const r=await fetch(url,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const d=await r.json();if(!r.ok)throw new Error(typeof d.detail==='string'?d.detail:'Check the selected request.');return d;}
const selectedGoals=()=>[...document.querySelectorAll('.goal:checked')].map(i=>i.value);
function reset(){removed=null;result=null;$('outcome').hidden=true;$('empty').hidden=false;}
function updateDomain(){const seed=anchors.find(i=>i.id===$('source').value);const old=$('domain').value;$('domain').innerHTML=['movie','book','music'].map(d=>`<option value="${d}">${({movie:'Films',book:'Books',music:'Songs'})[d]}</option>`).join('');if(old)$('domain').value=old;
 const stated=seed?.preference_label?`You said: ${seed.preference_label}. `:'';
 let reason='';if(profile){const matching=(profile.reason_evidence?.observations||[]).filter(r=>r.item_id===seed?.id);reason=matching.length?'Your words: '+matching.map(r=>'“'+r.quote+'”').join('; ')+'. ':'';}
 $('anchor-note').textContent=stated+reason+'Choose the criterion you want considered today.';reset();}
async function run(){if(busy)return;busy=true;$('find').disabled=true;$('error').hidden=true;$('empty').hidden=true;$('outcome').hidden=true;$('loading').hidden=false;
 try{const body={source_id:$('source').value,target_domain:$('domain').value,goals:selectedGoals(),removed,evidence_mode:$('evidence-mode').value,extractor:$('extractor').value,inspected:true};if(caseToken){body.case_token=caseToken;body.expected_revision=profile.profile.revision;}
 result=await request('/api/transfer/discover',body);render(result);
 }catch(e){$('error').textContent=e.message;$('error').hidden=false;$('empty').hidden=false;}finally{busy=false;$('find').disabled=false;$('loading').hidden=true;}}
function render(d){$('outcome').hidden=false;let body=`<div class="outcome-head"><span class="decision-label">${({recommend:'Evidence-backed discovery',abstain:'More evidence needed',ask_user:'A criterion is needed',inspect_evidence:'Inspect the passages'})[d.kind]}</span><h2>${esc(d.message)}</h2><p class="scope">${esc(d.source_context.title)} · ${esc(({movie:'Films',book:'Books',music:'Songs'})[d.target_domain||$('domain').value])}</p></div>`;
 if(d.kind==='ask_user'){body+='<p>Choose one or two criteria at the left, then try again.</p>';}
 if(d.student_scope){body+=`<p class="scope">${esc(d.student_scope)}</p>`;}
 if(d.student_run){body+=`<p class="scope">Local model: ${d.student_run.parameter_count.toLocaleString()} parameters, ${d.student_run.device}. ${d.student_run.retained} of ${d.student_run.proposed} proposed features retained by the cached-evidence gate.</p>`;}
 if(d.intervention){const before=d.candidates.find(i=>i.id===d.intervention.before_item_id)?.title||d.intervention.before_item_id||'abstention';const after=d.candidates.find(i=>i.id===d.item_id)?.title||'abstention';body+=`<div class="removed"><strong>Evidence removed for this comparison.</strong><p>Earlier choice: ${esc(before)}. Current choice: ${esc(after)}. ${d.intervention.changed_choice?'The decision changed.':'The decision stayed the same; other evidence or equally supported candidates may remain.'}</p><button class="restore" id="restore">Restore the evidence</button></div>`;}
 const candidates=d.candidates||[];const supported=candidates.filter(i=>i.eligible);if(d.kind==='recommend')body+='<p class="scope">These are options to explore based on the requested features. Equally supported options share the same evidence score; the order does not predict which you will enjoy most.</p>';
 const shown=d.kind==='recommend'?supported:candidates.filter(i=>i.evidence.length);
 body+=shown.slice(0,5).map(i=>`<article class="candidate"><p class="match">${i.evidence.length} of ${selectedGoals().length} requested criteria supported by the supplied text</p><h3>${esc(i.title)}</h3><p class="creator">${esc(i.creators)}</p>${i.evidence.map(e=>`<div class="evidence"><p class="feature">${esc(metadata.features[e.feature].label)}</p><blockquote>“${esc(e.quote)}”</blockquote><div class="tools"><a href="${esc(e.source_url)}" target="_blank" rel="noopener noreferrer">${esc(e.source_kind)} ↗</a><button class="remove" data-item="${esc(i.id)}" data-feature="${esc(e.feature)}">Remove this evidence</button></div></div>`).join('')}${i.missing_features.length?`<p class="unknown">Unknown from this text: ${i.missing_features.map(f=>esc(metadata.features[f].label)).join(', ')}.</p>`:''}</article>`).join('');
 if(d.kind==='abstain')body+='<p>The missing information could change the decision. Try another criterion or restore the descriptions. A missing feature does not establish that the work lacks it.</p>';
 if(d.text_baseline){body+=`<details class="detail"><summary>Compare plain text retrieval</summary><p>BM25 retrieves passages using fixed words for the same criteria and candidate set. This is an alternative retrieval baseline, not a prediction of your rating.</p><ol class="baseline-list">${d.text_baseline.map(i=>`<li>${esc(i.title)}</li>`).join('')}</ol></details>`;}
 if(candidates.length){body+=`<details class="detail"><summary>Inspect all ${candidates.length} candidate records</summary>${candidates.map(i=>`<p><strong>${esc(i.title)}</strong><br>${i.evidence.length?'Supported: '+i.evidence.map(e=>esc(metadata.features[e.feature].label)).join(', '):'No supported requested feature in the current text.'}<br><span class="scope">${esc(i.evidence_text||'Evidence not yet inspected.')}</span></p>`).join('')}</details>`;}
 if(d.certificate){body+=`<details class="detail"><summary>Decision trace and limits</summary><ol>${d.trace.map(t=>`<li>${esc(t)}</li>`).join('')}</ol><p>${esc(d.certificate.scope)}</p><p>The modeled regret is ${d.certificate.modeled_regret}; the selected bound is ${d.certificate.bound}. These numbers describe the declared source-feature model, not a probability of liking the work.</p><p>${esc(d.scope)}</p></details><button class="export" id="export">Download this decision receipt</button>`;}
 $('outcome').innerHTML=body;
 for(const b of document.querySelectorAll('.remove'))b.addEventListener('click',()=>{removed={item_id:b.dataset.item,feature:b.dataset.feature};run();});
 $('restore')?.addEventListener('click',()=>{removed=null;run();});
 $('export')?.addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='recros-decision-receipt.json';a.click();URL.revokeObjectURL(url);});}
$('request').addEventListener('submit',e=>{e.preventDefault();run();});
$('source').addEventListener('change',updateDomain);$('domain').addEventListener('change',reset);$('evidence-mode').addEventListener('change',reset);
$('extractor').addEventListener('change',reset);
async function init(){try{metadata=await request('/api/transfer/catalog');anchors=metadata.source_anchors;
 if(metadata.student_available)document.querySelector('#extractor option[value="student"]').disabled=false;
 if(caseToken){profile=await request('/api/personal-case/'+encodeURIComponent(caseToken));anchors=profile.profile.items.filter(i=>i.identity_status==='matched');$('mode').textContent='Your local case';}
 $('source').innerHTML=anchors.map(i=>`<option value="${esc(i.id)}">${esc(i.title)} · ${esc(i.domain)}</option>`).join('');
 $('criteria').innerHTML=Object.entries(metadata.features).map(([k,v])=>`<label class="criterion"><input class="goal" type="checkbox" value="${esc(k)}"><span><strong>${esc(v.label)}</strong><small>${esc(v.description)}</small></span></label>`).join('');
 for(const check of document.querySelectorAll('.goal'))check.addEventListener('change',()=>{if(selectedGoals().length>2){check.checked=false;$('error').textContent='Choose at most two criteria for this bounded experiment.';$('error').hidden=false;}else{$('error').hidden=true;reset();}});
 $('catalog-count').textContent=Object.entries(metadata.counts).map(([d,n])=>n+' '+({movie:'films',book:'books',music:'music tracks'})[d]).join(', ')+'.'+(metadata.pipeline_counts.indexed_narrative_records?' Text retrieval index: '+metadata.pipeline_counts.indexed_narrative_records.toLocaleString()+' movie/book summaries.':'');
 const footer=document.querySelector('footer p');footer.textContent='This demonstration retrieves from an evidence bank of '+metadata.pipeline_counts.evidence_bank+' works. A cited feature can guide exploration; whether you enjoy the work remains an open question.';updateDomain();
 }catch(e){$('error').textContent=e.message;$('error').hidden=false;$('find').disabled=true;}}
init();
