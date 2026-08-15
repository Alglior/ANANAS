/* admin/changelog page */
(function () {
  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  var modal = document.getElementById('version-modal');
  var form = document.getElementById('version-form');
  var modalTitle = document.getElementById('version-modal-title');
  var versionId = document.getElementById('version-id');
  var numberInput = document.getElementById('version-number');
  var orderInput = document.getElementById('version-order');
  var activeCheck = document.getElementById('version-active');
  var sectionsList = document.getElementById('sections-list');
  var errorEl = document.getElementById('version-error');
  var submitBtn = document.getElementById('version-submit');

  function renderSections(sections) {
    sectionsList.innerHTML = '';
    (sections || []).forEach(function (section, idx) {
      var div = document.createElement('div');
      div.className = 'section-entry';
      div.innerHTML =
        '<div class="form-group">' +
          '<label>Titre de la section</label>' +
          '<input type="text" class="section-title" maxlength="200" value="' + escapeHtml(section.title) + '" placeholder="Ex: Nouvelles fonctionnalités" />' +
        '</div>' +
        '<div class="form-group">' +
          '<label>Éléments (un par ligne)</label>' +
          '<textarea class="section-items" rows="4" placeholder="Ajout du blog&#10;Amélioration de la recherche">' + escapeHtml((section.items || []).join('\n')) + '</textarea>' +
        '</div>' +
        '<div class="form-group">' +
          '<label>Ordre</label>' +
          '<input type="number" class="section-order" min="0" value="' + (section.display_order || 0) + '" />' +
        '</div>' +
        '<button type="button" class="admin-btn-action btn-danger remove-section-btn">Supprimer la section</button>';
      sectionsList.appendChild(div);
    });
  }

  function addSection() {
    var entries = sectionsList.querySelectorAll('.section-entry');
    var sections = [];
    entries.forEach(function (entry) {
      sections.push({
        title: entry.querySelector('.section-title').value,
        items: entry.querySelector('.section-items').value.split('\n').filter(function (l) { return l.trim(); }),
        display_order: parseInt(entry.querySelector('.section-order').value) || 0,
      });
    });
    sections.push({ title: '', items: [], display_order: sections.length });
    renderSections(sections);
  }

  function openModal(version) {
    errorEl.classList.add('hidden-section');
    form.reset();
    if (version) {
      modalTitle.textContent = 'Modifier la version';
      versionId.value = version.id;
      numberInput.value = version.version;
      orderInput.value = version.display_order;
      activeCheck.checked = version.is_active;
      renderSections(version.sections);
    } else {
      modalTitle.textContent = 'Ajouter une version';
      versionId.value = '';
      activeCheck.checked = true;
      orderInput.value = 0;
      renderSections([]);
    }
    modal.classList.remove('hidden-section');
  }

  function closeModal() {
    modal.classList.add('hidden-section');
  }

  function collectSections() {
    var entries = sectionsList.querySelectorAll('.section-entry');
    var sections = [];
    entries.forEach(function (entry) {
      var items = entry.querySelector('.section-items').value.split('\n').filter(function (l) { return l.trim(); });
      if (entry.querySelector('.section-title').value.trim() || items.length) {
        sections.push({
          title: entry.querySelector('.section-title').value.trim(),
          items: items,
          display_order: parseInt(entry.querySelector('.section-order').value) || 0,
        });
      }
    });
    return sections;
  }

  async function loadVersions() {
    var resp = await fetch('/api/admin/changelog', { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } });
    var data = await resp.json();
    var tbody = document.getElementById('changelog-tbody');

    if (data.versions.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-cell">Aucune version</td></tr>';
    } else {
      tbody.innerHTML = data.versions.map(function (v) {
        var sectionCount = v.sections.length;
        var sectionNames = v.sections.map(function (s) { return escapeHtml(s.title); }).join(', ');
        return '<tr class="' + (v.is_active ? '' : 'mirror-inactive') + '">' +
          '<td data-label="Ordre">' + v.display_order + '</td>' +
          '<td data-label="Version">v' + escapeHtml(v.version) + '</td>' +
          '<td data-label="Date">' + escapeHtml(v.date) + '</td>' +
          '<td data-label="Sections">' + sectionCount + ' (' + sectionNames + ')</td>' +
          '<td data-label="Statut">' + (v.is_active
            ? '<span class="badge badge-verified">Actif</span>'
            : '<span class="badge badge-pending">Inactif</span>') + '</td>' +
          '<td data-label="Action"><div class="admin-actions-cell">' +
            '<button type="button" class="admin-btn-action btn-green" data-edit-version=\'' + JSON.stringify(v).replace(/'/g, '&#39;') + '\'>Modifier</button>' +
            '<button type="button" class="admin-btn-action btn-danger" data-delete-version="' + v.id + '">Supprimer</button>' +
          '</div></td>' +
          '</tr>';
      }).join('');
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errorEl.classList.add('hidden-section');

    var version = numberInput.value.trim();
    var order = parseInt(orderInput.value) || 0;
    var active = activeCheck.checked;
    var sections = collectSections();

    if (!version) {
      errorEl.textContent = 'Version est requise.';
      errorEl.classList.remove('hidden-section');
      return;
    }

    var method = versionId.value ? 'PUT' : 'POST';
    var endpoint = versionId.value ? '/api/admin/changelog/' + versionId.value : '/api/admin/changelog';

    submitBtn.disabled = true;
    fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': CsrfModule.getCsrfToken()
      },
      body: JSON.stringify({
        version: version,
        display_order: order,
        is_active: active,
        sections: sections
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
      loadVersions();
    });
  });

  document.getElementById('add-version-btn').addEventListener('click', function () {
    openModal(null);
  });

  document.getElementById('add-section-btn').addEventListener('click', addSection);

  sectionsList.addEventListener('click', function (e) {
    if (e.target.closest('.remove-section-btn')) {
      e.target.closest('.section-entry').remove();
    }
  });

  document.getElementById('version-cancel').addEventListener('click', closeModal);

  document.getElementById('changelog-tbody').addEventListener('click', function (e) {
    var editBtn = e.target.closest('button[data-edit-version]');
    if (editBtn) {
      var version = JSON.parse(editBtn.dataset.editVersion);
      openModal(version);
      return;
    }

    var delBtn = e.target.closest('button[data-delete-version]');
    if (delBtn) {
      if (!confirm('Supprimer définitivement cette version ?')) return;
      var id = delBtn.dataset.deleteVersion;
      fetch('/api/admin/changelog/' + id, {
        method: 'DELETE',
        headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
      }).then(function (r) {
        if (r.ok) loadVersions();
      });
    }
  });

  document.getElementById('version-modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  loadVersions();
})();
