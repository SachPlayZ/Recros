'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {movie:'Movie',book:'Book',music:'Song'};
let found=[], selected=[], busy=false, profileToken=null;
async function api(path, body) {
  const r=await fetch('/api/familiar/'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json(); if(!r.ok) throw new Error(typeof d.detail==='string'?d.detail:'Please check the required fields.'); return d;
}
async function attempt(fn) {
  if(busy)return; busy=true; $('error').hidden=true;
  document.querySelectorAll('button').forEach(b=>b.disabled=true);
  try{await fn();}catch(e){$('error').textContent=e.message; $('error').hidden=false;}
  finally{busy=false; document.querySelectorAll('button').forEach(b=>b.disabled=false); $('save').disabled=!selected.length;}
}
function capture() {
  selected.forEach((w,i)=>{w.familiarity=$('f-'+i)?.value||''; w.liking=$('l-'+i)?.value||''; w.reason=$('r-'+i)?.value||'';});
}
function render() {
  $('empty').hidden=selected.length>0; $('save').disabled=!selected.length; $('saved').textContent=''; $('download').hidden=true;
  $('selected').innerHTML=selected.map((w,i)=>`<article style="margin:18px 0"><p class="eyebrow">${labels[w.domain]} ${w.id?'· catalog match':'· source needed'}</p><h3>${esc(w.title)}</h3><p class="muted small">${esc([w.creators,w.year].filter(Boolean).join(' · '))}</p><div class="controls"><label>Familiarity<select id="f-${i}" required><option value="">Choose…</option><option value="consumed">I have watched / read / heard it</option><option value="familiar">I know about it</option></select></label><label>Your liking<select id="l-${i}" required><option value="">Choose…</option>${[1,2,3,4,5].map(n=>`<option value="${n}">${n}${n===1?' · Strongly dislike':n===3?' · Neutral':n===5?' · Strongly like':''}</option>`).join('')}</select></label></div><label>What did you like or dislike? (optional)<textarea id="r-${i}" rows="2" maxlength="800" placeholder="A character, atmosphere, pacing, music, writing…">${esc(w.reason||'')}</textarea></label><button class="secondary" type="button" data-remove="${i}">Remove this selection</button></article>`).join('');
  selected.forEach((w,i)=>{$('f-'+i).value=w.familiarity||''; $('l-'+i).value=w.liking||'';});
  document.querySelectorAll('[data-remove]').forEach(b=>b.addEventListener('click',()=>{capture(); selected.splice(Number(b.dataset.remove),1); render();}));
}
function add(work) {
  capture();
  if(selected.some(w=>work.id?w.id===work.id:w.title.toLowerCase()===work.title.toLowerCase()&&w.domain===work.domain)) { $('search-status').textContent='Already selected.'; return; }
  if(selected.length>=20){$('search-status').textContent='You can save up to 20 works.';return;}
  selected.push({...work}); render(); $('search-status').textContent=`Added ${work.title}. Give your rating below.`;
}
$('search-form').addEventListener('submit',e=>{e.preventDefault(); attempt(async()=>{
  found=(await api('search?q='+encodeURIComponent($('query').value)+'&domain='+$('domain').value)).items;
  $('search-status').textContent=found.length?`${found.length} matches shown. Check the title, artist and year.`:'No matches. Try a shorter title or add the missing work below.';
  $('results').innerHTML=found.map((w,i)=>`<article><p class="eyebrow">${labels[w.domain]} · ${esc(w.year)}</p><h3>${esc(w.title)}</h3><p class="small">${esc(w.creators||w.genres||'')}</p><button class="secondary" type="button" data-add="${i}">I know this work</button></article>`).join('');
  document.querySelectorAll('[data-add]').forEach(b=>b.addEventListener('click',()=>add(found[Number(b.dataset.add)])));
});});
$('manual-form').addEventListener('submit',e=>{e.preventDefault(); const title=$('manual-title').value.trim(); if(title)add({id:null,title,domain:$('manual-domain').value});});
$('profile').addEventListener('submit',e=>{e.preventDefault(); attempt(async()=>{
  capture(); const works=selected.map(w=>({id:w.id||null,title:w.title,domain:w.domain,familiarity:w.familiarity,liking:Number(w.liking),reason:w.reason}));
  const d=await api('profiles',{works}); profileToken=d.token; $('saved').textContent=d.message; $('download').hidden=false;
});});
$('export').addEventListener('click',()=>attempt(async()=>{
  const d=await api('profiles/'+profileToken); const u=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}));
  const a=document.createElement('a'); a.href=u; a.download='recros-familiar-starting-points.json'; a.click(); URL.revokeObjectURL(u);
}));
