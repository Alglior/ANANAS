/* admin/audit page behaviour — card layout like moderation */
(function () {
  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function actionBadgeLabel(action) {
    const map = {
      'ban': 'Utilisateur banni',
      'unban': 'Utilisateur désbanni',
      'comment_deleted': 'Commentaire supprimé',
      'item_deleted': 'Élément supprimé',
      'item_verified': 'Élément vérifié',
      'item_unverified': 'Vérification retirée',
      'report_resolved': 'Signalement traité',
      'report_dismissed': 'Signalement ignoré',
    };
    return map[action] || action;
  }

  function actionBadgeClass(action) {
    const cls = {
      'ban': 'audit-badge-ban',
      'unban': 'audit-badge-unban',
      'comment_deleted': 'audit-badge-comment_deleted',
      'item_deleted': 'audit-badge-item_deleted',
      'item_verified': 'audit-badge-item_verified',
      'item_unverified': 'audit-badge-item_unverified',
      'report_resolved': 'audit-badge-report_resolved',
      'report_dismissed': 'audit-badge-report_dismissed',
    };
    return cls[action] || 'audit-badge-ban';
  }

  function targetLabel(entry) {
    if (entry.target_type && entry.target_id) {
      const typeLabels = {
        'user': 'Utilisateur',
        'item': 'Élément',
        'comment': 'Commentaire',
        'report': 'Signalement',
      };
      return `${typeLabels[entry.target_type] || entry.target_type} #${entry.target_id}`;
    }
    return '—';
  }

  let currentPage = 1;
  let totalPages = 1;

  function buildPaginationHTML(page, total, base_url) {
    if (total <= 1) return '';

    const pages = [];
    if (total <= 7) {
      for (let i = 1; i <= total; i++) pages.push(i);
    } else {
      if (page <= 4) {
        pages.push(1, 2, 3, 4, '...', total);
      } else if (page > total - 5) {
        pages.push(1, '...', total - 3, total - 2, total - 1, total);
      } else {
        pages.push(1, '...', page - 1, page, page + 1, '...', total);
      }
    }

    let html = '<nav class="pagination" aria-label="Pagination">';

    if (page > 1) {
      html += `<a class="btn btn-outline transition-hover pagination-prev" href="${base_url}/${page - 1}">&#9664;&nbsp;Précédent</a>`;
    } else {
      html += `<span class="btn btn-outline pagination-prev disabled">&#9664;&nbsp;Précédent</span>`;
    }

    html += '<div class="pagination-numbers">';
    for (const p of pages) {
      if (p === '...') {
        html += '<span class="pagination-ellipsis">&hellip;</span>';
      } else if (p === page) {
        html += `<span class="pagination-link active">${p}</span>`;
      } else {
        html += `<a class="pagination-link" href="${base_url}/${p}">${p}</a>`;
      }
    }
    html += '</div>';

    if (page < total) {
      html += `<a class="btn btn-outline transition-hover pagination-next" href="${base_url}/${page + 1}">Suivant&nbsp;&#9658;</a>`;
    } else {
      html += `<span class="btn btn-outline pagination-next disabled">Suivant&nbsp;&#9658;</span>`;
    }

    html += '</nav>';
    html += `<p style="margin-top: 12px; color: #666; font-size: 0.85rem;">Page ${page} sur ${total}</p>`;

    return html;
  }

  async function loadAudit(page) {
    const tbody = document.getElementById('audit-tbody');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="4" class="loading-cell">Chargement...</td></tr>';
    }

    const resp = await fetch(`/api/admin/audit?page=${page || 1}`);
    const data = await resp.json();

    if (data.entries.length === 0) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="4" class="empty-cell">Aucune entrée</td></tr>';
      return;
    }

    if (tbody) {
      tbody.innerHTML = data.entries.map(e => `
        <tr>
          <td data-label="Date">${new Date(e.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
          <td data-label="Admin">${e.admin && e.admin.name ? escapeHtml(e.admin.name) : '(inconnu)'}</td>
          <td data-label="Action"><span class="badge ${actionBadgeClass(e.action_type)}">${escapeHtml(actionBadgeLabel(e.action_type))}</span></td>
          <td data-label="Cible">${escapeHtml(targetLabel(e))}</td>
        </tr>
      `).join('');
    }

    const pagDiv = document.getElementById('pagination-audit');
    if (pagDiv) {
      pagDiv.innerHTML = buildPaginationHTML(data.page, data.total_pages, '/admin/audit');
    }

    currentPage = data.page;
    totalPages = data.total_pages;
  }

  loadAudit(1);
})();
