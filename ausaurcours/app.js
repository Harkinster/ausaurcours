// ===============================
// Au SAURcours ! - app.js
// ===============================
const API = window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : '/api';

// Éléments DOM
const q = document.getElementById("q");
const btn = document.getElementById("btn");
const suggest = document.getElementById("suggest");
const artTitle = document.getElementById("art-title");
const artMeta = document.getElementById("art-meta");
const artContent = document.getElementById("art-content");
const breadcrumbs = document.getElementById("breadcrumbs");
const editBtn = document.getElementById("editBtn");
const infoBtn = document.getElementById("infoBtn");
const adminToggle = document.getElementById("adminToggle");
const logoutBtnMain = document.getElementById("logoutBtnMain");
const newBtn = document.getElementById("newBtn");
const createPanel = document.getElementById("create-panel");
const editPanel = document.getElementById("edit-panel");

let currentArticle = null;
let lastHits = [];
let debounceId = null;

function showSuggest() { suggest.classList.remove("hidden"); }
function hideSuggest() { suggest.classList.add("hidden"); suggest.innerHTML = ""; }
function hideRecent() { try { const r = document.getElementById('recent'); if (r) r.style.display = 'none'; } catch {} }

// ---- Fonctions utilitaires ----
function getCurrentUser() {
  try { return JSON.parse(localStorage.getItem('user') || 'null'); }
  catch { return null; }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[m]));
}

function renderContent(txt) {
  return txt.split(/\n{2,}/)
    .map(p => `<p>${escapeHtml(p).replace(/\n/g, "<br/>")}</p>`)
    .join("\n");
}

// ---- Recherche ----
async function search(query) {
  if (!query || query.trim().length < 2) {
    hideSuggest();
    return;
  }
  suggest.innerHTML = `<div class="suggest-item muted">⏳ Recherche…</div>`;
  showSuggest();
  try {
    let data = null;
    let r = await fetch(`${API}/search?q=${encodeURIComponent(query.trim())}`);
    if (!r.ok) {
      const all = await fetch(`${API}/articles`);
      if (!all.ok) throw new Error(`HTTP ${r.status}`);
      const items = await all.json();
      const ql = query.trim().toLowerCase();
      lastHits = items.filter(a =>
        (a.title || '').toLowerCase().includes(ql) ||
        (a.content || '').toLowerCase().includes(ql)
      ).slice(0, 20);
    } else {
      data = await r.json();
      lastHits = data?.hits || [];
    }
    if (!lastHits.length) {
      suggest.innerHTML = `<div class="suggest-item muted">Aucun résultat pour « ${escapeHtml(query)} »</div>`;
      return;
    }
    suggest.innerHTML = lastHits.map(h => {
      const tags = (h.tags || []).map(t => `#${t}`).join(" ");
      return `
        <div class="suggest-item" data-slug="${h.slug}">
          <div class="si-title">${escapeHtml(h.title)}</div>
          <div class="si-meta">${h.category || "—"} · ${escapeHtml(tags)}</div>
          <div class="si-snippet">${escapeHtml((h.snippet || "").slice(0,160))}</div>
        </div>`;
    }).join("");
  } catch (e) {
    suggest.innerHTML = `<div class="suggest-item error">⚠️ Erreur : ${escapeHtml(e.message)}</div>`;
  }
}

// ---- Ouverture d’un article ----
async function openArticle(slug) {
  const r = await fetch(`${API}/articles/slug/${slug}`);
  const a = await r.json();
  hideRecent();
  artTitle.textContent = a.title;
  artMeta.innerHTML = `${a.category} • ${a.tags.join(', ')} • par ${a.author}`;
  artContent.innerHTML = a.content;
  currentArticle = a;
  editBtn.onclick = () => openRichEditor(a);
  editBtn.disabled = false;
  mermaid.run();
}

