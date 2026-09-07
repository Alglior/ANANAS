(function () {
  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  var modal = document.getElementById('sf-modal');
  var form = document.getElementById('sf-form');
  var searchInput = document.getElementById('sf-search');
  var searchResults = document.getElementById('sf-search-results');
  var itemIdInput = document.getElementById('sf-item-id');
  var selectedDiv = document.getElementById('sf-selected');
  var selectedTitle = document.getElementById('sf-selected-title');
  var selectedInfo = document.getElementById('sf-selected-info');
  var errorEl = document.getElementById('sf-error');
  var submitBtn = document.getElementById('sf-submit');
  var searchTimeout = null;

  function openModal() {
    errorEl.classList.add('hidden-section');
    form.reset();
    itemIdInput.value = '';
    selectedDiv.classList.add('hidden-section');
    searchResults.classList.add('hidden-section');
    searchInput.value = '';
    searchInput.focus();
    submitBtn.textContent = 'Ajouter';
    submitBtn.disabled = true;
    modal.classList.remove('hidden-section');
  }

  function closeModal() {
    modal.classList.add('hidden-section');
  }

  function selectItem(item) {
    itemIdInput.value = item.id;
    selectedTitle.textContent = item.title;
    selectedInfo.textContent = (item.type || '') + ' \u2014 ' + (item.format_type || '');
    selectedDiv.classList.remove('hidden-section');
    searchResults.classList.add('hidden-section');
    searchInput.value = item.title;
    submitBtn.disabled = false;
  }

  function renderSearchResults(items) {
    if (items.length === 0) {
      searchResults.innerHTML = '<div class="search-result-item search-no-results">Aucun item trouv\u00e9</div>';
    } else {
      searchResults.innerHTML = items.map(function (it) {
        return '<div class="search-result-item" data-item=\'' + JSON.stringify(it).replace(/'/g, '&#39;') + '\'>' +
          '<strong>' + escapeHtml(it.title) + '</strong>' +
          '<span class="search-result-meta">' + escapeHtml(it.type || '') + ' \u2014 ' + escapeHtml(it.format_type || '') + '</span>' +
          '</div>';
      }).join('');
    }
    searchResults.classList.remove('hidden-section');
  }

  searchInput.addEventListener('input', function () {
    var q = searchInput.value.trim();
    if (q.length < 2) {
      searchResults.classList.add('hidden-section');
      return;
    }
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function () {
      fetch('/api/admin/items/search?q=' + encodeURIComponent(q) + '&limit=10', {
        headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
      })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        renderSearchResults(data.items);
      });
    }, 250);
  });

  searchResults.addEventListener('click', function (e) {
    var item = e.target.closest('.search-result-item');
    if (!item || !item.dataset.item) return;
    selectItem(JSON.parse(item.dataset.item));
  });

  document.addEventListener('click', function (e) {
    if (!searchResults.contains(e.target) && e.target !== searchInput) {
      searchResults.classList.add('hidden-section');
    }
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errorEl.classList.add('hidden-section');

    if (!itemIdInput.value) {
      errorEl.textContent = 'Veuillez s\u00e9lectionner un item.';
      errorEl.classList.remove('hidden-section');
      return;
    }

    submitBtn.disabled = true;
    fetch('/api/admin/simple-files', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': CsrfModule.getCsrfToken()
      },
      body: JSON.stringify({ item_id: parseInt(itemIdInput.value) })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      submitBtn.disabled = false;
      if (data.error) {
        errorEl.textContent = data.error;
        errorEl.classList.remove('hidden-section');
        return;
      }
      closeModal();
      loadSimpleFiles();
    })
    .catch(function () {
      submitBtn.disabled = false;
      errorEl.textContent = 'Erreur r\u00e9seau.';
      errorEl.classList.remove('hidden-section');
    });
  });

  function loadSimpleFiles() {
    fetch('/api/admin/simple-files', { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var tbody = document.getElementById('sf-tbody');
      if (data.simple_files.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">Aucun fichier simple</td></tr>';
      } else {
        tbody.innerHTML = data.simple_files.map(function (f) {
          return '<tr class="' + (f.is_active ? '' : 'mirror-inactive') + '">' +
            '<td data-label="Ordre">' + f.display_order + '</td>' +
            '<td data-label="ID">' + f.item_id + '</td>' +
            '<td data-label="Titre"><a href="/catalogue/item/' + f.item_id + '">' + escapeHtml(f.item_title || '\u2014') + '</a></td>' +
            '<td data-label="Type">' + escapeHtml(f.item_type || '\u2014') + '</td>' +
            '<td data-label="Format">' + escapeHtml(f.item_format || '\u2014') + '</td>' +
            '<td data-label="Statut">' + (f.is_active
              ? '<span class="badge badge-verified">Actif</span>'
              : '<span class="badge badge-pending">Inactif</span>') + '</td>' +
            '<td data-label="Action"><div class="admin-actions-cell">' +
              '<button type="button" class="admin-btn-action btn-green" data-toggle-sf="' + f.id + '" data-active="' + f.is_active + '">' + (f.is_active ? 'D\u00e9sactiver' : 'Activer') + '</button>' +
              '<button type="button" class="admin-btn-action btn-danger" data-delete-sf="' + f.id + '">Retirer</button>' +
            '</div></td>' +
            '</tr>';
        }).join('');
      }
    });
  }

  document.getElementById('add-sf-btn').addEventListener('click', openModal);
  document.getElementById('sf-cancel').addEventListener('click', closeModal);
  document.getElementById('sf-modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  document.getElementById('sf-tbody').addEventListener('click', function (e) {
    var toggleBtn = e.target.closest('button[data-toggle-sf]');
    if (toggleBtn) {
      var id = toggleBtn.dataset.toggleSf;
      var active = toggleBtn.dataset.active === 'true';
      fetch('/api/admin/simple-files/' + id, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': CsrfModule.getCsrfToken()
        },
        body: JSON.stringify({ is_active: !active })
      }).then(function (r) {
        if (r.ok) loadSimpleFiles();
      });
      return;
    }

    var delBtn = e.target.closest('button[data-delete-sf]');
    if (delBtn) {
      if (!confirm('Retirer ce fichier simple de la page d\'accueil ?')) return;
      var id = delBtn.dataset.deleteSf;
      fetch('/api/admin/simple-files/' + id, {
        method: 'DELETE',
        headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
      }).then(function (r) {
        if (r.ok) loadSimpleFiles();
      });
    }
  });

  loadSimpleFiles();
})();