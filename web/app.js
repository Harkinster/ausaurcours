function el(id){ return document.getElementById(id); }

/* ---------- API helpers ---------- */
async function apiSearch(q, cats){
  const url = new URL('/api/search', window.location.origin);
  url.searchParams.set('q', q);
  (cats||[]).forEach(c=>url.searchParams.append('categories', c));
  const r = await fetch(url.toString());
  return r.json();
}
async function apiAdmin(path, method='GET', body=null){
  const headers = {'Content-Type':'application/json'};
  const tok = localStorage.getItem('ausaur_admin_token') || '';
  if(tok) headers['Authorization'] = 'Bearer '+tok;
  const endpoint = path.startsWith('/api') ? path : '/api'+path;
  const r = await fetch(endpoint, {method, headers, body: body?JSON.stringify(body):null});
  if(!r.ok){ const t = await r.text(); throw new Error(`${r.status} ${t}`); }
  return r.json();
}
async function getBySlug(slug){
  const r = await fetch(`/api/articles/${encodeURIComponent(slug)}`);
  if(!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

/* ---------- Domaines ---------- */
const DOMAINES = {
  abonnement: { 
    cats: ["Abonnement","Résiliation","Paiement","Coordonnées","Dématérialisation","Intervention","Index","Courriers","Processus"],
    q: "abonnement resiliation paiement coordonnees dematerialisation intervention index"
  },
  diagnostic: { 
    cats: ["Diagnostic","Processus","Index"], 
    q: "diagnostic triage arbre requete anomalie"
  },
  mails: { 
    cats: ["Mails","Courriers"], 
    q: "email mail courrier modele reponse"
  }
};

/* ---------- Rendu ---------- */
function renderResults(items){
  const box = el('results');
  if(!items.length){ box.innerHTML = ""; return; }
  box.innerHTML = items.map(a=>`
    <div class="card" data-slug="${a.slug}">
      <h3>${a.title}</h3>
      <div class="meta">${a.category||"—"} • ${a.type||"process"}</div>
      <div>${(a.content||"").slice(0,160)}…</div>
    </div>
  `).join('');
  box.querySelectorAll('.card').forEach(c=>{
    c.addEventListener('click', async ()=>{
      const slug = c.getAttribute('data-slug');
      try{
        const doc = await getBySlug(slug);
        renderArticle(doc);
      }catch(e){ alert("Impossible d’ouvrir l’article: "+e.message); }
    });
  });
}

function renderArticle(a){
  const isAdmin = !!localStorage.getItem('ausaur_admin_token');
  const links = (a.links||[]).map(s=>`<a href="#" data-jump="${s}">${s}</a>`).join(', ');
  el('article').innerHTML = `
    <article class="article">
      <div style="display:flex;align-items:center;gap:8px;justify-content:space-between">
        <div>
          <h1 style="margin:0">${a.title||''}</h1>
          <div class="meta">${a.category||'—'} • ${a.type||'process'}</div>
        </div>
        ${isAdmin ? `<button id="btnEdit" data-id="${a.id}">Modifier</button>` : ``}
      </div>
      <p>${(a.content||'').replace(/\n/g,'<br>')}</p>
      ${links ? `<p><b>Liens internes</b> : ${links}</p>` : ``}
    </article>`;
  document.querySelectorAll('[data-jump]').forEach(x=>{
    x.addEventListener('click', async (e)=>{
      e.preventDefault();
      try{ renderArticle(await getBySlug(x.getAttribute('data-jump'))); }
      catch(err){ alert("Lien interne introuvable : "+err.message); }
    });
  });
  const btnEdit = document.getElementById('btnEdit');
  if(btnEdit){ btnEdit.onclick = ()=> openEditor(a); }
}

/* ---------- Éditeur ---------- */
const CATEGORIES = ["Abonnement","Résiliation","Paiement","Coordonnées","Dématérialisation","Intervention","Index","Courriers","Diagnostic","Outils","Mails","Processus"];
const TYPES = ["process","mail","outil"];
function slugify(s){
  return (s||"").toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .replace(/\s+/g,'-').replace(/[^a-z0-9\-]/g,'').replace(/\-+/g,'-').replace(/^\-|\-$/g,'');
}
function chipsToArray(v){ return (v||"").split(",").map(x=>x.trim()).filter(Boolean); }

function openEditor(a){
  const isNew = !a;
  a = a || {title:"", slug:"", content:"", category:"Processus", type:"process", tags:[], links:[]};
  el('article').innerHTML = `
    <form id="artForm" class="article">
      <h1 style="margin:0 0 8px">${isNew ? "Créer un article" : "Modifier l’article"}</h1>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <label>Title<br><input id="f_title" value="${a.title||""}" required></label>
        <label>Slug<br><input id="f_slug" value="${a.slug||""}" required></label>
        <label>Catégorie<br>
          <select id="f_cat">${CATEGORIES.map(c=>`<option ${a.category===c?'selected':''}>${c}</option>`).join('')}</select>
        </label>
        <label>Type<br>
          <select id="f_type">${TYPES.map(t=>`<option ${a.type===t?'selected':''}>${t}</option>`).join('')}</select>
        </label>
        <label>Tags (séparés par des virgules)<br><input id="f_tags" value="${(a.tags||[]).join(', ')}" placeholder="ex: abonnement, mensualisation, iban"></label>
        <label>Liens internes (slugs, virgules)<br><input id="f_links" value="${(a.links||[]).join(', ')}" placeholder="ex: creer-abonnement, resiliation"></label>
      </div>
      <label>Contenu<br><textarea id="f_content" rows="14">${a.content||""}</textarea></label>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button type="submit">${isNew?"Créer":"Enregistrer"}</button>
        <button type="button" id="f_cancel">Annuler</button>
        ${!isNew?'<button type="button" id="f_delete" style="margin-left:auto;background:#ef4444;color:#fff">Supprimer</button>':''}
      </div>
    </form>`;
  const ti = document.getElementById('f_title');
  const si = document.getElementById('f_slug');
  ti.addEventListener('input', ()=>{ if(!a.slug) si.value = slugify(ti.value); });
  document.getElementById('f_cancel').onclick = ()=>{ if(isNew){ el('article').innerHTML=""; } else { renderArticle(a);} };

  const form = document.getElementById('artForm');
  form.onsubmit = async (e)=>{
    e.preventDefault();
    const payload = {
      title: el('f_title').value.trim(),
      slug: el('f_slug').value.trim() || slugify(el('f_title').value),
      category: el('f_cat').value,
      type: el('f_type').value,
      tags: chipsToArray(el('f_tags').value),
      links: chipsToArray(el('f_links').value),
      content: el('f_content').value
    };
    try{
      if(isNew){
        const res = await apiAdmin('/api/api/api/api/admin/articles','POST', payload);     // { ok, id, slug }
        const art = await getBySlug(res.slug);                               // Relit par slug final
        renderArticle(art);
      }else{
        await apiAdmin(`/api/api/api/api/admin/articles/${a.id}`,'PUT', payload);
        const art = await getBySlug(payload.slug || a.slug);                 // Slug a pu changer
        renderArticle(art);
      }
    }catch(err){
      const msg = String(err.message||err);
      if(msg.startsWith("409")) alert("Slug déjà utilisé — modifie le champ « Slug ».");
      else alert("Erreur: "+msg);
    }
  };

  const del = document.getElementById('f_delete');
  if(del){
    del.onclick = async ()=>{
      if(confirm("Supprimer cet article ?")){
        try{ await apiAdmin(`/api/api/api/api/admin/articles/${a.id}`,'DELETE'); el('article').innerHTML=""; alert("Supprimé"); }
        catch(err){ alert("Erreur: "+err.message); }
      }
    };
  }
}

/* ---------- Suggestions recherche ---------- */
function suggestRow(a){
  return `<div class="row" data-slug="${a.slug}">
    <div><div><b>${a.title}</b></div><div class="meta">${a.category||'—'} • ${a.type||'process'}</div></div>
    <div class="meta">${(a.tags||[]).slice(0,3).join(', ')}</div>
  </div>`;
}
function openSuggest(items){
  const box = el('suggest');
  if(!items.length){ box.classList.add('hidden'); box.innerHTML=''; return; }
  box.innerHTML = items.slice(0,12).map(suggestRow).join('');
  box.classList.remove('hidden');
  box.querySelectorAll('.row').forEach(r=>{
    r.addEventListener('click', async ()=>{
      const slug = r.getAttribute('data-slug');
      try{ renderArticle(await getBySlug(slug)); closeSuggest(); }
      catch(e){ alert("Impossible d’ouvrir l’article: "+e.message); }
    });
  });
}
function closeSuggest(){ const s=el('suggest'); if(s) s.classList.add('hidden'); }

/* ---------- Orchestrateur ---------- */
async function runSearch(){
  const q = el('q').value.trim();
  if(q.length<3){ closeSuggest(); return; }
  try{
    const res = await apiSearch(q);
    openSuggest(res.hits||[]);
  }catch(e){ console.error(e); }
}
async function openDomaine(dom){
  const d = DOMAINES[dom];
  if(!d){
    el('results').innerHTML = '';
    el('article').innerHTML = '';
    return;
  }
  const res = await apiSearch(d.q, d.cats);
  closeSuggest();
  el('article').innerHTML = '';
  renderResults(res.hits||[]);
}

(function init(){
  const q = el('q');
  if(q){
    q.addEventListener('input', runSearch);
    const btn = document.getElementById('btn');
    if(btn) btn.addEventListener('click', runSearch);
  }
  document.addEventListener('click', (e)=>{
    const s = el('suggest');
    if(s && !s.contains(e.target) && e.target!==q) closeSuggest();
  });
  document.querySelectorAll('#nav-dom a').forEach(a=>{
    a.addEventListener('click', (e)=>{
      e.preventDefault();
      document.querySelectorAll('#nav-dom a').forEach(x=>x.classList.remove('active'));
      a.classList.add('active');
      const dom = a.getAttribute('data-dom');
      if(dom==='home'){ el('results').innerHTML=''; el('article').innerHTML=''; return; }
      openDomaine(dom);
    });
  });
  const btnAdmin = document.getElementById('btnAdmin');
  const btnCreate = document.getElementById('btnCreate');
  function refreshAdminUI(){
    const on = !!localStorage.getItem('ausaur_admin_token');
    if(btnCreate) btnCreate.classList.toggle('hidden', !on);
  }
  if(btnAdmin){
    btnAdmin.onclick = ()=>{
      const cur = localStorage.getItem('ausaur_admin_token') || '';
      const tok = prompt(cur? "Token admin (laisser vide pour désactiver)":"Entrer le token admin", cur||"");
      if(tok===null) return;
      if(tok.trim()){ localStorage.setItem('ausaur_admin_token', tok.trim()); }
      else{ localStorage.removeItem('ausaur_admin_token'); }
      refreshAdminUI();
    };
  }
  if(btnCreate){ btnCreate.onclick = ()=> openEditor(null); }
  refreshAdminUI();
})();
