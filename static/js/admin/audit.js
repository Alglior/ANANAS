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

  function actionBadgeClass(action) {
    const cls = {
      'ban': 'audit-badge-ban',
      'unban': 'audit-badge-unban',
      'comment_deleted': 'audit-badge-comment_deleted',
      'item_deleted': 'audit-badge-item_deleted',
      'item_published': 'audit-badge-item_published',
      'item_unpublished': 'audit-badge-item_unpublished',
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
          <td data-label="Action"><span class="badge ${actionBadgeClass(e.action_type)}">${escapeHtml(actionBadgeLabel(e.action_type))}</span></td>
          <td data-label="Cible">${escapeHtml(targetLabel(e))}</td>
        </tr>
      `).join('');
    }
  }

  loadAudit();
})();
