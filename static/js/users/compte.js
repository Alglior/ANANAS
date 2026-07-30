/**
 * A.N.A.N.A.S — Compte : profile form, password form, avatar upload, publication delete
 */
(function () {
  var csrfToken = CsrfModule.getCsrfToken();
  var csrfInput = document.querySelector('input[name="_csrf_token"]');
  var csrfTokenForm = csrfInput ? csrfInput.value : csrfToken;

  /* ── Avatar upload ── */
  var avatarInput = document.getElementById('avatarInput');
  var avatarPreview = document.getElementById('avatarPreview');
  if (avatarInput && avatarPreview) {
    avatarInput.addEventListener('change', function () {
      var file = this.files[0];
      if (!file) return;

      var formData = new FormData();
      formData.append('avatar', file);
      formData.append('_csrf_token', csrfTokenForm);

      fetch('/api/users/avatar', {
        method: 'POST',
        headers: { 'X-CSRF-Token': csrfToken },
        body: formData,
      }).then(function (resp) { return resp.json(); })
        .then(function (data) {
          if (data.avatar_path) {
            avatarPreview.src = data.avatar_path + '?t=' + Date.now();
          }
        }).catch(function () {});
    });
  }

  /* ── Profile form ── */
  function initProfileForm() {
    var form = document.getElementById('profileForm');
    var status = document.getElementById('profileStatus');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      status.textContent = 'Sauvegarde...';
      status.className = 'form-status';

      try {
        var resp = await fetch('/api/users/profile', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
          body: JSON.stringify({
            prenom: document.getElementById('prenom').value,
            nom: document.getElementById('nom').value,
          }),
        });
        var data = await resp.json();
        if (resp.ok) {
          status.textContent = 'Profil sauvegardé !';
          status.className = 'form-status form-success';
        } else {
          status.textContent = data.error || 'Erreur';
          status.className = 'form-status form-error';
        }
      } catch (err) {
        status.textContent = 'Erreur réseau';
        status.className = 'form-status form-error';
      }
    });
  }

  /* ── Password form ── */
  function initPasswordForm() {
    var form = document.getElementById('passwordForm');
    if (!form) return;
    var status = document.getElementById('passwordStatus');

    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      var newPw = document.getElementById('new_password').value;
      var confirmPw = document.getElementById('confirm_password').value;

      if (newPw !== confirmPw) {
        status.textContent = 'Les mots de passe ne correspondent pas';
        status.className = 'form-status form-error';
        return;
      }

      try {
        var resp = await fetch('/api/users/change-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
          body: JSON.stringify({
            current_password: document.getElementById('current_password').value,
            new_password: newPw,
          }),
        });
        var data = await resp.json();
        if (resp.ok) {
          status.textContent = 'Mot de passe modifié !';
          status.className = 'form-status form-success';
          document.getElementById('current_password').value = '';
          document.getElementById('new_password').value = '';
          document.getElementById('confirm_password').value = '';
        } else {
          status.textContent = data.error || (data.details ? data.details.join('; ') : 'Erreur');
          status.className = 'form-status form-error';
        }
      } catch (err) {
        status.textContent = 'Erreur réseau';
        status.className = 'form-status form-error';
      }
    });

    var newPassInput = document.getElementById('new_password');
    if (newPassInput) {
      function toggleReq(id, met) {
        var el = document.getElementById(id);
        if (el) el.classList.toggle('req-met', met);
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
  }

  /* ── Publication delete ── */
  function showConfirm(message, onConfirm) {
    var overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = '<div class="confirm-dialog"><p>' + message + '</p><div class="confirm-actions"><button class="btn-cancel">Annuler</button><button class="btn-danger">Supprimer</button></div></div>';
    document.body.appendChild(overlay);
    overlay.querySelector('.btn-cancel').addEventListener('click', function () { overlay.remove(); });
    overlay.querySelector('.btn-danger').addEventListener('click', function () { overlay.remove(); onConfirm(); });
    overlay.addEventListener('click', function (ev) { if (ev.target === overlay) overlay.remove(); });
  }

  document.addEventListener('click', function (e) {
    var delBtn = e.target.closest('.publication-delete-btn');
    if (!delBtn) return;
    e.preventDefault();
    var id = delBtn.getAttribute('data-id');
    showConfirm(
      'Mettre cette publication \u00e0 la corbeille ?<br><small>Elle ne sera plus visible dans le catalogue et restera r\u00e9cup\u00e9rable pendant 7 jours.</small>',
      function () {
        fetch('/api/upload/item/' + id, {
          method: 'DELETE',
          headers: { 'X-CSRF-Token': csrfToken },
        }).then(function (resp) {
          if (resp.ok) window.location.reload();
        });
      }
    );
  });

  /* ── Init ── */
  initProfileForm();
  initPasswordForm();
})();