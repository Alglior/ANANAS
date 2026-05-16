(function () {
  var csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';

  function initProfileForm() {
    var profileForm = document.getElementById('profileForm');
    var profileStatus = document.getElementById('profileStatus');
    if (!profileForm) return;

    profileForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      profileStatus.textContent = 'Sauvegarde...';
      profileStatus.className = 'form-status';

      var formData = {
        prenom: document.getElementById('prenom').value,
        nom: document.getElementById('nom').value,
        email: document.getElementById('email').value,
      };

      try {
        var response = await fetch('/api/users/profile', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken,
          },
          body: JSON.stringify(formData),
        });

        var data = await response.json();

        if (response.ok) {
          profileStatus.textContent = 'Profil sauvegardé !';
          profileStatus.className = 'form-status form-success';
        } else {
          profileStatus.textContent = data.error || 'Erreur lors de la sauvegarde';
          profileStatus.className = 'form-status form-error';
        }
      } catch (err) {
        profileStatus.textContent = 'Erreur réseau';
        profileStatus.className = 'form-status form-error';
      }
    });
  }

  function initPasswordForm() {
    var passwordForm = document.getElementById('passwordForm');
    if (!passwordForm) return;

    passwordForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      var newPw = document.getElementById('new_password').value;
      var confirmPw = document.getElementById('confirm_password').value;

      if (newPw !== confirmPw) {
        document.getElementById('passwordStatus').textContent = 'Les mots de passe ne correspondent pas';
        document.getElementById('passwordStatus').className = 'form-status form-error';
        return;
      }

      var formData = {
        current_password: document.getElementById('current_password').value,
        new_password: newPw,
      };

      try {
        var response = await fetch('/api/users/change-password', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken,
          },
          body: JSON.stringify(formData),
        });

        var data = await response.json();

        if (response.ok) {
          document.getElementById('passwordStatus').textContent = 'Mot de passe modifié !';
          document.getElementById('passwordStatus').className = 'form-status form-success';
          document.getElementById('current_password').value = '';
          document.getElementById('new_password').value = '';
          document.getElementById('confirm_password').value = '';
        } else {
          document.getElementById('passwordStatus').textContent = data.error || (data.details ? data.details.join('; ') : 'Erreur');
          document.getElementById('passwordStatus').className = 'form-status form-error';
        }
      } catch (err) {
        document.getElementById('passwordStatus').textContent = 'Erreur réseau';
        document.getElementById('passwordStatus').className = 'form-status form-error';
      }
    });

    var newPassInput = document.getElementById('new_password');
    if (!newPassInput) return;

    function toggleReq(id, met) {
      var el = document.getElementById(id);
      if (el) {
        el.classList.toggle('req-met', met);
      }
    }

    newPassInput.addEventListener('input', function () {
      var val = this.value;
      toggleReq('req-length', val.length >= 8);
      toggleReq('req-upper', /[A-Z]/.test(val));
      toggleReq('req-lower', /[a-z]/.test(val));
      toggleReq('req-digit', /\d/.test(val));
      toggleReq('req-special', /[!@#$%^&*()_+\-={}\[\];':\\|,.<>\/?~`]/.test(val));
    });
  }

  if (window.DOCUMENT_READY_HANDLERS) {
    window.DOCUMENT_READY_HANDLERS.push(function () { initProfileForm(); initPasswordForm(); });
  } else {
    document.addEventListener('DOMContentLoaded', function () { initProfileForm(); initPasswordForm(); });
  }
})();
