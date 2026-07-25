/**
 * A.N.A.N.A.S. — Upload : drafts / trash / publications lists + confirm dialog
 */
UploadModule.history = (function () {
  var currentDraftPage = 1;
  var currentTrashPage = 1;

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function showConfirm(message, onConfirm) {
    var overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = [
      '<div class="confirm-dialog">',
      '<p>' + message + '</p>',
      '<div class="confirm-actions">',
      '<button class="btn-cancel">Annuler</button>',
      '<button class="btn-danger">Supprimer</button>',
      '</div>',
      '</div>'
    ].join('');
    document.body.appendChild(overlay);

    overlay.querySelector('.btn-cancel').addEventListener('click', function() {
      overlay.remove();
    });
    overlay.querySelector('.btn-danger').addEventListener('click', function() {
      overlay.remove();
      onConfirm();
    });
    overlay.addEventListener('click', function(ev) {
      if (ev.target === overlay) overlay.remove();
    });
  }

  function sendDelete(url) {
    fetch(url, {
      method: 'DELETE',
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() },
    }).then(function(resp) {
      if (resp.ok) window.location.reload();
    });
  }

  function sendRestore(url) {
    fetch(url, {
      method: 'POST',
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() },
    }).then(function(resp) {
      if (resp.ok) window.location.reload();
    });
  }

  function renderDraftItem(d) {
    return '<li class="upload-history-item" data-draft-id="' + d.id + '">' +
      '<a href="/catalogue/item/' + d.id + '" class="upload-history-link">' + escapeHtml(d.title) + '</a>' +
      '<span class="upload-history-meta">' +
        '<span class="badge badge-draft">Brouillon</span>' +
        ' ' + d.created_at +
        ' <a href="/upload?edit=' + d.id + '" class="btn btn-sm">Modifier</a>' +
        ' <button type="button" class="btn btn-sm btn-outline draft-delete-btn" data-id="' + d.id + '">Supprimer</button>' +
      '</span>' +
    '</li>';
  }

  function renderTrashItem(t) {
    return '<li class="upload-history-item" data-draft-id="' + t.id + '">' +
      '<span class="upload-history-link trashed-title">' + escapeHtml(t.title) + '</span>' +
      '<span class="upload-history-meta">' +
        '<span class="badge badge-trashed">Corbeille</span>' +
        ' ' + t.deleted_at +
        ' <button type="button" class="btn btn-sm btn-outline trash-restore-btn" data-id="' + t.id + '">Restaurer</button>' +
        ' <button type="button" class="btn btn-sm btn-outline trash-purge-btn" data-id="' + t.id + '">Supprimer</button>' +
      '</span>' +
    '</li>';
  }

  function renderPublicationItem(item) {
    return '<li class="upload-history-item">' +
      '<a href="/catalogue/item/' + item.id + '" class="upload-history-link">' + escapeHtml(item.title) + '</a>' +
      '<span class="upload-history-meta">' +
        '<span class="badge badge-published">' + escapeHtml(item.type_label) + '</span> ' +
        item.created_at +
      '</span>' +
    '</li>';
  }

  function renderPagination(data, containerId) {
    PaginationModule.renderPagination(data, containerId);
  }

  function loadDraftsPage(page) {
    currentDraftPage = page;
    var list = document.getElementById('drafts-list');
    var empty = document.getElementById('drafts-empty');
    if (!list && !empty) return;

    fetch('/api/upload/drafts?page=' + page, {
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
    }).then(function(resp) { return resp.json(); })
    .then(function(data) {
      if (data.total_items === 0 || data.drafts.length === 0) {
        if (list) list.style.display = 'none';
        if (!empty) {
          empty = document.createElement('p');
          empty.className = 'no-data-message';
          empty.id = 'drafts-empty';
          var tabDrafts = document.getElementById('tab-drafts');
          if (tabDrafts) tabDrafts.insertBefore(empty, document.getElementById('draft-pagination'));
        }
        empty.style.display = '';
        empty.textContent = 'Aucun brouillon pour le moment.';
      } else {
        if (empty) empty.style.display = 'none';
        if (!list) {
          list = document.createElement('ul');
          list.className = 'upload-history-list';
          list.id = 'drafts-list';
          var pagDiv = document.getElementById('draft-pagination');
          var tabDrafts = document.getElementById('tab-drafts');
          if (tabDrafts && pagDiv) tabDrafts.insertBefore(list, pagDiv);
        }
        list.style.display = '';
        list.innerHTML = data.drafts.map(renderDraftItem).join('');
      }
      renderPagination(data, 'draft-pagination');
    }).catch(function() {
      console.error('Failed to load drafts');
    });
  }

  function loadTrashPage(page) {
    currentTrashPage = page;
    var list = document.getElementById('trash-list');
    var empty = document.getElementById('trash-empty');

    fetch('/api/upload/trash?page=' + page, {
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
    }).then(function(resp) { return resp.json(); })
    .then(function(data) {
      if (data.total_items === 0 || data.trashed.length === 0) {
        if (list) list.style.display = 'none';
        if (!empty) {
          empty = document.createElement('p');
          empty.className = 'no-data-message';
          empty.id = 'trash-empty';
          var pagDiv = document.getElementById('trash-pagination');
          var tabTrash = document.getElementById('tab-trash');
          if (tabTrash && pagDiv) tabTrash.insertBefore(empty, pagDiv);
        }
        empty.style.display = '';
        empty.textContent = 'La corbeille est vide.';
      } else {
        if (empty) empty.style.display = 'none';
        if (!list) {
          list = document.createElement('ul');
          list.className = 'upload-history-list';
          list.id = 'trash-list';
          var pagDiv = document.getElementById('trash-pagination');
          var tabTrash = document.getElementById('tab-trash');
          if (tabTrash && pagDiv) tabTrash.insertBefore(list, pagDiv);
        }
        list.style.display = '';
        list.innerHTML = data.trashed.map(renderTrashItem).join('');
      }
      renderPagination(data, 'trash-pagination');
    }).catch(function() {
      console.error('Failed to load trash');
    });
  }

  function loadPublicationsPage(page) {
    var list = document.getElementById('publications-list');
    var empty = document.getElementById('publications-empty');

    fetch('/api/upload/publications?page=' + page, {
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
    }).then(function(resp) { return resp.json(); })
    .then(function(data) {
      if (data.total_items === 0 || data.publications.length === 0) {
        if (list) list.style.display = 'none';
        if (!empty) {
          empty = document.createElement('p');
          empty.className = 'no-data-message';
          empty.id = 'publications-empty';
          var pagDiv = document.getElementById('publications-pagination');
          var tabPubs = document.getElementById('tab-publications');
          if (tabPubs && pagDiv) tabPubs.insertBefore(empty, pagDiv);
        }
        empty.style.display = '';
        empty.textContent = 'Vous n\'avez pas encore publi\u00e9 de donn\u00e9es.';
      } else {
        if (empty) empty.style.display = 'none';
        if (!list) {
          list = document.createElement('ul');
          list.className = 'upload-history-list';
          list.id = 'publications-list';
          var pagDiv = document.getElementById('publications-pagination');
          var tabPubs = document.getElementById('tab-publications');
          if (tabPubs && pagDiv) tabPubs.insertBefore(list, pagDiv);
        }
        list.style.display = '';
        list.innerHTML = data.publications.map(renderPublicationItem).join('');
      }
      renderPagination(data, 'publications-pagination');
    }).catch(function() {
      console.error('Failed to load publications');
    });
  }

  function init() {
    document.addEventListener('click', function(e) {
      var delBtn = e.target.closest('.draft-delete-btn');
      if (delBtn) {
        e.preventDefault();
        var draftId = delBtn.getAttribute('data-id');
        showConfirm(
          'Mettre ce brouillon \u00e0 la corbeille ?<br><small>Il restera r\u00e9cup\u00e9rable pendant 7 jours.</small>',
          function() { sendDelete('/api/upload/item/' + draftId); }
        );
        return;
      }

      var restoreBtn = e.target.closest('.trash-restore-btn');
      if (restoreBtn) {
        e.preventDefault();
        var restoreId = restoreBtn.getAttribute('data-id');
        sendRestore('/api/upload/item/' + restoreId + '/restore');
        return;
      }

      var purgeBtn = e.target.closest('.trash-purge-btn');
      if (purgeBtn) {
        e.preventDefault();
        var purgeId = purgeBtn.getAttribute('data-id');
        showConfirm(
          'Supprimer d\u00e9finitivement ce brouillon ?<br><small>Cette action est irr\u00e9versible.</small>',
          function() { sendDelete('/api/upload/item/' + purgeId + '/purge'); }
        );
        return;
      }
    });

    var draftPagination = document.getElementById('draft-pagination');
    if (draftPagination) {
      draftPagination.addEventListener('click', function(e) {
        e.preventDefault();
        var link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
        if (!link) return;
        var page = parseInt(link.dataset.page);
        loadDraftsPage(page);
      });
    }

    var trashPagination = document.getElementById('trash-pagination');
    if (trashPagination) {
      trashPagination.addEventListener('click', function(e) {
        e.preventDefault();
        var link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
        if (!link) return;
        var page = parseInt(link.dataset.page);
        loadTrashPage(page);
      });
    }

    var pubsPagination = document.getElementById('publications-pagination');
    if (pubsPagination) {
      pubsPagination.addEventListener('click', function(e) {
        e.preventDefault();
        var link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
        if (!link) return;
        var page = parseInt(link.dataset.page);
        loadPublicationsPage(page);
      });
    }
  }

  return { init: init };
})();