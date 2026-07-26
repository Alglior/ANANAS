/* admin/reports page behaviour */
(function () {

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  let reportPage = 1;
  let activeStatusFilter = 'all';

  function renderReportBadge(status) {
    if (status === 'pending') return '<span class="badge badge-pending">En attente</span>';
    if (status === 'resolved') return '<span class="badge badge-verified">Résolu</span>';
    if (status === 'dismissed') return '<span class="badge badge-rejected">Non fondé</span>';
    return status;
  }

  function renderReportRow(r) {
    let targetCell = '';
    const hasItem = r.target_item_id;
    if (hasItem && r.report_type && r.report_type.startsWith('item_')) {
      targetCell = '<td data-label="Cible"><a href="/catalogue/item/' + r.target_item_id + '">' + escapeHtml(r.target_item_id) + '</a></td>';
    } else if (r.reported_user) {
      const name = r.reported_user.name || 'Utilisateur #' + r.reported_user.id;
      targetCell = '<td data-label="Cible">' + escapeHtml(name) + '</td>';
    } else {
      targetCell = '<td data-label="Cible">Inconnu</td>';
    }

    const actions = r.status === 'pending'
      ? '<div class="admin-actions-cell"><button type="button" class="admin-btn-action admin-btn-resolve" data-report-resolve="' + r.id + '">Résoudre</button><button type="button" class="admin-btn-action admin-btn-dismiss" data-report-dismiss="' + r.id + '">Non fondé</button></div>'
      : '\u2014';

    return `
      <tr>
        <td data-label="ID">${r.id}</td>
        <td data-label="Signaleur">${r.reporter ? escapeHtml(r.reporter.name) : '(anonyme)'}</td>
        ${targetCell}
        <td data-label="Type">${escapeHtml(r.report_type)}</td>
        <td data-label="Raison">${escapeHtml(r.reason || '')}</td>
        <td data-label="Statut">${renderReportBadge(r.status)}</td>
        <td data-label="Date">${r.created_at ? new Date(r.created_at).toLocaleDateString('fr-FR') : '-'}</td>
        <td data-label="Action">${actions}</td>
      </tr>
    `;
  }

  function renderReportsTable(reports) {
    const tbody = document.getElementById('reports-tbody');
    if (reports.length === 0) {
      return '<tr><td colspan="8" class="empty-cell">Aucun signalement</td></tr>';
    }
    return reports.map(r => renderReportRow(r)).join('');
  }

function renderReportPagination(data) {
    PaginationModule.renderPagination(data, 'report-pagination', { navClass: 'mod-pagination-nav', ariaLabel: 'Pagination des signalements' });
  }

  async function loadReportsPage(page) {
    if (page !== undefined) reportPage = page;
    let url = '/api/admin/reports?status=' + activeStatusFilter + '&page=' + reportPage;
    try {
      const resp = await fetch(url, { headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() } });
      const data = await resp.json();
      document.getElementById('reports-tbody').innerHTML = renderReportsTable(data.reports);
      renderReportPagination(data);
    } catch (e) {
      console.error('Failed to load reports:', e);
      document.getElementById('reports-tbody').innerHTML = '<tr><td colspan="8" class="empty-cell">Erreur de chargement</td></tr>';
    }
  }

  async function resolveReport(reportId, newStatus) {
    try {
      const resp = await fetch('/api/admin/reports/' + reportId + '/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': CsrfModule.getCsrfToken() },
        body: JSON.stringify({ status: newStatus })
      });
      if (resp.ok) loadReportsPage();
    } catch (e) {
      console.error('Failed to resolve report:', e);
    }
  }

  // Status filter buttons
  document.querySelectorAll('#report-status-filters button').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('#report-status-filters button').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      activeStatusFilter = this.dataset.filter;
      reportPage = 1;
      loadReportsPage(1);
    });
  });

  // Resolve / dismiss buttons via event delegation
  document.getElementById('reports-tbody').addEventListener('click', function (e) {
    const btn = e.target.closest('button[data-report-resolve]');
    if (btn) {
      e.preventDefault();
      return resolveReport(parseInt(btn.dataset.reportResolve), 'resolved');
    }
    const dismissBtn = e.target.closest('button[data-report-dismiss]');
    if (dismissBtn) {
      e.preventDefault();
      return resolveReport(parseInt(dismissBtn.dataset.reportDismiss), 'dismissed');
    }
  });

  // Pagination clicks
  const pagDiv = document.getElementById('report-pagination');
  if (pagDiv) {
    pagDiv.addEventListener('click', function (e) {
      e.preventDefault();
      const link = e.target.closest('a.pagination-link, a.pagination-prev, a.pagination-next');
      if (!link) return;
      const page = parseInt(link.dataset.page);
      loadReportsPage(page);
    });
  }

  // Initial load
  loadReportsPage(1);
})();
