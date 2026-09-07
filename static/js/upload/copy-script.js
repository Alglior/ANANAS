/**
 * A.N.A.N.A.S — Upload : bouton copier le script bulk
 */
UploadModule.copyScript = (function () {
  function init() {
    var btn = document.querySelector('.copy-script-btn');
    var code = document.getElementById('bulkUploadScript');
    if (!btn || !code) return;

    btn.addEventListener('click', function () {
      var text = code.textContent;
      
      // Méthode 1 : Clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          btn.textContent = 'Copié !';
          setTimeout(function () { btn.textContent = 'Copier'; }, 1500);
        }).catch(function () {
          fallbackCopy(text, btn);
        });
      } else {
        fallbackCopy(text, btn);
      }
    });
  }

  function fallbackCopy(text, btn) {
    // Méthode 2 : textarea temporaire
    var textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      btn.textContent = 'Copié !';
      setTimeout(function () { btn.textContent = 'Copier'; }, 1500);
    } catch (e) {
      btn.textContent = 'Erreur';
      setTimeout(function () { btn.textContent = 'Copier'; }, 1500);
    }
    document.body.removeChild(textarea);
  }

  return { init: init };
})();
