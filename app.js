const DATA = window.__DATA__;
let ADMIN = false;
let CURRENT = DATA.articles[0];

function el(sel){ return document.querySelector(sel); }
function els(sel){ return [...document.querySelectorAll(sel)]; }
function normalize(s){ return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,''); }

function expandQuery(q){
  const t = normalize(q).split(/\s+/).filter(Boolean);
  const out = new Set();
  for(const tok of t){
    out.add(tok);
    const syn = DATA.synonyms[tok];
    if(syn) syn.forEach(v => out.add(normalize(v)));
  }
  return [...out];
}

function score(a, terms){
  if(!terms.length) return 1;
  let s = 0; const t = normalize(a.title), c = normalize(a.content), g = normalize((a.tags||[]).join(' '));
  for(const x of terms){
    if(t.includes(x)) s += 5;
    if(g.includes(x)) s += 2;
    if(c.includes(x)) s += 1;
  }
  return s;
}

function search(q){
  const terms = expandQuery(q);
  return DATA.articles.map(a => ({a, score: score(a, terms)}))
    .filter(x => x.score>0)
    .sort((x,y) => y.score - x.score || x.a.title.localeCompare(y.a.title))
    .map(x => x.a);
}

function renderArticle(a){
  CURRENT = a;
  el('#art-title').textContent = a.title;
  el('#art-meta').textContent = `${a.category} • ${a.type.charAt(0).toUpperCase()+a.type.slice(1)} • Tags : ${(a.tags||[]).join(', ') || '—'}`;
  const links = (a.links||[]).map(slug => {
    const b = DATA.articles.find(x => x.slug===slug);
    return b ? `<a href="#" data-goto="${b.slug}">${b.title}</a>` : '';
  }).join(', ');
  el('#art-content').innerHTML = `<p>${a.content}</p>` + (links? `<p><b>Liens internes</b> : ${links}.</p>` : '');
  bindInternalLinks();
  el('#breadcrumbs').textContent = `Catégories › ${a.category}`;
}

function bindInternalLinks(){
  el('#art-content').querySelectorAll('a[data-goto]').forEach(a => {
    a.addEventListener('click', (e)=>{
      e.preventDefault();
      const slug = a.getAttribute('data-goto');
      const b = DATA.articles.find(x => x.slug===slug);
      if(b){ renderArticle(b); closeSuggest(); }
    });
  });
}

function openSuggest(items){
  const box = el('#suggest');
  box.innerHTML = items.slice(0,12).map(a => `
    <div class="row" data-slug="${a.slug}">
      <div>
        <div><b>${a.title}</b></div>
        <div class="meta">${a.category} • ${a.type}</div>
      </div>
      <div class="meta">${(a.tags||[]).slice(0,3).join(', ')}</div>
    </div>
  `).join('');
  box.classList.remove('hidden');
  box.querySelectorAll('.row').forEach(r => {
    r.addEventListener('click', ()=>{
      const slug = r.getAttribute('data-slug');
      const a = DATA.articles.find(x => x.slug===slug);
      if(a){ renderArticle(a); closeSuggest(); }
    });
  });
}
function closeSuggest(){ el('#suggest').classList.add('hidden'); }

function bindSearch(){
  const q = el('#q');
  el('#btn').addEventListener('click', ()=>{
    const items = search(q.value);
    openSuggest(items);
  });
  q.addEventListener('input', ()=>{
    if(q.value.trim().length===0){ closeSuggest(); return; }
    openSuggest(search(q.value));
  });
  document.addEventListener('click', (e)=>{
    if(!el('#suggest').contains(e.target) && e.target !== q) closeSuggest();
  });
}

function bindNav(){
  els('.navbtn').forEach(b => b.addEventListener('click', ()=>{
    els('.navbtn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    const tab = b.getAttribute('data-tab');
    let a = CURRENT;
    if(tab==='categories'){ a = DATA.articles.find(x=>x.type==='process') || DATA.articles[0]; }
    if(tab==='outils'){ a = DATA.articles.find(x=>x.type==='outil') || DATA.articles[0]; }
    if(tab==='diagnostic'){ a = DATA.articles.find(x=>x.type==='diagnostic') || DATA.articles[0]; }
    if(tab==='mails'){ a = DATA.articles.find(x=>x.type==='mail') || DATA.articles[0]; }
    renderArticle(a);
  }));
}

function bindAdmin(){
  const chk = el('#adminToggle');
  const edit = el('#editBtn');
  chk.addEventListener('change', ()=>{
    ADMIN = chk.checked;
    edit.disabled = !ADMIN;
  });
  edit.addEventListener('click', ()=>{
    if(!ADMIN) return;
    alert('Démo : ouverture de l’éditeur pour « '+ CURRENT.title +' ».');
  });
}

function init(){
  bindNav();
  bindSearch();
  bindAdmin();
  renderArticle(CURRENT);
}
init();