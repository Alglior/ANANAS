/* admin/moderation page behaviour */
(function () {
  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  let commentPage = 1;
  let activeCommentFilter = 'all';
  let itemPage = 1;
  let activeItemFilter = 'all';

  function renderCommentPagination(data) {
    const container = document.getElementById('comment-pagination');
    if (!container || data.total_pages <= 1) {
      if (container) container.innerHTML = '';
      return;
    }
    const baseQuery = activeCommentFilter === 'recent' ? '?since=' + new Date(Date.now() - 7 * 86400000).toISOString() : '';
    let html = '<nav class="pagination mod-pagination-nav" aria-label="Pagination des commentaires">';

    if (data.page > 1) {
      html += `<a class="btn btn-outline transition-hover pagination-prev" href="#" data-page="${data.page - 1}" ${baseQuery ? 'data-filter="recent"' : 'data-filter="all"' }>&#9664;&nbsp;Précédent</a>`;
    } else {
      html += `<span class="btn btn-outline pagination-prev disabled">&#9664;&nbsp;Précédent</span>`;
    }

    html += '<div class="pagination-numbers">';
    for (const p of data.page_numbers) {
      if (p === '...') {
        html += '<span class="pagination-ellipsis">&hellip;</span>';
      } else if (p === data.page) {
        html += `<span class="pagination-link active">${p}</span>`;
      } else {
        html += `<a class="pagination-link" href="#" data-page="${p}" ${baseQuery ? 'data-filter="recent"' : 'data-filter="all"' }>${p}</a>`;
      }
    }
    html += '</div>';

    if (data.page < data.total_pages) {
      html += `<a class="btn btn-outline transition-hover pagination-next" href="#" data-page="${data.page + 1}" ${baseQuery ? 'data-filter="recent"' : 'data-filter="all"' }>Suivant&nbsp;&#9658;</a>`;
    } else {
      html += `<span class="btn btn-outline pagination-next disabled">Suivant&nbsp;&#9658;</span>`;
    }

    html += '</nav>';
    container.innerHTML = html;
  }

  async function loadComments(page = 1) {
    let url = '/api/admin/comments?page=' + page;
    if (activeCommentFilter === 'recent') {
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      url += '&since=' + sevenDaysAgo.toISOString();
    }
    const resp = await fetch(url, { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } });
    const data = await resp.json();
    const tbody = document.getElementById('comments-tbody');
    if (data.comments.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">Aucun commentaire</td></tr>';
    } else {
      tbody.innerHTML = data.comments.map(c => `
        <tr>
          <td data-label="ID">${c.id}</td>
          <td data-label="Auteur">${escapeHtml(c.author_name || '(anonyme)')}</td>
          <td data-label="Contenu">${escapeHtml(c.content).substring(0, 80)}${c.content && c.content.length > 80 ? '...' : ''}</td>
          <td data-label="Article"><a href="/catalogue/item/${c.item_id}">${c.item_title || '#'}</a></td>
          <td data-label="Type">${c.item_type || '-'}</td>
          <td data-label="Date">${c.created_at ? new Date(c.created_at).toLocaleDateString('fr-FR') : '-'}</td>
          <td data-label="Action">
            <form class="admin-form-inline" data-delete-comment="${c.id}" method="post">
              <button type="submit" class="admin-btn-action btn-danger">Supprimer</button>
            </form>
          </td>
        </tr>
      `).join('');
    }
    renderCommentPagination(data);
  }

  function renderItemsRows(items) {
    const allowedTypes = {
      geodonnee: "Géodonnée",
      carte: "Carte",
      application: "Application"
    };

    return items.map(it => {
      const verBadge = it.verification_status === 'verified'
        ? '<span class="badge badge-verified">Vérifié</span>'
        : it.verification_status === 'rejected'
        ? '<span class="badge badge-rejected">Rejeté</span>'
        : '<span class="badge badge-pending">Non vérifié</span>';

      const rawType = (typeof it.type === 'string') ? it.type : '';
      const safeType = Object.prototype.hasOwnProperty.call(allowedTypes, rawType) ? rawType : 'unknown';
      const typeLabel = allowedTypes[safeType] || 'Inconnu';

      const actions = [];
      actions.push(`<a href="/catalogue/item/${it.id}" class="admin-btn-action btn-green">Voir données</a>`);
      if (it.verification_status === 'verified') {
        actions.push(`<button type="button" class="admin-btn-action btn-unverify" data-unverify-item="${it.id}">Révoquer</button>`);
      } else {
        actions.push(`<button type="button" class="admin-btn-action btn-verify" data-verify-item="${it.id}">Vérifier</button>`);
      }
      actions.push(`<button type="button" class="admin-btn-action btn-danger" data-delete-item="${it.id}">Supprimer</button>`);
      return `
          <tr>
            <td data-label="ID">${it.id}</td>
            <td data-label="Type"><span class="type-badge type-${safeType}">${escapeHtml(typeLabel)}</span></td>
            <td data-label="Titre"><a href="/catalogue/item/${it.id}" class="admin-item-link">${escapeHtml(it.title).substring(0, 40)}${it.title.length > 40 ? '...' : ''}</a></td>
            <td data-label="Auteur">${escapeHtml(it.author_name || '-')}</td>
            <td data-label="Vérification">${verBadge}</td>
            <td data-label="Commentaires">${it.comment_count || 0}</td>
            <td data-label="Date">${it.created_at ? new Date(it.created_at).toLocaleDateString('fr-FR') : '-'}</td>
            <td data-label="Action"><div class="admin-actions-cell">${actions.join('')}</div></td>
          </tr>
        `;
    }).join('');
  }

  function renderItemsTable(items) {
    const tbody = document.getElementById('items-tbody');
    if (items.length === 0) {
      return '<tr><td colspan="9" class="empty-cell">Aucun élément</td></tr>';
    }
    return renderItemsRows(items);
  }

function renderItemPagination(data) {
    PaginationModule.renderPagination(data, 'items-pagination', { navClass: 'mod-pagination-nav', ariaLabel: 'Pagination des \u00e9l\u00e9ments' });
  }
    let html = '<nav class="pagination mod-pagination-nav" aria-label="Pagination des éléments">';

    if (data.page > 1) {
      html += `<a class="btn btn-outline transition-hover pagination-prev" href="#" data-page="${data.page - 1}">&#9664;&nbsp;Précédent</a>`;
    } else {
      html += `<span class="btn btn-outline pagination-prev disabled">&#9664;&nbsp;Précédent</span>`;
    }

    html += '<div class="pagination-numbers">';
    for (const p of data.page_numbers) {
      if (p === '...') {
        html += '<span class="pagination-ellipsis">&hellip;</span>';
      } else if (p === data.page) {
        html += `<span class="pagination-link active">${p}</span>`;
      } else {
        html += `<a class="pagination-link" href="#" data-page="${p}">${p}</a>`;
      }
    }
    html += '</div>';

    if (data.page < data.total_pages) {
      html += `<a class="btn btn-outline transition-hover pagination-next" href="#" data-page="${data.page + 1}">Suivant&nbsp;&#9658;</a>`;
    } else {
      html += `<span class="btn btn-outline pagination-next disabled">Suivant&nbsp;&#9658;</span>`;
    }

    html += '</nav>';
    container.innerHTML = html;
  }

  async function loadItemsPage(page = 1) {
    let url = '/api/admin/items?type=' + activeItemFilter + '&status=all&page=' + page;
    const resp = await fetch(url, { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } });
    const data = await resp.json();
    document.getElementById('items-tbody').innerHTML = renderItemsTable(data.items);
    renderItemPagination(data);
  }

  async function loadItems() {
    await loadItemsPage(itemPage);
  }

  async function filterComments(type) {
    activeCommentFilter = type;
    commentPage = 1;
    await loadComments(commentPage);
  }

  async function filterItems(type) {
    activeItemFilter = type;
    itemPage = 1;
    await loadItemsPage(itemPage);
  }

  function reloadWithTab(tabName) {
    const url = new URL(window.location);
    url.searchParams.set('tab', tabName);
    window.location.href = url.toString();
  }

  let activeTab = (new URLSearchParams(window.location.search)).get('tab') || 'comments';

  // Restore active tab from URL parameter on load
  document.querySelectorAll('.mod-tab').forEach(tab => {
    if (tab.dataset.tab === activeTab) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const targetPanel = document.getElementById('tab-' + activeTab);
  if (targetPanel) targetPanel.classList.add('active');

  // Event delegation for comment deletion forms
  document.getElementById('comments-tbody').addEventListener('submit', function (e) {
    const form = e.target.closest('form[data-delete-comment]');
    if (!form) return;
    e.preventDefault();
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce commentaire ? Cette action est irréversible.')) return;
    const endpoint = '/api/admin/comments/' + form.dataset.deleteComment;
    fetch(endpoint, { method: 'DELETE', headers: {'X-CSRF-Token': CsrfModule.getCsrfToken()}})
      .then(r => { if (r.ok) reloadWithTab('comments'); });
  });

  // Event delegation for verify button
  document.getElementById('items-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('button[data-verify-item]');
    if (!btn) return;
    const itemId = parseInt(btn.dataset.verifyItem);
    fetch('/api/admin/items/' + itemId + '/verify', { method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': CsrfModule.getCsrfToken()}})
      .then(r => { if (r.ok) reloadWithTab('items'); });
  });

  // Event delegation for unverify button
  document.getElementById('items-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('button[data-unverify-item]');
    if (!btn) return;
    const itemId = parseInt(btn.dataset.unverifyItem);
    fetch('/api/admin/items/' + itemId + '/unverify', { method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': CsrfModule.getCsrfToken()}})
      .then(r => { if (r.ok) reloadWithTab('items'); });
  });

  // Event delegation for item deletion
  document.getElementById('items-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('button[data-delete-item]');
    if (!btn) return;
    const itemId = parseInt(btn.dataset.deleteItem);
    const msg = 'Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible et supprimera aussi les commentaires, notes et galeries associés.';
    if (!confirm(msg)) return;
    fetch('/api/admin/items/' + itemId, { method: 'DELETE', headers: {'X-CSRF-Token': CsrfModule.getCsrfToken()}})
      .then(r => { if (r.ok) reloadWithTab('items'); });
  });

  // Filter buttons for comments
  document.querySelectorAll('#comment-filters button').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('#comment-filters button').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const type = this.dataset.type;
      filterComments(type);
    });
  });

  // Pagination for comments
  const pagDiv = document.getElementById('comment-pagination');
  if (pagDiv) {
    pagDiv.addEventListener('click', function (e) {
      e.preventDefault();
      const link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
      if (!link) return;
      const page = parseInt(link.dataset.page);
      const filter = link.dataset.filter;
      commentPage = page;
      if (filter) {
        document.querySelectorAll('#comment-filters button').forEach(b => b.classList.remove('active'));
        const filterBtn = document.querySelector(`#comment-filters button[data-type="${filter}"]`);
        if (filterBtn) filterBtn.classList.add('active');
        activeCommentFilter = filter;
      }
      loadComments(page);
    });
  }

  // Filter buttons for items
  document.querySelectorAll('#item-filters button').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('#item-filters button').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const type = this.dataset.type;
      filterItems(type);
    });
  });

  // Pagination for items
  const itemsPagDiv = document.getElementById('items-pagination');
  if (itemsPagDiv) {
    itemsPagDiv.addEventListener('click', function (e) {
      e.preventDefault();
      const link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
      if (!link) return;
      const page = parseInt(link.dataset.page);
      itemPage = page;
      loadItemsPage(page);
    });
  }

  // Tab switching for moderation panels
  document.querySelectorAll('.mod-tab').forEach(tab => {
    tab.addEventListener('click', function () {
      const tabName = this.dataset.tab;
      document.querySelectorAll('.mod-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      document.getElementById('tab-' + tabName).classList.add('active');

      const url = new URL(window.location);
      url.searchParams.set('tab', tabName);
      window.history.pushState({}, '', url.toString());
    });
  });

  loadComments();
  loadItems();
})();
