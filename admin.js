// Configuration de base de l'API
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = isLocalhost ? 'http://localhost:8000' : window.location.protocol + '//' + window.location.host;
const API_PREFIX = '/api';
const $ = (sel, root=document) => root.querySelector(sel);
const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

// Fonction pour obtenir les en-têtes d'authentification
function authHeaders() {
  const jwt = localStorage.getItem('jwt');
  const headers = { 'Content-Type': 'application/json' };
  if (jwt) headers['Authorization'] = `Bearer ${jwt}`;
  return headers;
}

// Fonction utilitaire pour les appels API
async function api(endpoint, options = {}) {
  const url = `${API_BASE}${API_PREFIX}${endpoint}`;
  const headers = { ...authHeaders(), ...(options.headers || {}) };
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include' // Important pour les cookies de session
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.message || 'Une erreur est survenue');
      error.status = response.status;
      error.data = errorData;
      throw error;
    }

    // Si la réponse est vide (comme pour les réponses 204 No Content)
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error(`Erreur API [${endpoint}]:`, error);
    throw error;
  }
}

async function loadUsers() {
  try {
    // Désactivé temporairement jusqu'à l'implémentation du backend
    $('#user-list').innerHTML = `
      <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> La gestion des utilisateurs sera disponible prochainement.
      </div>`;
  } catch (error) {
    console.error('Erreur lors du chargement des utilisateurs:', error);
    $('#user-list').innerHTML = `
      <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle"></i> Impossible de charger la liste des utilisateurs.
      </div>`;
  }
}

async function loadComments() {
  try {
    // Désactivé temporairement jusqu'à l'implémentation du backend
    $('#comment-list').innerHTML = `
      <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> La modération des commentaires sera disponible prochainement.
      </div>`;
  } catch (error) {
    console.error('Erreur lors du chargement des commentaires:', error);
    $('#comment-list').innerHTML = `
      <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle"></i> Impossible de charger les commentaires en attente.
      </div>`;
  }
}

async function loadAudit() {
  try {
    // Désactivé temporairement jusqu'à l'implémentation du backend
    $('#audit-list').innerHTML = `
      <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> Le journal d'audit sera disponible prochainement.
      </div>`;
  } catch (error) {
    console.error('Erreur lors du chargement du journal d\'audit:', error);
    $('#audit-list').innerHTML = `
      <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle"></i> Impossible de charger le journal d'audit.
      </div>`;
  }
}

// Fonctions pour gérer les commentaires (désactivées pour l'instant)
window.approve = id => {
  console.log('Approuver le commentaire', id);
  // Implémentation à venir
};

window.reject = id => {
  console.log('Rejeter le commentaire', id);
  // Implémentation à venir
};

