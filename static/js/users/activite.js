/* users/activite — tab switching */
(function () {
  if (window.DOCUMENT_READY_HANDLERS) {
    window.DOCUMENT_READY_HANDLERS.push(initTabs);
  } else {
    initTabs();
  }

  function initTabs() {
    var tabs = document.querySelectorAll('.tab-btn');
    var panels = document.querySelectorAll('.tab-panel');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('tab-active'); });
        panels.forEach(function (p) { p.classList.remove('tab-panel-active'); });
        tab.classList.add('tab-active');
        var panelId = 'panel-' + tab.getAttribute('data-tab');
        document.getElementById(panelId).classList.add('tab-panel-active');
      });
    });
  }
})();
