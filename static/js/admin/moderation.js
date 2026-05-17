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
          <td data-label="ID">${c.id}</td>
          <td data-label="Auteur">${c.author_name || '(anonyme)'}</td>
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
          actions.push(`<button type="button" class="admin-btn-action admin-btn-dismiss" data-toggle-publish="${it.id}" data-published="false">Masquer</button>`);
        } else {
          actions.push(`<button type="button" class="admin-btn-action admin-btn-resolve" data-toggle-publish="${it.id}" data-published="true">Publier</button>`);
        }
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
            <td data-label="Type"><span class="type-badge type-${it.type}">${it.type.charAt(0).toUpperCase() + it.type.slice(1)}</span></td>
            <td data-label="Titre"><a href="/catalogue/item/${it.id}" class="admin-item-link">${escapeHtml(it.title).substring(0, 40)}${it.title.length > 40 ? '...' : ''}</a></td>
            <td data-label="Auteur">${it.author_name || '-'}</td>
            <td data-label="Publié">${statusBadge}</td>
            <td data-label="Vérification">${verBadge}</td>
            <td data-label="Commentaires">${it.comment_count || 0}</td>
            <td data-label="Date">${it.created_at ? new Date(it.created_at).toLocaleDateString('fr-FR') : '-'}</td>
            <td data-label="Action"><div class="admin-actions-cell">${actions.join('')}</div></td>
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
          <td data-label="ID">${c.id}</td>
          <td data-label="Auteur">${c.author_name || '(anonyme)'}</td>
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
          actions.push(`<button type="button" class="admin-btn-action admin-btn-dismiss" data-toggle-publish="${it.id}" data-published="false">Masquer</button>`);
        } else {
          actions.push(`<button type="button" class="admin-btn-action admin-btn-resolve" data-toggle-publish="${it.id}" data-published="true">Publier</button>`);
        }
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
            <td data-label="Type"><span class="type-badge type-${it.type}">${it.type.charAt(0).toUpperCase() + it.type.slice(1)}</span></td>
            <td data-label="Titre"><a href="/catalogue/item/${it.id}" class="admin-item-link">${escapeHtml(it.title).substring(0, 40)}${it.title.length > 40 ? '...' : ''}</a></td>
            <td data-label="Auteur">${it.author_name || '-'}</td>
            <td data-label="Publié">${statusBadge}</td>
            <td data-label="Vérification">${verBadge}</td>
            <td data-label="Commentaires">${it.comment_count || 0}</td>
            <td data-label="Date">${it.created_at ? new Date(it.created_at).toLocaleDateString('fr-FR') : '-'}</td>
            <td data-label="Action"><div class="admin-actions-cell">${actions.join('')}</div></td>
          </tr>
        `;
      }).join('');
    }
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
    fetch(endpoint, { method: 'DELETE' })
      .then(r => { if (r.ok) reloadWithTab('comments'); });
  });

  // Event delegation for publish/unpublish toggles
  document.getElementById('items-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('button[data-toggle-publish]');
    if (!btn) return;
    const itemId = parseInt(btn.dataset.togglePublish);
    const published = btn.dataset.published === 'true';
    const endpoint = published ? '/api/admin/items/' + itemId + '/publish' : '/api/admin/items/' + itemId + '/unpublish';
    fetch(endpoint, { method: 'POST' })
      .then(r => { if (r.ok) reloadWithTab('items'); });
  });

  // Event delegation for verify button
  document.getElementById('items-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('button[data-verify-item]');
    if (!btn) return;
    const itemId = parseInt(btn.dataset.verifyItem);
    fetch('/api/admin/items/' + itemId + '/verify', { method: 'POST' })
      .then(r => { if (r.ok) reloadWithTab('items'); });
  });

  // Event delegation for unverify button
  document.getElementById('items-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('button[data-unverify-item]');
    if (!btn) return;
    const itemId = parseInt(btn.dataset.unverifyItem);
    fetch('/api/admin/items/' + itemId + '/unverify', { method: 'POST' })
      .then(r => { if (r.ok) reloadWithTab('items'); });
  });

  // Event delegation for item deletion
  document.getElementById('items-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('button[data-delete-item]');
    if (!btn) return;
    const itemId = parseInt(btn.dataset.deleteItem);
    const msg = 'Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible et supprimera aussi les commentaires, notes et galeries associés.';
    if (!confirm(msg)) return;
    fetch('/api/admin/items/' + itemId, { method: 'DELETE' })
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

  // Filter buttons for items
  document.querySelectorAll('#item-filters button').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('#item-filters button').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const type = this.dataset.type;
      filterItems(type);
    });
  });

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
