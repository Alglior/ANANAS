/**
 * A.N.A.N.A.S — Admin : qBittorrent status dashboard
 */
(function () {
  function formatSpeed(bytes) {
    if (!bytes) return '0 B/s';
    var units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    var i = 0;
    while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
    return bytes.toFixed(1) + ' ' + units[i];
  }

  function formatSize(bytes) {
    if (!bytes) return '0 B';
    var units = ['B', 'KB', 'MB', 'GB', 'TB'];
    var i = 0;
    while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
    return bytes.toFixed(1) + ' ' + units[i];
  }

  function formatETA(eta) {
    if (eta <= 0 || eta === 8640000) return '\u2014';
    if (eta < 60) return eta + 's';
    if (eta < 3600) return Math.floor(eta / 60) + 'm';
    return Math.floor(eta / 3600) + 'h';
  }

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function loadStatus() {
    fetch('/api/admin/qbittorrent/status', {
      headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() }
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) {
          document.getElementById('qb-error').textContent = data.error;
          document.getElementById('qb-error').style.display = '';
          document.getElementById('qb-content').style.display = 'none';
          return;
        }
        document.getElementById('qb-error').style.display = 'none';
        document.getElementById('qb-content').style.display = '';

        var t = data.transfer;
        document.getElementById('dlSpeed').textContent = formatSpeed(t.dl_speed);
        document.getElementById('upSpeed').textContent = formatSpeed(t.up_speed);

        var active = data.torrents.filter(function (tor) { return tor.state === 'downloading' || tor.state === 'uploading'; });
        document.getElementById('activeCount').textContent = active.length;
        document.getElementById('totalCount').textContent = data.torrents.length;

        var tbody = document.getElementById('qb-torrents-tbody');
        if (data.torrents.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" class="empty-cell">Aucun torrent</td></tr>';
          return;
        }
        tbody.innerHTML = data.torrents.map(function (tor) {
          var progressClass = tor.progress >= 100 ? 'badge badge-verified' : 'badge badge-pending';
          return '<tr>' +
            '<td>' + escapeHtml(tor.name) + '</td>' +
            '<td><span class="' + progressClass + '">' + tor.progress + '%</span></td>' +
            '<td>' + escapeHtml(tor.state || '\u2014') + '</td>' +
            '<td>' + formatSpeed(tor.dl_speed) + '</td>' +
            '<td>' + formatSpeed(tor.up_speed) + '</td>' +
            '<td>' + formatSize(tor.size) + '</td>' +
            '</tr>';
        }).join('');
      })
      .catch(function () {
        document.getElementById('qb-error').textContent = 'Erreur r\u00e9seau';
        document.getElementById('qb-error').style.display = '';
        document.getElementById('qb-content').style.display = 'none';
      });
  }

  loadStatus();
  setInterval(loadStatus, 5000);
})();