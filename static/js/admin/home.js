/**
 * A.N.A.N.A.S — Admin home : tab switching
 */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var tabs = document.querySelectorAll('.admin-home-tabs .mod-tab');
    var contents = document.querySelectorAll('.admin-home-tabs .tab-content');

    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('active'); });
        contents.forEach(function (c) { c.classList.remove('active'); });
        tab.classList.add('active');
        document.getElementById('tab-' + tab.getAttribute('data-tab')).classList.add('active');
      });
    });
  });
})();