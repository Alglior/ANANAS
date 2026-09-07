(function() {
  var searchInput = document.getElementById('api-search');
  if (!searchInput) return;

  var rows = document.querySelectorAll('.api-row');
  var categories = document.querySelectorAll('.api-category');
  var noResults = document.getElementById('api-no-results');

  function filterEndpoints() {
    var query = searchInput.value.toLowerCase().trim();
    var visibleCount = 0;

    rows.forEach(function(row) {
      var searchData = row.getAttribute('data-search') || '';
      var match = !query || searchData.includes(query);
      row.classList.toggle('is-filtered-out', !match);
      if (match) visibleCount++;
    });

    categories.forEach(function(cat) {
      var visibleRows = cat.querySelectorAll('.api-row:not(.is-filtered-out)');
      var totalRows = cat.querySelectorAll('.api-row').length;
      cat.classList.toggle('is-hidden', visibleRows.length === 0);
    });

    noResults.classList.toggle('is-hidden', visibleCount > 0);
  }

  searchInput.addEventListener('input', filterEndpoints);

  var collapseBtns = document.querySelectorAll('.api-collapse-btn');
  collapseBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var body = btn.closest('.api-category').querySelector('.api-category-body');
      var icon = btn.querySelector('.collapse-icon');
      var isCollapsed = body.classList.contains('is-collapsed');
      body.classList.toggle('is-collapsed');
      icon.classList.toggle('collapsed');
      btn.setAttribute('aria-label', isCollapsed ? 'Replier la categorie' : 'Deplier la categorie');
    });
  });

  var codeBtns = document.querySelectorAll('.api-code-btn');
  codeBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var targetId = btn.getAttribute('data-target');
      var codeRow = document.getElementById(targetId);
      if (!codeRow) return;
      var isVisible = codeRow.classList.contains('is-visible');
      codeRow.classList.toggle('is-visible');
      btn.textContent = isVisible ? 'Voir' : 'Masquer';
    });
  });

  document.querySelectorAll('.code-examples').forEach(function(examples) {
    var tabs = examples.querySelectorAll('.code-tab');
    var panels = examples.querySelectorAll('.code-panel');

    tabs.forEach(function(tab) {
      tab.addEventListener('click', function() {
        var lang = tab.getAttribute('data-lang');
        tabs.forEach(function(t) { t.classList.remove('active'); });
        panels.forEach(function(p) { p.classList.remove('active'); });
        tab.classList.add('active');
        examples.querySelector('.code-panel[data-lang="' + lang + '"]').classList.add('active');
      });
    });
  });

  var copyBtns = document.querySelectorAll('.api-copy-btn');
  copyBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var targetId = btn.getAttribute('data-target');
      var pre = document.getElementById(targetId);
      if (!pre) return;
      var text = pre.textContent.trim();
      if (!text) return;

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
          btn.textContent = 'Copie !';
          btn.classList.add('copied');
          setTimeout(function() {
            btn.textContent = 'Copier';
            btn.classList.remove('copied');
          }, 2000);
        });
      } else {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        try {
          document.execCommand('copy');
          btn.textContent = 'Copie !';
          btn.classList.add('copied');
          setTimeout(function() {
            btn.textContent = 'Copier';
            btn.classList.remove('copied');
          }, 2000);
        } catch (e) {}
        document.body.removeChild(ta);
      }
    });
  });
})();