// Fonctions pour gérer les articles
async function loadArticles() {
  const articlesList = document.getElementById('articles-list');
  if (!articlesList) {
    console.error('Élément articles-list non trouvé');
    return;
  }

  try {
    console.log('Chargement des articles...');
    // Afficher l'indicateur de chargement
    articlesList.innerHTML = `
      <tr>
        <td colspan="5" class="text-center">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Chargement...</span>
          </div>
        </td>
      </tr>`;

    // Utilisation de la fonction api pour gérer l'authentification et les erreurs
    const articles = await api('/articles');
    console.log('Articles chargés:', articles);
    
    if (!articles || articles.length === 0) {
      articlesList.innerHTML = `
        <tr>
          <td colspan="5" class="text-center">
            <div class="alert alert-info mb-0">
              <i class="fas fa-info-circle"></i> Aucun article trouvé. Commencez par en créer un nouveau.
            </div>
          </td>
        </tr>`;
      return;
    }
    
    // Formater les articles avec un gestionnaire de clic
    articlesList.innerHTML = articles.map(article => `
      <tr class="article-row" data-id="${article.id}">
        <td>${article.id}</td>
        <td>
          <div class="d-flex align-items-center">
            <i class="bi bi-file-text me-2"></i>
            <div>
              <div class="fw-bold">${escapeHtml(article.title)}</div>
              <small class="text-muted">${article.slug || 'sans-slug'}</small>
            </div>
          </div>
        </td>
        <td>
          ${article.category ? 
            `<span class="badge bg-primary">${escapeHtml(article.category)}</span>` : 
            '<span class="text-muted">Aucune</span>'
          }
        </td>
        <td>
          <div class="d-flex flex-column">
            <span>${formatDate(article.created_at)}</span>
            <small class="text-muted">par ${article.author || 'Inconnu'}</small>
          </div>
        </td>
        <td class="text-end">
          <div class="btn-group" role="group">
            <a href="/?edit=${article.id}" class="btn btn-sm btn-outline-primary" 
               data-bs-toggle="tooltip" title="Éditer">
              <i class="fas fa-edit"></i>
            </a>
            <button type="button" class="btn btn-sm btn-outline-danger delete-article" 
                    data-id="${article.id}" 
                    data-title="${escapeHtml(article.title)}"
                    data-bs-toggle="tooltip" 
                    title="Supprimer">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
    
    // Ajouter les gestionnaires d'événements pour les lignes d'articles
    document.querySelectorAll('.article-row').forEach(row => {
      row.addEventListener('click', (e) => {
        // Ne pas déclencher si on clique sur un bouton d'action
        if (e.target.closest('button, a, .btn, [data-bs-toggle]')) {
          return;
        }
        const articleId = row.dataset.id;
        showArticleDetail(articleId);
      });
      
      // Ajouter un effet de survol
      row.style.cursor = 'pointer';
    });
    
    // Initialiser les tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Ajouter les gestionnaires d'événements pour les boutons de suppression
    document.querySelectorAll('.delete-article').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation(); // Empêcher le déclenchement du clic sur la rangée
        const button = e.target.closest('button');
        const id = button.dataset.id;
        const title = button.dataset.title || 'cet article';
        deleteArticle(id, title);
      });
    });
    
    // Gestionnaire pour le bouton de retour à la liste
    const backToListBtn = document.getElementById('backToListBtn');
    if (backToListBtn) {
      backToListBtn.addEventListener('click', showArticleList);
    }
    
  } catch (error) {
    console.error('Erreur lors du chargement des articles:', error);
    const articlesList = document.getElementById('articles-list');
    if (articlesList) {
      articlesList.innerHTML = `<tr><td colspan="5" class="text-danger">Erreur: ${error.message}</td></tr>`;
    }
  }
}

async function deleteArticle(articleId, title = 'cet article') {
  // Vérifier si SweetAlert2 est disponible
  if (typeof Swal === 'undefined') {
    console.error('SweetAlert2 n\'est pas chargé');
    return;
  }

  // Demande de confirmation plus détaillée
  const confirmed = await Swal.fire({
    title: 'Confirmer la suppression',
    html: `Êtes-vous sûr de vouloir supprimer <strong>${escapeHtml(title)}</strong> ?<br>Cette action est irréversible.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#3085d6',
    confirmButtonText: 'Oui, supprimer',
    cancelButtonText: 'Annuler',
    reverseButtons: true,
    allowOutsideClick: () => !Swal.isLoading()
  });
  
  if (!confirmed.isConfirmed) return;
  
  const tbody = document.getElementById('articles-list');
  if (!tbody) {
    console.error('Élément tbody non trouvé');
    return;
  }
  
  const originalContent = tbody.innerHTML;
  
  try {
    // Afficher un indicateur de chargement
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Suppression en cours...</span>
          </div>
        </td>
      </tr>`;
    
    // Utilisation de la fonction api pour gérer l'authentification et les erreurs
    await api(`/articles/${articleId}`, { method: 'DELETE' });
    
    // Afficher un message de succès
    await Swal.fire({
      title: 'Supprimé !',
      text: 'L\'article a été supprimé avec succès.',
      icon: 'success',
      timer: 2000,
      showConfirmButton: false
    });
    
    // Recharger la liste des articles
    await loadArticles();
    
  } catch (error) {
    console.error('Erreur lors de la suppression:', error);
    
    // Restaurer le contenu original
    tbody.innerHTML = originalContent;
    
    // Afficher un message d'erreur plus détaillé
    const errorMessage = error.status === 403 
      ? 'Vous n\'avez pas les droits nécessaires pour effectuer cette action.'
      : error.status === 404 
        ? 'L\'article demandé n\'existe pas ou a déjà été supprimé.'
        : `Une erreur est survenue : ${error.message || 'Veuillez réessayer plus tard.'}`;
    
    await Swal.fire({
      title: 'Erreur',
      html: `<p>${errorMessage}</p>`,
      icon: 'error',
      confirmButtonColor: '#3085d6',
    });
  }
}

function showAlert(message, type = 'info') {
  const alert = document.createElement('div');
  alert.className = `alert alert-${type} alert-dismissible fade show`;
  alert.role = 'alert';
  alert.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  const container = document.querySelector('.admin-container');
  if (container) {
    container.prepend(alert);
    // Supprimer l'alerte après 5 secondes
    setTimeout(() => alert.remove(), 5000);
  }
}

// Fonctions pour gérer l'affichage des articles
async function showArticleDetail(articleId) {
  try {
    // Afficher l'indicateur de chargement
    const articleDetail = document.getElementById('article-detail');
    if (articleDetail) {
      articleDetail.innerHTML = `
        <div class="text-center my-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Chargement...</span>
          </div>
          <p class="mt-2">Chargement de l'article...</p>
        </div>`;
    }

    // Récupérer les détails de l'article depuis l'API
    const article = await api(`/articles/${articleId}`);
    
    if (!article) {
      throw new Error('Impossible de charger les détails de l\'article');
    }

    // Afficher les détails de l'article
    if (articleDetail) {
      articleDetail.innerHTML = `
        <h2 class="card-title">${escapeHtml(article.title)}</h2>
        <div class="text-muted mb-3">
          <small>Publié le ${formatDate(article.created_at)} par ${article.author || 'Inconnu'}</small>
          ${article.updated_at ? `<br><small>Mis à jour le ${formatDate(article.updated_at)}</small>` : ''}
        </div>
        ${article.category ? 
          `<p><span class="badge bg-primary">${escapeHtml(article.category)}</span></p>` : ''}
        <div class="article-content">
          ${article.content || '<p class="text-muted">Aucun contenu disponible.</p>'}
        </div>
        <div class="mt-4">
          <a href="/?edit=${article.id}" class="btn btn-primary me-2">
            <i class="fas fa-edit me-1"></i> Modifier
          </a>
          <button type="button" class="btn btn-outline-secondary" id="backToListBtn">
            <i class="fas fa-arrow-left me-1"></i> Retour à la liste
          </button>
        </div>`;
      
      // Ajouter le gestionnaire d'événement pour le bouton de retour
      const backBtn = document.getElementById('backToListBtn');
      if (backBtn) {
        backBtn.addEventListener('click', showArticleList);
      }
    }

    // Afficher le conteneur de détail et masquer la liste
    const listContainer = document.getElementById('articles-list-container');
    const detailContainer = document.getElementById('article-detail-container');
    const backToListBtn = document.getElementById('backToListBtn');
    
    if (listContainer) listContainer.style.display = 'none';
    if (detailContainer) detailContainer.style.display = 'block';
    if (backToListBtn) backToListBtn.style.display = 'inline-block';
    
  } catch (error) {
    console.error('Erreur lors du chargement des détails de l\'article:', error);
    
    const articleDetail = document.getElementById('article-detail');
    if (articleDetail) {
      articleDetail.innerHTML = `
        <div class="alert alert-danger">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Erreur lors du chargement de l'article : ${error.message}
        </div>
        <button class="btn btn-secondary mt-3" id="backToListBtn">
          <i class="fas fa-arrow-left me-1"></i> Retour à la liste
        </button>`;
      
      // Ajouter le gestionnaire d'événement pour le bouton de retour
      const backBtn = document.getElementById('backToListBtn');
      if (backBtn) {
        backBtn.addEventListener('click', showArticleList);
      }
    }
  }
}

function showArticleList() {
  // Afficher la liste et masquer le détail
  const listContainer = document.getElementById('articles-list-container');
  const detailContainer = document.getElementById('article-detail-container');
  const backToListBtn = document.getElementById('backToListBtn');
  
  if (listContainer) listContainer.style.display = 'block';
  if (detailContainer) detailContainer.style.display = 'none';
  if (backToListBtn) backToListBtn.style.display = 'none';
  
  // Faire défendre jusqu'en haut de la page
  window.scrollTo(0, 0);
}

// Fonctions utilitaires
function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatDate(dateString) {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      // Si la date n'est pas valide, essayer de la parser manuellement
      const parts = dateString.split(/[-T:.]/);
      if (parts.length >= 5) {
        return `${parts[2]}/${parts[1]}/${parts[0]} à ${parts[3]}:${parts[4]}`;
      }
      return dateString;
    }
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    console.error('Erreur de formatage de date:', e);
    return dateString || 'Date inconnue';
  }
}

// Gestion des onglets
function showTab(tabId) {
  // Masquer tous les onglets
  document.querySelectorAll('.tab').forEach(tab => {
    tab.classList.remove('active');
  });
  
  // Désactiver tous les boutons d'onglet
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Activer l'onglet sélectionné
  const tab = document.getElementById(tabId);
  const btn = document.querySelector(`.tab-btn[data-target="#${tabId}"]`);
  
  if (tab) tab.classList.add('active');
  if (btn) btn.classList.add('active');
  
  // Charger les données de l'onglet si nécessaire
  switch(tabId) {
    case 'users':
      loadUsers();
      break;
    case 'comments':
      loadComments();
      break;
    case 'audit':
      loadAudit();
      break;
    case 'articles':
      loadArticles();
      break;
  }
}

// Gestion des événements
async function handleLogout() {
  const result = await Swal.fire({
    title: 'Déconnexion',
    text: 'Êtes-vous sûr de vouloir vous déconnecter ?',
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Oui, me déconnecter',
    cancelButtonText: 'Annuler',
    reverseButtons: true
  });

  if (result.isConfirmed) {
    // Afficher un indicateur de chargement
    const loadingSwal = Swal.fire({
      title: 'Déconnexion en cours...',
      allowOutsideClick: false,
      didOpen: () => {
        Swal.showLoading();
      }
    });

    try {
      // Nettoyer le stockage local
      localStorage.removeItem('jwt');
      localStorage.removeItem('user');
      
      // Rediriger vers la page d'accueil après un court délai
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
      
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
      Swal.fire('Erreur', 'Une erreur est survenue lors de la déconnexion', 'error');
    } finally {
      loadingSwal.close();
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  // Gestionnaire de déconnexion
  const logoutBtn = $('#logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }

  document.addEventListener('click', async (e) => {
    const tabBtn = e.target.closest('.tab-btn');
    if (tabBtn) {
      e.preventDefault();
      const target = tabBtn.getAttribute('data-target');
      if (target) {
        const tabId = target.replace('#', '');
        showTab(tabId);
      }
    }
    
    // Gestion du bouton d'actualisation
    if (e.target.closest('#refresh-articles')) {
      e.preventDefault();
      const btn = e.target.closest('button');
      const originalHtml = btn.innerHTML;
      
      // Afficher un indicateur de chargement
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Actualisation...';
      
      try {
        await loadArticles();
        
        // Afficher une notification de succès
        const toast = Swal.mixin({
          toast: true,
          position: 'top-end',
          showConfirmButton: false,
          timer: 3000,
          timerProgressBar: true
        });
        
        await toast.fire({
          icon: 'success',
          title: 'Liste actualisée avec succès'
        });
        
      } catch (error) {
        console.error('Erreur lors du rafraîchissement:', error);
        
        // Afficher une notification d'erreur
        await Swal.fire({
          title: 'Erreur',
          text: 'Impossible de rafraîchir la liste des articles',
          icon: 'error',
          confirmButtonColor: '#3085d6',
        });
        
      } finally {
        // Restaurer le bouton
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }
    }
    
    // Gestion du bouton de nouvel article
    if (e.target.closest('#new-article')) {
      e.preventDefault();
      window.location.href = '/?new=1';
    }
    
    // Gestion de la fermeture des alertes
    if (e.target.closest('.btn-close')) {
      e.target.closest('.alert').remove();
    }
  });
  
  const initialTab = window.location.hash.replace('#', '') || 'articles';
  showTab(initialTab);
  
  // Mettre à jour l'URL lors du changement d'onglet
  window.addEventListener('hashchange', () => {
    const tabId = window.location.hash.replace('#', '') || 'articles';
    showTab(tabId);
  });
  
  // Rafraîchir la liste des articles toutes les 30 secondes
  setInterval(() => {
    if (!document.hidden && document.querySelector('.tab.active').id === 'articles') {
      loadArticles();
    }
  }, 30000);

  (async () => {
    try { await api('/auth/me'); }
    catch { location.href = '/login.html'; return; }
    // Vérifier rôle admin côté front
    let u = null; try { u = JSON.parse(localStorage.getItem('user')||'null'); } catch {}
    const isAdmin = !!(u && (u.role === 'admin' || u?.is_admin === true || (Array.isArray(u?.roles) && u.roles.includes('admin'))));
    if (!isAdmin) { location.href = '/'; return; }
    loadUsers(); loadComments(); loadAudit();
  })();
});
