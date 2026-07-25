/**
 * A.N.A.N.A.S. — Upload : tab switching
 */
UploadModule.tabs = (function () {
  function init() {
    var tabs = document.querySelectorAll('.upload-tab');
    var tabContents = document.querySelectorAll('.upload-tab-content');
    tabs.forEach(function(tab) {
      tab.addEventListener('click', function() {
        var target = this.getAttribute('data-tab');
        tabs.forEach(function(t) { t.classList.remove('active'); });
        tabContents.forEach(function(c) { c.classList.remove('active'); });
        this.classList.add('active');
        var content = document.getElementById('tab-' + target);
        if (content) content.classList.add('active');
      });
    });

    if (window.location.search.indexOf('drafts=1') !== -1) {
      var draftsTab = document.querySelector('.upload-tab[data-tab="drafts"]');
      if (draftsTab) draftsTab.click();
    }
  }

  return { init: init };
})();