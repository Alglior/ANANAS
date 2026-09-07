/* admin/tags page */
(function () {
  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  var catModal = document.getElementById('category-modal');
  var catForm = document.getElementById('category-form');
  var catModalTitle = document.getElementById('category-modal-title');
  var catIdInput = document.getElementById('category-id');
  var catNameInput = document.getElementById('category-name');
  var catOrderInput = document.getElementById('category-order');
  var catErrorEl = document.getElementById('category-error');
  var catSubmitBtn = document.getElementById('category-submit');

  var tagModal = document.getElementById('tag-modal');
  var tagForm = document.getElementById('tag-form');
  var tagModalTitle = document.getElementById('tag-modal-title');
  var tagCategoryIdInput = document.getElementById('tag-category-id');
  var tagIdInput = document.getElementById('tag-id');
  var tagNameInput = document.getElementById('tag-name');
  var tagOrderInput = document.getElementById('tag-order');
  var tagErrorEl = document.getElementById('tag-error');
  var tagSubmitBtn = document.getElementById('tag-submit');

  function openCatModal(cat) {
    catErrorEl.classList.add('hidden-section');
    catForm.reset();
    if (cat) {
      catModalTitle.textContent = 'Modifier la catégorie';
      catIdInput.value = cat.id;
      catNameInput.value = cat.name;
      catOrderInput.value = cat.display_order;
    } else {
      catModalTitle.textContent = 'Ajouter une catégorie';
      catIdInput.value = '';
      catOrderInput.value = 0;
    }
    catModal.classList.remove('hidden-section');
  }

  function closeCatModal() {
    catModal.classList.add('hidden-section');
  }

  function openTagModal(categoryId, tag) {
    tagErrorEl.classList.add('hidden-section');
    tagForm.reset();
    tagCategoryIdInput.value = categoryId;
    if (tag) {
      tagModalTitle.textContent = 'Modifier l\'étiquette';
      tagIdInput.value = tag.id;
      tagNameInput.value = tag.name;
      tagOrderInput.value = tag.display_order;
    } else {
      tagModalTitle.textContent = 'Ajouter une étiquette';
      tagIdInput.value = '';
      tagOrderInput.value = 0;
    }
    tagModal.classList.remove('hidden-section');
  }

  function closeTagModal() {
    tagModal.classList.add('hidden-section');
  }

  async function loadTags() {
    var resp = await fetch('/api/admin/tags', { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } });
    var data = await resp.json();
    var tbody = document.getElementById('tags-tbody');

    if (data.categories.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty-cell">Aucune catégorie d\'étiquettes</td></tr>';
    } else {
      tbody.innerHTML = data.categories.map(function (cat) {
        var tagsHtml = cat.tags.length === 0
          ? '<span class="text-muted">Aucune</span>'
          : cat.tags.map(function (t) {
              return '<span class="tag-badge">' +
                escapeHtml(t.name) +
                ' <button type="button" class="tag-badge-remove" data-edit-tag=\'' +
                JSON.stringify(t).replace(/'/g, '&#39;') +
                '\' data-category-id="' + cat.id + '" title="Modifier">&#9998;</button>' +
                ' <button type="button" class="tag-badge-remove" data-delete-tag="' + t.id + '" data-category-id="' + cat.id + '" title="Supprimer">&times;</button>' +
                '</span>';
            }).join('');

        return '<tr>' +
          '<td data-label="Ordre">' + cat.display_order + '</td>' +
          '<td data-label="Catégorie"><strong>' + escapeHtml(cat.name) + '</strong></td>' +
          '<td data-label="Étiquettes" class="tags-cell">' + tagsHtml +
            ' <button type="button" class="btn-tag-add" data-category-id="' + cat.id + '" title="Ajouter une étiquette">+</button>' +
          '</td>' +
          '<td data-label="Action"><div class="admin-actions-cell">' +
            '<button type="button" class="admin-btn-action btn-green" data-edit-cat=\'' + JSON.stringify(cat).replace(/'/g, '&#39;') + '\'>Modifier</button>' +
            '<button type="button" class="admin-btn-action btn-danger" data-delete-cat="' + cat.id + '">Supprimer</button>' +
          '</div></td>' +
          '</tr>';
      }).join('');
    }
  }

  catForm.addEventListener('submit', function (e) {
    e.preventDefault();
    catErrorEl.classList.add('hidden-section');

    var name = catNameInput.value.trim();
    var order = parseInt(catOrderInput.value) || 0;

    if (!name) {
      catErrorEl.textContent = 'Le nom est requis.';
      catErrorEl.classList.remove('hidden-section');
      return;
    }

    var method = catIdInput.value ? 'PUT' : 'POST';
    var endpoint = catIdInput.value ? '/api/admin/tags/' + catIdInput.value : '/api/admin/tags';

    catSubmitBtn.disabled = true;
    fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': CsrfModule.getCsrfToken()
      },
      body: JSON.stringify({ name: name, display_order: order })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      catSubmitBtn.disabled = false;
      if (data.error) {
        catErrorEl.textContent = data.error;
        catErrorEl.classList.remove('hidden-section');
        return;
      }
      closeCatModal();
      loadTags();
    });
  });

  tagForm.addEventListener('submit', function (e) {
    e.preventDefault();
    tagErrorEl.classList.add('hidden-section');

    var categoryId = tagCategoryIdInput.value;
    var name = tagNameInput.value.trim();
    var order = parseInt(tagOrderInput.value) || 0;

    if (!name) {
      tagErrorEl.textContent = 'Le nom est requis.';
      tagErrorEl.classList.remove('hidden-section');
      return;
    }

    var method = tagIdInput.value ? 'PUT' : 'POST';
    var endpoint = tagIdInput.value
      ? '/api/admin/tags/' + categoryId + '/tags/' + tagIdInput.value
      : '/api/admin/tags/' + categoryId + '/tags';

    tagSubmitBtn.disabled = true;
    fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': CsrfModule.getCsrfToken()
      },
      body: JSON.stringify({ name: name, display_order: order })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      tagSubmitBtn.disabled = false;
      if (data.error) {
        tagErrorEl.textContent = data.error;
        tagErrorEl.classList.remove('hidden-section');
        return;
      }
      closeTagModal();
      loadTags();
    });
  });

  document.getElementById('add-category-btn').addEventListener('click', function () {
    openCatModal(null);
  });

  document.getElementById('category-cancel').addEventListener('click', closeCatModal);
  document.getElementById('category-modal-close').addEventListener('click', closeCatModal);
  catModal.addEventListener('click', function (e) {
    if (e.target === catModal) closeCatModal();
  });

  document.getElementById('tag-cancel').addEventListener('click', closeTagModal);
  document.getElementById('tag-modal-close').addEventListener('click', closeTagModal);
  tagModal.addEventListener('click', function (e) {
    if (e.target === tagModal) closeTagModal();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeCatModal();
      closeTagModal();
    }
  });

  document.getElementById('tags-tbody').addEventListener('click', function (e) {
    var editCatBtn = e.target.closest('button[data-edit-cat]');
    if (editCatBtn) {
      var cat = JSON.parse(editCatBtn.dataset.editCat);
      openCatModal(cat);
      return;
    }

    var delCatBtn = e.target.closest('button[data-delete-cat]');
    if (delCatBtn) {
      if (!confirm('Supprimer définitivement cette catégorie et toutes ses étiquettes ?')) return;
      var id = delCatBtn.dataset.deleteCat;
      fetch('/api/admin/tags/' + id, {
        method: 'DELETE',
        headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
      }).then(function (r) {
        if (r.ok) loadTags();
      });
      return;
    }

    var addTagBtn = e.target.closest('button.btn-tag-add');
    if (addTagBtn) {
      var catId = addTagBtn.dataset.categoryId;
      openTagModal(catId, null);
      return;
    }

    var editTagBtn = e.target.closest('button[data-edit-tag]');
    if (editTagBtn) {
      var tag = JSON.parse(editTagBtn.dataset.editTag);
      var catId = editTagBtn.dataset.categoryId;
      openTagModal(catId, tag);
      return;
    }

    var delTagBtn = e.target.closest('button[data-delete-tag]');
    if (delTagBtn) {
      if (!confirm('Supprimer définitivement cette étiquette ?')) return;
      var tagId = delTagBtn.dataset.deleteTag;
      var catId = delTagBtn.dataset.categoryId;
      fetch('/api/admin/tags/' + catId + '/tags/' + tagId, {
        method: 'DELETE',
        headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
      }).then(function (r) {
        if (r.ok) loadTags();
      });
    }
  });

  loadTags();
})();