// ---- Création d’un article ----
function openCreateArticle() {
  const modal = document.createElement('div');
  modal.className = 'modal show';
  modal.innerHTML = `
    <div class="modal-content" style="width:90%;max-width:860px;">
      <h3>Nouveau contenu</h3>
      <div class="editor">
        <input id="na-title" placeholder="Titre">
        <input id="na-slug" placeholder="Slug">
        <input id="na-category" placeholder="Catégorie">
        <input id="na-tags" placeholder="Tags (séparés par des virgules)">
        <textarea id="na-content" style="min-height:240px"></textarea>
      </div>
      <div class="bar">
        <button id="na-save">Créer</button>
        <button id="na-cancel">Annuler</button>
      </div>
    </div>`;
  document.body.appendChild(modal);

  modal.querySelector('#na-cancel').onclick = () => modal.remove();
  modal.querySelector('#na-save').onclick = async () => {
    const title = modal.querySelector('#na-title').value.trim();
    const slug = modal.querySelector('#na-slug').value.trim();
    const category_slug = modal.querySelector('#na-category').value.trim() || null;
    const tags = (modal.querySelector('#na-tags').value || '')
      .split(',').map(s => s.trim()).filter(Boolean);
    const content = tinymce.get('na-content').getContent();
    if (!title || !slug) return alert('Titre et slug requis.');
    const jwt = localStorage.getItem('jwt');
    try {
      const res = await fetch(`${API}/articles/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(jwt ? { 'Authorization': 'Bearer ' + jwt } : {})
        },
        body: JSON.stringify({ title, slug, category_slug, tags, content })
      });
      if (!res.ok) throw new Error(await res.text());
      await res.json();
      modal.remove();
      openArticle(slug);
    } catch (e) {
      alert('Erreur création : ' + e.message);
    }
  };
}

// ---- Éditeur riche ----
function openRichEditor(article) {
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.cssText = `
    display:flex;position:fixed;top:0;left:0;right:0;bottom:0;
    background:rgba(0,0,0,0.5);z-index:1000;justify-content:center;align-items:center;`;
  document.body.style.overflow = 'hidden';

  modal.innerHTML = `
    <div style="width:95%;max-width:1000px;background:white;border-radius:8px;padding:20px;">
      <h3>Éditer l'article</h3>
      <input id="ed-title" value="${escapeHtml(article.title||'')}" placeholder="Titre">
      <input id="ed-slug" value="${escapeHtml(article.slug||'')}" placeholder="Slug">
      <input id="ed-category" value="${escapeHtml(article.category||'')}" placeholder="Catégorie">
      <input id="ed-tags" value="${(article.tags||[]).join(', ')}" placeholder="Tags">
      <textarea id="ed-content" style="min-height:400px;">${article.content || ''}</textarea>
      <div style="margin-top:10px;text-align:right;">
        <button id="ed-cancel">Annuler</button>
        <button id="ed-save">Enregistrer</button>
      </div>
    </div>`;
  document.body.appendChild(modal);

  tinymce.init({
    selector: '#ed-content',
    height: 500,
    menubar: true,
    plugins: [
      'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview', 'anchor',
      'searchreplace', 'visualblocks', 'code', 'fullscreen',
      'insertdatetime', 'media', 'table', 'help', 'wordcount'
    ],
    toolbar: 'undo redo | bold italic | alignleft aligncenter alignright | bullist numlist | image code',
    images_upload_url: '/api/upload-image',
    convert_urls: false,
    promotion: false
  });

  modal.querySelector('#ed-cancel').onclick = () => {
    tinymce.get('ed-content').destroy();
    modal.remove();
    document.body.style.overflow = '';
  };

  modal.querySelector('#ed-save').onclick = async () => {
    const title = document.getElementById('ed-title').value.trim();
    const slug = document.getElementById('ed-slug').value.trim();
    const category = document.getElementById('ed-category').value.trim();
    const tags = (document.getElementById('ed-tags').value || '')
      .split(',').map(s => s.trim()).filter(Boolean);
    const content = tinymce.get('ed-content').getContent();
    if (!title || !slug) return alert('Titre et slug obligatoires');
    const jwt = localStorage.getItem('jwt');
    try {
      const res = await fetch(`${API}/articles/${article.slug}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(jwt ? { 'Authorization': 'Bearer ' + jwt } : {})
        },
        body: JSON.stringify({ title, slug, category_slug: category || null, tags, content })
      });
      if (!res.ok) throw new Error(await res.text());
      tinymce.get('ed-content').destroy();
      modal.remove();
      openArticle(slug);
    } catch (e) {
      alert('Erreur sauvegarde : ' + e.message);
    }
  };
}

// ---- Événements généraux ----
q.addEventListener("input", () => {
  clearTimeout(debounceId);
  debounceId = setTimeout(() => search(q.value), 180);
});
btn.addEventListener("click", () => search(q.value));

suggest.addEventListener("click", (e) => {
  const item = e.target.closest(".suggest-item[data-slug]");
  if (item) {
    openArticle(item.dataset.slug);
    hideSuggest();
    hideRecent();
  }
});

q.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && lastHits.length) openArticle(lastHits[0].slug);
  else if (e.key === "Escape") hideSuggest();
});

window.addEventListener("load", async () => {
  try {
    const r = await fetch(`${API}/health`);
    const j = await r.json();
    if (!j.ok) console.warn("API non OK", j);
  } catch {
    console.warn("API inaccessible");
  }
});
