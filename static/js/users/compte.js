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
          container.classList.add('is-hidden');
          listEl.classList.remove('is-hidden');
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
      listEl.classList.add('is-hidden');
      container.classList.remove('is-hidden');
      currentCodes = [];
    });
  }

  /* ── 2FA ── */
  function init2FA() {
    var setupBtn = document.getElementById('setupTfaBtn');
    var verifySection = document.getElementById('tfaVerifySection');
    var verifyBtn = document.getElementById('verifyTfaBtn');
    var cancelBtn = document.getElementById('cancelTfaBtn');
    var tfaQr = document.getElementById('tfaQrCode');
    var tfaSecret = document.getElementById('tfaSecretKey');
    var tfaVerifyCode = document.getElementById('tfa_verify_code');
    var tfaVerifyStatus = document.getElementById('tfaVerifyStatus');
    var tfaSetupStatus = document.getElementById('tfaSetupStatus');
    var tfaSetupSection = document.getElementById('tfaSetupSection');
    var tfaEnabledSection = document.getElementById('tfaEnabledSection');
    var disableBtn = document.getElementById('disableTfaBtn');
    var tfaDisablePw = document.getElementById('tfa_disable_password');
    var tfaDisableCode = document.getElementById('tfa_disable_code');
    var tfaDisableStatus = document.getElementById('tfaDisableStatus');

    if (!setupBtn) return;

    var currentSecret = null;

    setupBtn.addEventListener('click', async function () {
      tfaSetupStatus.textContent = 'Configuration...';
      tfaSetupStatus.className = 'form-status';

      try {
        var resp = await fetch('/api/users/2fa/setup', {
          method: 'POST',
          headers: { 'X-CSRF-Token': csrfToken },
        });
        var data = await resp.json();
        if (resp.ok) {
          currentSecret = data.secret;
          tfaQr.src = data.qr_data_uri;
          tfaSecret.textContent = data.secret;
          tfaSetupSection.classList.add('is-hidden');
          verifySection.classList.remove('is-hidden');
          tfaSetupStatus.textContent = '';
        } else {
          tfaSetupStatus.textContent = data.error || 'Erreur';
          tfaSetupStatus.className = 'form-status form-error';
        }
      } catch (err) {
        tfaSetupStatus.textContent = 'Erreur réseau';
        tfaSetupStatus.className = 'form-status form-error';
      }
    });

    verifyBtn.addEventListener('click', async function () {
      var code = tfaVerifyCode.value.trim();
      if (!code) {
        tfaVerifyStatus.textContent = 'Entrez le code à 6 chiffres';
        tfaVerifyStatus.className = 'form-status form-error';
        return;
      }

      tfaVerifyStatus.textContent = 'Vérification...';
      tfaVerifyStatus.className = 'form-status';

      try {
        var resp = await fetch('/api/users/2fa/enable', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
          body: JSON.stringify({ code: code }),
        });
        var data = await resp.json();
        if (resp.ok) {
          verifySection.classList.add('is-hidden');
          tfaEnabledSection.classList.remove('is-hidden');
          tfaSetupSection.classList.add('is-hidden');
          tfaVerifyStatus.textContent = '';
          currentSecret = null;
        } else {
          tfaVerifyStatus.textContent = data.error || 'Erreur';
          tfaVerifyStatus.className = 'form-status form-error';
        }
      } catch (err) {
        tfaVerifyStatus.textContent = 'Erreur réseau';
        tfaVerifyStatus.className = 'form-status form-error';
      }
    });

    cancelBtn.addEventListener('click', function () {
      verifySection.classList.add('is-hidden');
      tfaSetupSection.classList.remove('is-hidden');
      tfaVerifyCode.value = '';
      tfaVerifyStatus.textContent = '';
      currentSecret = null;
    });

    disableBtn.addEventListener('click', async function () {
      var password = tfaDisablePw.value.trim();
      var code = tfaDisableCode.value.trim();

      if (!password) {
        tfaDisableStatus.textContent = 'Entrez votre mot de passe';
        tfaDisableStatus.className = 'form-status form-error';
        return;
      }

      tfaDisableStatus.textContent = 'Désactivation...';
      tfaDisableStatus.className = 'form-status';

      try {
        var resp = await fetch('/api/users/2fa/disable', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
          body: JSON.stringify({ password: password, code: code }),
        });
        var data = await resp.json();
        if (resp.ok) {
          tfaEnabledSection.classList.add('is-hidden');
          tfaSetupSection.classList.remove('is-hidden');
          tfaDisablePw.value = '';
          tfaDisableCode.value = '';
          tfaDisableStatus.textContent = '';
        } else {
          tfaDisableStatus.textContent = data.error || 'Erreur';
          tfaDisableStatus.className = 'form-status form-error';
        }
      } catch (err) {
        tfaDisableStatus.textContent = 'Erreur réseau';
        tfaDisableStatus.className = 'form-status form-error';
      }
    });
  }

  /* ── Init ── */
  initProfileForm();
  initPasswordForm();
  initRecoveryCodes();
  init2FA();
})();