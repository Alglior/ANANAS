var ZoomMagnetModule = (function () {
  function init() {
    var tabs = document.querySelectorAll('.zoom-tab');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var zoom = tab.getAttribute('data-zoom');
        document.querySelectorAll('.zoom-tab').forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');
        document.querySelectorAll('.zoom-panel').forEach(function (p) { p.classList.remove('active'); });
        var panel = document.getElementById('zoomPanel-' + zoom);
        if (panel) {
          panel.classList.add('active');
          showPage(panel, 1);
        }
      });
    });

    document.querySelectorAll('.zoom-panel').forEach(function (panel) {
      initPagination(panel);
    });

    document.querySelectorAll('.btn-copy-all').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var zoom = btn.getAttribute('data-zoom');
        var panel = document.getElementById('zoomPanel-' + zoom);
        if (!panel) return;
        var links = panel.querySelectorAll('[data-magnet]');
        var magnets = [];
        links.forEach(function (el) {
          var m = el.getAttribute('data-magnet');
          if (m) magnets.push(m);
        });
        if (!magnets.length) return;
        var text = magnets.join('\n');
        navigator.clipboard.writeText(text).then(function () {
          var original = btn.textContent;
          btn.textContent = 'Copi\u00e9 !';
          btn.classList.add('copied');
          setTimeout(function () {
            btn.textContent = original;
            btn.classList.remove('copied');
          }, 2000);
        }).catch(function () {
          btn.textContent = 'Erreur';
          setTimeout(function () {
            btn.textContent = 'Tout copier (' + magnets.length + ')';
          }, 1500);
        });
      });
    });
  }

  function initPagination(panel) {
    var nav = panel.querySelector('.zoom-pagination');
    if (!nav) return;
    var prevBtn = nav.querySelector('.pagination-prev');
    var nextBtn = nav.querySelector('.pagination-next');
    var pageLinks = nav.querySelectorAll('.pagination-link');
    var rows = panel.querySelectorAll('.magnet-level-link-row');
    var perPage = parseInt(panel.getAttribute('data-per-page')) || 15;
    var totalPages = Math.max(1, Math.ceil(rows.length / perPage));

    prevBtn.addEventListener('click', function () {
      var active = nav.querySelector('.pagination-link.active');
      if (!active) return;
      var page = parseInt(active.getAttribute('data-page'));
      if (page > 1) showPage(panel, page - 1);
    });

    nextBtn.addEventListener('click', function () {
      var active = nav.querySelector('.pagination-link.active');
      if (!active) return;
      var page = parseInt(active.getAttribute('data-page'));
      if (page < totalPages) showPage(panel, page + 1);
    });

    pageLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        var page = parseInt(link.getAttribute('data-page'));
        showPage(panel, page);
      });
    });
  }

  function showPage(panel, page) {
    var nav = panel.querySelector('.zoom-pagination');
    var rows = panel.querySelectorAll('.magnet-level-link-row');
    var perPage = parseInt(panel.getAttribute('data-per-page')) || 15;
    var totalPages = Math.max(1, Math.ceil(rows.length / perPage));

    rows.forEach(function (row, i) {
      if (i >= (page - 1) * perPage && i < page * perPage) row.classList.remove('hidden');
      else row.classList.add('hidden');
    });

    if (nav) {
      var prevBtn = nav.querySelector('.pagination-prev');
      var nextBtn = nav.querySelector('.pagination-next');
      var pageLinks = nav.querySelectorAll('.pagination-link');

      pageLinks.forEach(function (link) {
        var p = parseInt(link.getAttribute('data-page'));
        if (p === page) link.classList.add('active');
        else link.classList.remove('active');
      });

      if (prevBtn) {
        if (page <= 1) prevBtn.classList.add('disabled');
        else prevBtn.classList.remove('disabled');
      }
      if (nextBtn) {
        if (page >= totalPages) nextBtn.classList.add('disabled');
        else nextBtn.classList.remove('disabled');
      }
    }
  }

  return { init: init };
})();

document.addEventListener('DOMContentLoaded', ZoomMagnetModule.init);