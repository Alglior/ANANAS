/**
 * A.N.A.N.A.S — Upload : bouton copier le script bulk
 */
UploadModule.copyScript = (function () {
  function init() {
    var btn = document.querySelector('.copy-script-btn');
    var code = document.getElementById('bulkUploadScript');
    if (!btn || !code) return;

    btn.addEventListener('click', function () {
      navigator.clipboard.writeText(code.textContent).then(function () {
        btn.textContent = 'Copié !';
        setTimeout(function () { btn.textContent = 'Copier'; }, 1500);
      });
    });
  }
  return { init: init };
})();
