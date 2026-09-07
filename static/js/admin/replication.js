/* Replication admin page */
(function () {
  var urlInput = document.getElementById('remote-url');
  var previewBtn = document.getElementById('preview-btn');
  var fetchBtn = document.getElementById('fetch-btn');
  var previewSection = document.getElementById('replication-preview');
  var previewResults = document.getElementById('preview-results');
  var progressSection = document.getElementById('replication-progress');
  var progressBar = document.getElementById('progress-bar');
  var progressText = document.getElementById('progress-text');
  var resultsSection = document.getElementById('replication-results');
  var resultsContent = document.getElementById('results-content');

  function getSelectedTypes() {
    var checks = document.querySelectorAll('#replication-types input[type="checkbox"]:checked');
    return Array.from(checks).map(function (c) { return c.value; });
  }

  function getCsrf() {
    return typeof CsrfModule !== 'undefined' ? CsrfModule.getCsrfToken() : '';
  }

  function showError(msg) {
    resultsSection.classList.remove('hidden-section');
    resultsContent.innerHTML = '<div class="results-summary"><div class="stat" style="color:#c62828;">' + escapeHtml(msg) + '</div></div>';
  }

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function updateFetchBtn() {
    var url = urlInput.value.trim();
    var types = getSelectedTypes();
    fetchBtn.disabled = !url || types.length === 0;
  }

  urlInput.addEventListener('input', updateFetchBtn);
  document.querySelectorAll('#replication-types input[type="checkbox"]').forEach(function (cb) {
    cb.addEventListener('change', updateFetchBtn);
  });

  previewBtn.addEventListener('click', async function () {
    var url = urlInput.value.trim();
    if (!url) return;

    previewResults.innerHTML = '<p style="color:var(--text-muted,#666);">Chargement...</p>';
    previewSection.classList.remove('hidden-section');

    try {
      var resp = await fetch('/api/admin/replication/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrf() },
        body: JSON.stringify({ url: url }),
      });
      var data = await resp.json();

      if (data.error) {
        previewResults.innerHTML = '<p style="color:#c62828;">Erreur: ' + escapeHtml(data.error) + '</p>';
        return;
      }

      previewResults.innerHTML = data.catalogues.map(function (c) {
        var statusClass = c.reachable ? 'reachable' : 'unreachable';
        var statusText = c.reachable ? 'Accessible' : 'Inaccessible';
        var countText = c.reachable ? c.total_items + ' item(s)' : '—';
        return '<div class="preview-catalogue">' +
          '<span class="cat-name">' + escapeHtml(c.label) + '</span>' +
          '<span class="cat-count">' + countText + '</span>' +
          '<span class="cat-status ' + statusClass + '">' + statusText + '</span>' +
          '</div>';
      }).join('');
    } catch (e) {
      previewResults.innerHTML = '<p style="color:#c62828;">Erreur de connexion: ' + escapeHtml(e.message) + '</p>';
    }
  });

  fetchBtn.addEventListener('click', async function () {
    var url = urlInput.value.trim();
    var types = getSelectedTypes();
    if (!url || types.length === 0) return;

    fetchBtn.disabled = true;
    previewBtn.disabled = true;
    progressSection.classList.remove('hidden-section');
    resultsSection.classList.add('hidden-section');
    progressBar.style.width = '0%';
    progressText.textContent = 'Récupération des données...';

    var startTime = Date.now();
    var progressInterval = setInterval(function () {
      var elapsed = Math.min((Date.now() - startTime) / 30000, 0.95);
      progressBar.style.width = (elapsed * 100) + '%';
    }, 300);

    try {
      var resp = await fetch('/api/admin/replication/fetch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrf() },
        body: JSON.stringify({ url: url, types: types }),
      });
      var data = await resp.json();

      clearInterval(progressInterval);
      progressBar.style.width = '100%';
      progressText.textContent = 'Terminé.';

      if (data.error) {
        showError(data.error);
        return;
      }

      resultsSection.classList.remove('hidden-section');
      displayResults(data);
    } catch (e) {
      clearInterval(progressInterval);
      progressBar.style.width = '100%';
      progressText.textContent = 'Erreur.';
      showError('Erreur réseau: ' + e.message);
    } finally {
      fetchBtn.disabled = false;
      previewBtn.disabled = false;
      setTimeout(function () {
        progressSection.classList.add('hidden-section');
        progressBar.style.width = '0%';
      }, 2000);
    }
  });

  function displayResults(data) {
    var html = '';

    html += '<div class="results-summary">';
    html += '<div class="stat"><strong>' + data.created_count + '</strong> créé(s)</div>';
    html += '<div class="stat"><strong>' + data.skipped_count + '</strong> ignoré(s)</div>';
    html += '<div class="stat"><strong>' + data.error_count + '</strong> erreur(s)</div>';
    html += '</div>';

    if (data.created.length > 0 || data.skipped.length > 0 || data.errors.length > 0) {
      html += '<div class="results-details">';
      html += '<table class="results-table">';
      html += '<thead><tr><th>Statut</th><th>Titre</th><th>Catalogue</th><th>Détail</th></tr></thead><tbody>';

      data.created.forEach(function (item) {
        html += '<tr class="result-created">';
        html += '<td><span class="badge-created">Créé</span></td>';
        html += '<td>' + escapeHtml(item.title) + '</td>';
        html += '<td>' + escapeHtml(item.type) + '</td>';
        html += '<td>ID ' + item.id + '</td>';
        html += '</tr>';
      });

      data.skipped.forEach(function (item) {
        html += '<tr class="result-skipped">';
        html += '<td><span class="badge-skipped">Ignoré</span></td>';
        html += '<td>' + escapeHtml(item.title) + '</td>';
        html += '<td>' + escapeHtml(item.type) + '</td>';
        html += '<td>' + escapeHtml(item.reason) + '</td>';
        html += '</tr>';
      });

      data.errors.forEach(function (err) {
        html += '<tr class="result-error">';
        html += '<td><span class="badge-error">Erreur</span></td>';
        html += '<td colspan="3">' + escapeHtml(err) + '</td>';
        html += '</tr>';
      });

      html += '</tbody></table></div>';
    }

    resultsContent.innerHTML = html;

    resultsContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
})();