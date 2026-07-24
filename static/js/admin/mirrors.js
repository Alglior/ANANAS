/* admin/mirrors page */
(function () {
  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  var modal = document.getElementById('mirror-modal');
  var form = document.getElementById('mirror-form');
  var modalTitle = document.getElementById('mirror-modal-title');
  var mirrorId = document.getElementById('mirror-id');
  var nameInput = document.getElementById('mirror-name');
  var urlInput = document.getElementById('mirror-url');
  var descInput = document.getElementById('mirror-desc');
  var orderInput = document.getElementById('mirror-order');
  var activeCheck = document.getElementById('mirror-active');
  var errorEl = document.getElementById('mirror-error');
  var submitBtn = document.getElementById('mirror-submit');

  function openModal(mirror) {
    errorEl.classList.add('hidden-section');
    form.reset();
    if (mirror) {
      modalTitle.textContent = 'Modifier le site miroir';
      mirrorId.value = mirror.id;
      nameInput.value = mirror.name;
      urlInput.value = mirror.url;
      descInput.value = mirror.description;
      orderInput.value = mirror.display_order;
      activeCheck.checked = mirror.is_active;
    } else {
      modalTitle.textContent = 'Ajouter un site miroir';
      mirrorId.value = '';
      activeCheck.checked = true;
      orderInput.value = 0;
    }
    modal.classList.remove('hidden-section');
  }

  function closeModal() {
    modal.classList.add('hidden-section');
  }

  async function loadMirrors() {
    var resp = await fetch('/api/admin/mirrors', { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } });
    var data = await resp.json();
    var tbody = document.getElementById('mirrors-tbody');

    if (data.mirrors.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-cell">Aucun site miroir</td></tr>';
    } else {
      tbody.innerHTML = data.mirrors.map(function (m) {
        return '<tr class="' + (m.is_active ? '' : 'mirror-inactive') + '">' +
          '<td data-label="Ordre">' + m.display_order + '</td>' +
          '<td data-label="Nom">' + escapeHtml(m.name) + '</td>' +
          '<td data-label="URL"><a href="' + escapeHtml(m.url) + '" target="_blank" rel="noopener">' + escapeHtml(m.url).substring(0, 50) + (m.url.length > 50 ? '...' : '') + '</a></td>' +
          '<td data-label="Description">' + escapeHtml(m.description) + '</td>' +
          '<td data-label="Statut">' + (m.is_active
            ? '<span class="badge badge-verified">Actif</span>'
            : '<span class="badge badge-pending">Inactif</span>') + '</td>' +
          '<td data-label="Action"><div class="admin-actions-cell">' +
            '<button type="button" class="admin-btn-action btn-green" data-edit-mirror=\'' + JSON.stringify(m).replace(/'/g, '&#39;') + '\'>Modifier</button>' +
            '<button type="button" class="admin-btn-action btn-danger" data-delete-mirror="' + m.id + '">Supprimer</button>' +
          '</div></td>' +
          '</tr>';
      }).join('');
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errorEl.classList.add('hidden-section');

    var name = nameInput.value.trim();
    var url = urlInput.value.trim();
    var desc = descInput.value.trim();
    var order = parseInt(orderInput.value) || 0;
    var active = activeCheck.checked;

    if (!name || !url || !desc) {
      errorEl.textContent = 'Tous les champs sont requis.';
      errorEl.classList.remove('hidden-section');
      return;
    }

    var method = mirrorId.value ? 'PUT' : 'POST';
    var endpoint = mirrorId.value ? '/api/admin/mirrors/' + mirrorId.value : '/api/admin/mirrors';

    submitBtn.disabled = true;
    fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': CsrfModule.getCsrfToken()
      },
      body: JSON.stringify({
        name: name,
        url: url,
        description: desc,
        display_order: order,
        is_active: active
      })
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
      loadMirrors();
    });
  });

  document.getElementById('add-mirror-btn').addEventListener('click', function () {
    openModal(null);
  });

  document.getElementById('mirror-cancel').addEventListener('click', closeModal);

  document.getElementById('mirrors-tbody').addEventListener('click', function (e) {
    var editBtn = e.target.closest('button[data-edit-mirror]');
    if (editBtn) {
      var mirror = JSON.parse(editBtn.dataset.editMirror);
      openModal(mirror);
      return;
    }

    var delBtn = e.target.closest('button[data-delete-mirror]');
    if (delBtn) {
      if (!confirm('Supprimer définitivement ce site miroir ?')) return;
      var id = delBtn.dataset.deleteMirror;
      fetch('/api/admin/mirrors/' + id, {
        method: 'DELETE',
        headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
      }).then(function (r) {
        if (r.ok) loadMirrors();
      });
    }
  });

  document.getElementById('mirror-modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  loadMirrors();
})();