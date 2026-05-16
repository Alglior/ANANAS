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
      'item_published': 'Élément publié',
      'item_unpublished': 'Élément masqué',
      'item_verified': 'Élément vérifié',
      'item_unverified': 'Vérification retirée',
      'report_resolved': 'Signalement traité',
      'report_dismissed': 'Signalement ignoré',
    };
    return map[action] || action;
  }

  function actionColor(action) {
    const colors = {
      'ban': '#dc3545',
      'unban': '#0d6efd',
      'comment_deleted': '#dc3545',
      'item_deleted': '#dc3545',
      'item_published': '#198754',
      'item_unpublished': '#6c757d',
      'item_verified': '#198754',
      'item_unverified': '#ffc107',
      'report_resolved': '#198754',
      'report_dismissed': '#6c757d',
    };
    return colors[action] || '#6c757d';
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

  async function loadAudit() {
    const resp = await fetch('/api/admin/audit');
    const data = await resp.json();
    const tbody = document.getElementById('audit-tbody');
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty-cell">Aucune entrée</td></tr>';
    } else {
      tbody.innerHTML = data.map(e => `
        <tr>
          <td data-label="Date">${new Date(e.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
          <td data-label="Admin">${e.admin && e.admin.name ? escapeHtml(e.admin.name) : '(inconnu)'}</td>
          <td data-label="Action"><span class="badge" style="background:${actionColor(e.action_type)};color:#fff;">${escapeHtml(actionBadgeLabel(e.action_type))}</span></td>
          <td data-label="Cible">${escapeHtml(targetLabel(e))}</td>
        </tr>
      `).join('');
    }
  }

  loadAudit();
})();
