/* admin/moderation page behaviour */
(function () {
  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  async function loadComments() {
    const resp = await fetch('/api/admin/comments');
    const data = await resp.json();
    const tbody = document.getElementById('comments-tbody');
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">Aucun commentaire</td></tr>';
    } else {
      tbody.innerHTML = data.map(c => `
        <tr>
          <td>${c.id}</td>
          <td>${c.author_name || '(anonyme)'}</td>
          <td>${escapeHtml(c.content).substring(0, 80)}${c.content && c.content.length > 80 ? '...' : ''}</td>
          <td><a href="/catalogue/item/${c.item_id}">${c.item_title || '#'}</a></td>
          <td>${c.item_type || '-'}</td>
          <td>${c.created_at ? new Date(c.created_at).toLocaleDateString('fr-FR') : '-'}</td>
          <td>
            <form class="admin-form-inline" onsubmit="return confirmSuppression(this)">
              <button type="submit" class="admin-btn-action btn-danger" data-delete="/api/admin/comments/${c.id}">Supprimer</button>
            </form>
          </td>
        </tr>
      `).join('');
    }
  }

  async function loadItems() {
    const resp = await fetch('/api/admin/items?type=all&status=all');
    const data = await resp.json();
    const tbody = document.getElementById('items-tbody');
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty-cell">Aucun élément</td></tr>';
    } else {
      tbody.innerHTML = data.map(it => {
        const statusBadge = it.is_published
          ? '<span class="badge badge-verified">Publié</span>'
          : '<span class="badge badge-pending">Non publié</span>';
        const verBadge = it.verification_status === 'verified'
          ? '<span class="badge badge-verified">Vérifié</span>'
          : it.verification_status === 'rejected'
          ? '<span class="badge badge-rejected">Rejeté</span>'
          : '<span class="badge badge-pending">Non vérifié</span>';
        const actions = [];
        if (it.is_published) {
          actions.push(`<button type="button" class="admin-btn-action admin-btn-dismiss" onclick="togglePublish(${it.id}, false)">Masquer</button>`);
        } else {
          actions.push(`<button type="button" class="admin-btn-action admin-btn-resolve" onclick="togglePublish(${it.id}, true)">Publier</button>`);
        }
        actions.push(`<button type="button" class="admin-btn-action btn-danger" onclick="deleteItem(${it.id}, '${escapeHtml(it.title)}')">Supprimer</button>`);
        return `
          <tr>
            <td>${it.id}</td>
            <td><span class="type-badge type-${it.type}">${it.type.charAt(0).toUpperCase() + it.type.slice(1)}</span></td>
            <td>${escapeHtml(it.title).substring(0, 40)}${it.title.length > 40 ? '...' : ''}</td>
            <td>${it.author_name || '-'}</td>
            <td>${statusBadge}</td>
            <td>${verBadge}</td>
            <td>${it.comment_count || 0}</td>
            <td>${it.created_at ? new Date(it.created_at).toLocaleDateString('fr-FR') : '-'}</td>
            <td><div class="admin-actions-cell">${actions.join('')}</div></td>
          </tr>
        `;
      }).join('');
    }
  }

  async function filterComments(type) {
    let url = '/api/admin/comments';
    if (type === 'recent') {
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      url += '?since=' + sevenDaysAgo.toISOString();
    }
    const resp = await fetch(url);
    const data = await resp.json();
    const tbody = document.getElementById('comments-tbody');
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">Aucun commentaire</td></tr>';
    } else {
      tbody.innerHTML = data.map(c => `
        <tr>
          <td>${c.id}</td>
          <td>${c.author_name || '(anonyme)'}</td>
          <td>${escapeHtml(c.content).substring(0, 80)}${c.content && c.content.length > 80 ? '...' : ''}</td>
          <td><a href="/catalogue/item/${c.item_id}">${c.item_title || '#'}</a></td>
          <td>${c.item_type || '-'}</td>
          <td>${c.created_at ? new Date(c.created_at).toLocaleDateString('fr-FR') : '-'}</td>
          <td>
            <form class="admin-form-inline" onsubmit="return confirmSuppression(this)">
              <button type="submit" class="admin-btn-action btn-danger" data-delete="/api/admin/comments/${c.id}">Supprimer</button>
            </form>
          </td>
        </tr>
      `).join('');
    }
  }

  async function filterItems(type) {
    const url = `/api/admin/items?type=${type}&status=all`;
    const resp = await fetch(url);
    const data = await resp.json();
    const tbody = document.getElementById('items-tbody');
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty-cell">Aucun élément</td></tr>';
    } else {
      tbody.innerHTML = data.map(it => {
        const statusBadge = it.is_published
          ? '<span class="badge badge-verified">Publié</span>'
          : '<span class="badge badge-pending">Non publié</span>';
        const verBadge = it.verification_status === 'verified'
          ? '<span class="badge badge-verified">Vérifié</span>'
          : it.verification_status === 'rejected'
          ? '<span class="badge badge-rejected">Rejeté</span>'
          : '<span class="badge badge-pending">Non vérifié</span>';
        const actions = [];
        if (it.is_published) {
          actions.push(`<button type="button" class="admin-btn-action admin-btn-dismiss" onclick="togglePublish(${it.id}, false)">Masquer</button>`);
        } else {
          actions.push(`<button type="button" class="admin-btn-action admin-btn-resolve" onclick="togglePublish(${it.id}, true)">Publier</button>`);
        }
        actions.push(`<button type="button" class="admin-btn-action btn-danger" onclick="deleteItem(${it.id}, '${escapeHtml(it.title)}')">Supprimer</button>`);
        return `
          <tr>
            <td>${it.id}</td>
            <td><span class="type-badge type-${it.type}">${it.type.charAt(0).toUpperCase() + it.type.slice(1)}</span></td>
            <td>${escapeHtml(it.title).substring(0, 40)}${it.title.length > 40 ? '...' : ''}</td>
            <td>${it.author_name || '-'}</td>
            <td>${statusBadge}</td>
            <td>${verBadge}</td>
            <td>${it.comment_count || 0}</td>
            <td>${it.created_at ? new Date(it.created_at).toLocaleDateString('fr-FR') : '-'}</td>
            <td><div class="admin-actions-cell">${actions.join('')}</div></td>
          </tr>
        `;
      }).join('');
    }
  }

  window.confirmSuppression = function (form) {
    return confirm('Êtes-vous sûr de vouloir supprimer ce commentaire ? Cette action est irréversible.');
  };

  window.togglePublish = function (itemId, published) {
    const endpoint = published ? '/api/admin/items/' + itemId + '/publish' : '/api/admin/items/' + itemId + '/unpublish';
    fetch(endpoint, { method: 'POST' })
      .then(r => { if (r.ok) window.location.reload(); });
  };

  window.deleteItem = function (itemId, title) {
    const msg = `Êtes-vous sûr de vouloir supprimer cet élément "${title}" ? Cette action est irréversible et supprimera aussi les commentaires, notes et galeries associés.`;
    if (!confirm(msg)) return;
    fetch('/api/admin/items/' + itemId, { method: 'DELETE' })
      .then(r => { if (r.ok) window.location.reload(); });
  };

  document.querySelectorAll('#comment-filters a').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('#comment-filters a').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const type = this.dataset.type;
      filterComments(type);
    });
  });

  document.querySelectorAll('#item-filters a').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('#item-filters a').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const type = this.dataset.type;
      filterItems(type);
    });
  });

  loadComments();
  loadItems();
})();
