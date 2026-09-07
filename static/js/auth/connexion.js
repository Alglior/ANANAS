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
      var isPasswordMode = !passwordField.classList.contains('is-hidden');
      if (isPasswordMode) {
        passwordField.classList.add('is-hidden');
        passwordInput.required = false;
        recoveryField.classList.remove('is-hidden');
        recoveryInput.required = true;
        toggleBtn.textContent = 'Utiliser le mot de passe';
      } else {
        recoveryField.classList.add('is-hidden');
        recoveryInput.required = false;
        passwordField.classList.remove('is-hidden');
        passwordInput.required = true;
        toggleBtn.textContent = 'Utiliser un code de récupération';
      }
    });
  }
})();