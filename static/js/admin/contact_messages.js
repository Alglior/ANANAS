/* admin/contact-messages page */
(function () {
  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  var msgPage = 1;
  var activeFilter = 'all';

function renderPagination(data) {
    PaginationModule.renderPagination(data, 'contact-msgs-pagination', { navClass: 'mod-pagination-nav', ariaLabel: 'Pagination des messages' });
  }
    var html = '<nav class="pagination mod-pagination-nav" aria-label="Pagination des messages">';

    if (data.page > 1) {
      html += '<a class="btn btn-outline transition-hover pagination-prev" href="#" data-page="' + (data.page - 1) + '">&#9664;&nbsp;Précédent</a>';
    } else {
      html += '<span class="btn btn-outline pagination-prev disabled">&#9664;&nbsp;Précédent</span>';
    }

    html += '<div class="pagination-numbers">';
    for (var i = 0; i < data.page_numbers.length; i++) {
      var p = data.page_numbers[i];
      if (p === '...') {
        html += '<span class="pagination-ellipsis">&hellip;</span>';
      } else if (p === data.page) {
        html += '<span class="pagination-link active">' + p + '</span>';
      } else {
        html += '<a class="pagination-link" href="#" data-page="' + p + '">' + p + '</a>';
      }
    }
    html += '</div>';

    if (data.page < data.total_pages) {
      html += '<a class="btn btn-outline transition-hover pagination-next" href="#" data-page="' + (data.page + 1) + '">Suivant&nbsp;&#9658;</a>';
    } else {
      html += '<span class="btn btn-outline pagination-next disabled">Suivant&nbsp;&#9658;</span>';
    }

    html += '</nav>';
    container.innerHTML = html;
  }

  function openModal(msg) {
    document.getElementById('modal-subject').textContent = msg.subject;
    document.getElementById('modal-name').textContent = msg.name;
    document.getElementById('modal-email').textContent = msg.email;
    document.getElementById('modal-message').textContent = msg.message;
    document.getElementById('modal-date').textContent = msg.created_at ? new Date(msg.created_at).toLocaleString('fr-FR') : '-';
    document.getElementById('contact-msg-modal').classList.remove('hidden-section');

    if (!msg.is_read) {
      fetch('/api/admin/contact-messages/' + msg.id + '/read', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': CsrfModule.getCsrfToken()
        },
        body: JSON.stringify({ is_read: true })
      }).then(function () {
        loadMessages(msgPage);
      });
    }
  }

  function closeModal() {
    document.getElementById('contact-msg-modal').classList.add('hidden-section');
  }

  async function loadMessages(page) {
    if (page !== undefined) msgPage = page;
    var url = '/api/admin/contact-messages?page=' + msgPage;
    if (activeFilter !== 'all') {
      url += '&status=' + activeFilter;
    }

    var resp = await fetch(url, { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } });
    var data = await resp.json();
    var tbody = document.getElementById('contact-msgs-tbody');

    if (data.messages.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty-cell">Aucun message</td></tr>';
    } else {
      tbody.innerHTML = data.messages.map(function (m) {
        var statusBadge = m.is_read
          ? '<span class="badge badge-verified">Lu</span>'
          : '<span class="badge badge-pending">Non lu</span>';
        return '<tr class="' + (m.is_read ? '' : 'contact-msg-unread') + '">' +
          '<td data-label="ID">' + m.id + '</td>' +
          '<td data-label="Nom">' + escapeHtml(m.name) + '</td>' +
          '<td data-label="Email">' + escapeHtml(m.email) + '</td>' +
          '<td data-label="Sujet">' + escapeHtml(m.subject) + '</td>' +
          '<td data-label="Message">' + escapeHtml(m.message).substring(0, 80) + (m.message.length > 80 ? '...' : '') + '</td>' +
          '<td data-label="Statut">' + statusBadge + '</td>' +
          '<td data-label="Date">' + (m.created_at ? new Date(m.created_at).toLocaleDateString('fr-FR') : '-') + '</td>' +
          '<td data-label="Action"><div class="admin-actions-cell">' +
            '<button type="button" class="admin-btn-action btn-green" data-view-msg="' + m.id + '" data-msg=\'' + JSON.stringify(m).replace(/'/g, '&#39;') + '\'>Voir</button>' +
            '<button type="button" class="admin-btn-action btn-danger" data-delete-msg="' + m.id + '">Supprimer</button>' +
          '</div></td>' +
          '</tr>';
      }).join('');
    }

    renderPagination(data);
  }

  // Filter buttons
  document.querySelectorAll('#contact-msg-filters button').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('#contact-msg-filters button').forEach(function (b) { b.classList.remove('active'); });
      this.classList.add('active');
      activeFilter = this.dataset.filter;
      msgPage = 1;
      loadMessages();
    });
  });

  // Pagination
  var pagDiv = document.getElementById('contact-msgs-pagination');
  if (pagDiv) {
    pagDiv.addEventListener('click', function (e) {
      e.preventDefault();
      var link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
      if (!link) return;
      var page = parseInt(link.dataset.page);
      loadMessages(page);
    });
  }

  // View message (open modal)
  document.getElementById('contact-msgs-tbody').addEventListener('click', function (e) {
    var btn = e.target.closest('button[data-view-msg]');
    if (!btn) return;
    var msg = JSON.parse(btn.dataset.msg);
    openModal(msg);
  });

  // Delete message
  document.getElementById('contact-msgs-tbody').addEventListener('click', function (e) {
    var btn = e.target.closest('button[data-delete-msg]');
    if (!btn) return;
    if (!confirm('Supprimer définitivement ce message ?')) return;
    var msgId = btn.dataset.deleteMsg;
    fetch('/api/admin/contact-messages/' + msgId, {
      method: 'DELETE',
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
    }).then(function (r) {
      if (r.ok) loadMessages();
    });
  });

  // Modal close
  document.getElementById('contact-msg-modal-close').addEventListener('click', closeModal);
  document.getElementById('contact-msg-modal').addEventListener('click', function (e) {
    if (e.target === this) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  loadMessages();
})();