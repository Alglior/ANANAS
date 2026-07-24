/* admin/geopackages page */
(function () {
  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  var modal = document.getElementById('gp-modal');
  var form = document.getElementById('gp-form');
  var modalTitle = document.getElementById('gp-modal-title');
  var pkgId = document.getElementById('gp-id');
  var titleInput = document.getElementById('gp-title');
  var descInput = document.getElementById('gp-desc');
  var formatInput = document.getElementById('gp-format');
  var linkInput = document.getElementById('gp-link');
  var orderInput = document.getElementById('gp-order');
  var activeCheck = document.getElementById('gp-active');
  var errorEl = document.getElementById('gp-error');
  var submitBtn = document.getElementById('gp-submit');

  function openModal(pkg) {
    errorEl.classList.add('hidden-section');
    form.reset();
    if (pkg) {
      modalTitle.textContent = 'Modifier le pack';
      pkgId.value = pkg.id;
      titleInput.value = pkg.title;
      descInput.value = pkg.description;
      formatInput.value = pkg.format_info;
      linkInput.value = pkg.link_url;
      orderInput.value = pkg.display_order;
      activeCheck.checked = pkg.is_active;
      submitBtn.textContent = 'Enregistrer';
    } else {
      modalTitle.textContent = 'Ajouter un pack';
      pkgId.value = '';
      activeCheck.checked = true;
      orderInput.value = 0;
      submitBtn.textContent = 'Ajouter';
    }
    modal.classList.remove('hidden-section');
  }

  function closeModal() {
    modal.classList.add('hidden-section');
  }

  function loadPackages() {
    fetch('/api/admin/geopackages', { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var tbody = document.getElementById('geopackages-tbody');
      if (data.packages.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">Aucun pack</td></tr>';
      } else {
        tbody.innerHTML = data.packages.map(function (p) {
          return '<tr class="' + (p.is_active ? '' : 'mirror-inactive') + '">' +
            '<td data-label="Ordre">' + p.display_order + '</td>' +
            '<td data-label="Titre">' + escapeHtml(p.title) + '</td>' +
            '<td data-label="Description">' + escapeHtml(p.description).substring(0, 60) + (p.description.length > 60 ? '...' : '') + '</td>' +
            '<td data-label="Format">' + escapeHtml(p.format_info) + '</td>' +
            '<td data-label="Lien"><a href="' + escapeHtml(p.link_url) + '" target="_blank" rel="noopener">' + escapeHtml(p.link_url).substring(0, 40) + '</a></td>' +
            '<td data-label="Statut">' + (p.is_active
              ? '<span class="badge badge-verified">Actif</span>'
              : '<span class="badge badge-pending">Inactif</span>') + '</td>' +
            '<td data-label="Action"><div class="admin-actions-cell">' +
              '<button type="button" class="admin-btn-action btn-green" data-edit-gp=\'' + JSON.stringify(p).replace(/'/g, '&#39;') + '\'>Modifier</button>' +
              '<button type="button" class="admin-btn-action btn-danger" data-delete-gp="' + p.id + '">Supprimer</button>' +
            '</div></td>' +
            '</tr>';
        }).join('');
      }
    });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errorEl.classList.add('hidden-section');

    var payload = {
      title: titleInput.value.trim(),
      description: descInput.value.trim(),
      format_info: formatInput.value.trim(),
      link_url: linkInput.value.trim(),
      display_order: parseInt(orderInput.value) || 0,
      is_active: activeCheck.checked
    };

    if (!payload.title || !payload.description || !payload.format_info || !payload.link_url) {
      errorEl.textContent = 'Tous les champs sont requis.';
      errorEl.classList.remove('hidden-section');
      return;
    }

    var method = pkgId.value ? 'PUT' : 'POST';
    var endpoint = pkgId.value ? '/api/admin/geopackages/' + pkgId.value : '/api/admin/geopackages';

    submitBtn.disabled = true;
    fetch(endpoint, {
      method: method,
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': CsrfModule.getCsrfToken() },
      body: JSON.stringify(payload)
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
      loadPackages();
    });
  });

  document.getElementById('add-gp-btn').addEventListener('click', function () { openModal(null); });
  document.getElementById('gp-cancel').addEventListener('click', closeModal);
  document.getElementById('gp-modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });

  document.getElementById('geopackages-tbody').addEventListener('click', function (e) {
    var editBtn = e.target.closest('button[data-edit-gp]');
    if (editBtn) { openModal(JSON.parse(editBtn.dataset.editGp)); return; }

    var delBtn = e.target.closest('button[data-delete-gp]');
    if (delBtn) {
      if (!confirm('Supprimer définitivement ce pack ?')) return;
      fetch('/api/admin/geopackages/' + delBtn.dataset.deleteGp, {
        method: 'DELETE', headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
      }).then(function (r) { if (r.ok) loadPackages(); });
    }
  });

  loadPackages();
})();