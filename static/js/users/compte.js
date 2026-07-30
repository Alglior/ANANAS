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

  /* ── Recovery codes ── */
  function initRecoveryCodes() {
    var generateBtn = document.getElementById('generateRecoveryCodesBtn');
    var downloadBtn = document.getElementById('downloadRecoveryCodesBtn');
    var closeBtn = document.getElementById('closeRecoveryCodesBtn');
    var container = document.getElementById('recoveryCodesContainer');
    var listEl = document.getElementById('recoveryCodesList');
    var ol = document.getElementById('recoveryCodesOl');
    var status = document.getElementById('recoveryStatus');
    var currentCodes = [];

    if (!generateBtn) return;

    generateBtn.addEventListener('click', async function () {
      status.textContent = 'Génération...';
      status.className = 'form-status';

      try {
        var resp = await fetch('/api/users/generate-recovery-codes', {
          method: 'POST',
          headers: { 'X-CSRF-Token': csrfToken },
        });
        var data = await resp.json();

        if (resp.ok) {
          currentCodes = data.codes;
          ol.innerHTML = '';
          currentCodes.forEach(function (code) {
            var li = document.createElement('li');
            li.textContent = code;
            li.className = 'recovery-code-item';
            ol.appendChild(li);
          });
          container.style.display = 'none';
          listEl.style.display = 'block';
          status.textContent = '';
        } else {
          status.textContent = data.error || 'Erreur lors de la génération';
          status.className = 'form-status form-error';
        }
      } catch (err) {
        status.textContent = 'Erreur réseau';
        status.className = 'form-status form-error';
      }
    });

    downloadBtn.addEventListener('click', function () {
      if (currentCodes.length === 0) return;

      var pseudo = document.querySelector('.compte-avatar-pseudo');
      var username = pseudo ? pseudo.textContent.replace('@', '').trim() : 'utilisateur';
      var date = new Date().toLocaleDateString('fr-FR');
      var lines = [
        '=== Codes de récupération A.N.A.N.A.S ===',
        '',
        'Compte : ' + username,
        'Généré le : ' + date,
        '',
        'Conservez ces codes en lieu sûr. Chaque code ne peut être utilisé qu\'une seule fois.',
        '',
        '---',
        '',
      ];
      currentCodes.forEach(function (code) {
        lines.push(code);
      });
      lines.push('');
      lines.push('---');
      lines.push('');

      var blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'recuperation-' + username + '.txt';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });

    closeBtn.addEventListener('click', function () {
      listEl.style.display = 'none';
      container.style.display = 'block';
      currentCodes = [];
    });
  }

  /* ── Init ── */
  initProfileForm();
  initPasswordForm();
  initRecoveryCodes();
})();