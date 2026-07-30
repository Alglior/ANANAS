(function () {
  var pseudoEl = document.getElementById('newPseudo');
  var copyBtn = document.getElementById('copyPseudoBtn');
  if (pseudoEl && copyBtn) {
    copyBtn.addEventListener('click', function () {
      var text = pseudoEl.textContent.trim();
      if (!text) return;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          var original = copyBtn.textContent;
          copyBtn.textContent = 'Copie !';
          setTimeout(function () { copyBtn.textContent = original; }, 2000);
        });
      }
    });
  }

  var toggleBtn = document.getElementById('toggleRecoveryBtn');
  var passwordField = document.getElementById('passwordField');
  var recoveryField = document.getElementById('recoveryCodeField');
  var passwordInput = document.getElementById('password');
  var recoveryInput = document.getElementById('recovery_code');

  if (toggleBtn && passwordField && recoveryField) {
    toggleBtn.addEventListener('click', function () {
      var isPasswordMode = passwordField.style.display !== 'none';
      if (isPasswordMode) {
        passwordField.style.display = 'none';
        passwordInput.required = false;
        recoveryField.style.display = '';
        recoveryInput.required = true;
        toggleBtn.textContent = 'Utiliser le mot de passe';
      } else {
        recoveryField.style.display = 'none';
        recoveryInput.required = false;
        passwordField.style.display = '';
        passwordInput.required = true;
        toggleBtn.textContent = 'Utiliser un code de récupération';
      }
    });
  }
})();