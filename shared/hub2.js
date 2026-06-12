/* SDR hub v2: company search, persona filter, one-click copy. Overrides hub() from app.js. */
function hub(data){
  document.title='CommerceNext NYC \u2014 Prospect Assets \u00b7 Triple Whale';
  const E=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  const slugs=data.order.slice().sort((a,b)=>data.contacts[a].company.localeCompare(data.contacts[b].company)||data.contacts[a].name.localeCompare(data.contacts[b].name));
  const personas=[...new Set(slugs.map(s=>data.contacts[s].persona))].sort();
  const st=document.createElement('style');
  st.textContent='.tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 16px}'
   +'.tools input{flex:1;min-width:230px;background:rgba(236,246,255,.06);border:1px solid var(--line);border-radius:11px;padding:11px 15px;color:#fff;font:inherit;font-size:14px;outline:none}'
   +'.tools input:focus{border-color:var(--blue)}'
   +'.tools input::placeholder{color:var(--mist)}'
   +'.tools select{background:rgba(236,246,255,.06);border:1px solid var(--line);border-radius:11px;padding:11px 13px;color:#fff;font:inherit;font-size:13.5px;outline:none}'
   +'.tools select option{color:#0B1A33;background:#fff}'
   +'.cnt{font-size:12.5px;color:var(--mist);white-space:nowrap}'
   +'.copybtn{background:rgba(12,112,242,.16);border:1px solid rgba(12,112,242,.5);border-radius:9px;color:#fff;font:inherit;font-size:12.5px;font-weight:600;padding:7px 13px;cursor:pointer;white-space:nowrap;transition:.15s}'
   +'.copybtn:hover{background:rgba(12,112,242,.32)}'
   +'.copybtn.ok{background:rgba(22,163,74,.25);border-color:rgba(22,163,74,.65)}'
   +'.copyall{background:none;border:1px solid var(--line);border-radius:11px;color:var(--sky);font:inherit;font-size:12.5px;font-weight:600;padding:11px 14px;cursor:pointer;white-space:nowrap}'
   +'.copyall:hover{border-color:var(--blue)}'
   +'.norows{padding:30px;text-align:center;color:var(--mist);border:1px dashed var(--line);border-radius:13px}';
  document.head.appendChild(st);
  const rows=slugs.map(s=>{const c=data.contacts[s];const url=new URL(s+'/',location.href).href;
    const q=(c.company+' '+c.name+' '+c.title+' '+c.persona+' '+(c.domain||'')).toLowerCase();
    return '<a class="row" href="'+s+'/" data-q="'+E(q)+'" data-p="'+E(c.persona)+'" data-url="'+E(url)+'" data-co="'+E(c.company)+'">'
     +'<div class="l"><img src="https://www.google.com/s2/favicons?domain='+c.domain+'&sz=128" style="height:22px;width:22px;border-radius:5px;background:#fff;padding:1.5px" alt="">'
     +'<div><b>'+E(c.company)+'</b><span>'+E(c.name)+' \u00b7 '+E(c.title)+'</span></div></div>'
     +'<div class="r"><span class="pers">'+E(c.persona)+'</span><button class="copybtn" type="button" data-url="'+E(url)+'">Copy link</button><span class="go">Open \u2192</span></div></a>';}).join('');
  document.body.innerHTML='<div class="hero"><div class="wrap"><div class="lockup"><img class="twl" src="'+TW_LOGO+'"></div>'
   +'<div class="prep">Internal SDR hub \u2014 not for distribution</div>'
   +'<h1>CommerceNext NYC \u00b7 <em>Prospect assets</em></h1>'
   +'<p class="sub">Search by company, copy the link, drop it in your sequence. Every linked page is customer-facing and safe to share as-is.</p></div></div>'
   +'<div class="wrap"><div class="tools">'
   +'<input id="q" type="search" placeholder="Search company, name, or title\u2026" autocomplete="off" autofocus>'
   +'<select id="pf"><option value="">All personas</option>'+personas.map(p=>'<option>'+E(p)+'</option>').join('')+'</select>'
   +'<button class="copyall" id="ca" type="button">Copy all shown</button>'
   +'<span class="cnt" id="cnt"></span></div>'
   +'<section id="rows">'+rows+'<div class="norows" id="nr" style="display:none">No matches \u2014 check spelling or clear the persona filter.</div></section></div>'
   +'<footer><div class="wrap">This hub page is internal. Links unfurl with a branded preview card when pasted in LinkedIn, email, or Slack.</div></footer>';
  const q=document.getElementById('q'),pf=document.getElementById('pf'),cnt=document.getElementById('cnt'),nr=document.getElementById('nr');
  function apply(){const t=q.value.trim().toLowerCase(),p=pf.value;let n=0;
    document.querySelectorAll('#rows .row').forEach(r=>{const ok=(!t||r.dataset.q.indexOf(t)>-1)&&(!p||r.dataset.p===p);r.style.display=ok?'':'none';if(ok)n++});
    cnt.textContent=n+' of '+slugs.length;nr.style.display=n?'none':'';}
  q.addEventListener('input',apply);pf.addEventListener('change',apply);apply();
  function copyText(t,done){if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,()=>fallback(t,done));}else fallback(t,done);}
  function fallback(t,done){const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();try{document.execCommand('copy')}catch(e){}document.body.removeChild(ta);done();}
  document.body.addEventListener('click',e=>{const b=e.target.closest('.copybtn');if(b){e.preventDefault();e.stopPropagation();
    copyText(b.dataset.url,()=>{b.textContent='Copied \u2713';b.classList.add('ok');setTimeout(()=>{b.textContent='Copy link';b.classList.remove('ok')},1400)});return;}
    if(e.target.closest('#ca')){const vis=[...document.querySelectorAll('#rows .row')].filter(r=>r.style.display!=='none');
      const txt=vis.map(r=>r.dataset.co+'\t'+r.dataset.url).join('\n');const ca=document.getElementById('ca');
      copyText(txt,()=>{ca.textContent='Copied '+vis.length+' \u2713';setTimeout(()=>{ca.textContent='Copy all shown'},1600)});}});
}
