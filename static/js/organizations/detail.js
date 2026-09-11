/**
 * A.N.A.N.A.S — Organization detail : join/leave, roles, members, invites
 */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('orgActionBtn');
    var slug = btn ? btn.getAttribute('data-slug') : '';
    if (btn) {
      btn.addEventListener('click', function () {
        var joined = btn.getAttribute('data-joined') === '1';
        var action = joined ? 'leave' : 'join';
        fetch('/api/organizations/' + slug + '/' + action, {
          method: 'POST',
          headers: { 'X-CSRF-TOKEN': CsrfModule.getCsrfToken() }
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            if (data.status === 'requested') {
              alert(data.message);
              btn.textContent = 'Demande envoy\u00e9e';
              btn.disabled = true;
              btn.classList.remove('org-btn-outline');
              btn.classList.add('org-btn-disabled');
              return;
            }
            location.reload();
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
      });
    }

    var deleteBtn = document.getElementById('orgDeleteBtn');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', function () {
        if (!confirm('Supprimer d\u00e9finitivement cette organisation ? Cette action est irr\u00e9versible.')) return;
        fetch('/api/organizations/' + slug, {
          method: 'DELETE',
          headers: { 'X-CSRF-TOKEN': CsrfModule.getCsrfToken() }
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            window.location.href = '/organizations';
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
      });
    }

    document.querySelectorAll('.org-role-select').forEach(function (sel) {
      sel.addEventListener('change', function () {
        var userId = sel.getAttribute('data-user-id');
        var val = sel.value;
        var body = {};
        if (val.startsWith('custom:')) {
          body.custom_role_id = parseInt(val.split(':')[1]);
        } else {
          body.role = val;
        }
        fetch('/api/organizations/' + slug + '/members/' + userId + '/role', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': CsrfModule.getCsrfToken()
          },
          body: JSON.stringify(body)
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            location.reload();
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
      });
    });

    document.querySelectorAll('.org-remove-btn').forEach(function (rmBtn) {
      rmBtn.addEventListener('click', function () {
        if (!confirm('Retirer ce membre de l\'organisation ?')) return;
        var userId = rmBtn.getAttribute('data-user-id');
        fetch('/api/organizations/' + slug + '/members/' + userId, {
          method: 'DELETE',
          headers: { 'X-CSRF-TOKEN': CsrfModule.getCsrfToken() }
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            location.reload();
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
      });
    });

    var inviteToggle = document.getElementById('inviteToggleBtn');
    var inviteForm = document.getElementById('inviteForm');
    var cancelInvite = document.getElementById('cancelInviteBtn');

    if (inviteToggle && inviteForm) {
      inviteToggle.addEventListener('click', function () {
        inviteForm.classList.remove('form-hidden');
        inviteToggle.classList.add('form-hidden');
      });
    }
    if (cancelInvite && inviteForm) {
      cancelInvite.addEventListener('click', function () {
        inviteForm.classList.add('form-hidden');
        inviteToggle.classList.remove('form-hidden');
        inviteForm.reset();
      });
    }
    if (inviteForm) {
      inviteForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var pseudo = document.getElementById('invitePseudo').value.trim();
        if (!pseudo) return;
        fetch('/api/organizations/' + slug + '/invite', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': CsrfModule.getCsrfToken()
          },
          body: JSON.stringify({ pseudo: pseudo })
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            location.reload();
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
      });
    }

    var rolesToggle = document.getElementById('rolesToggleBtn');
    var rolesPanel = document.getElementById('rolesPanel');
    if (rolesToggle && rolesPanel) {
      rolesToggle.addEventListener('click', function () {
        if (rolesPanel.classList.contains('form-hidden')) {
          rolesPanel.classList.remove('form-hidden');
          rolesToggle.textContent = 'Masquer les r\u00f4les';
        } else {
          rolesPanel.classList.add('form-hidden');
          rolesToggle.textContent = 'G\u00e9rer les r\u00f4les';
        }
      });
    }

    var createRoleForm = document.getElementById('createRoleForm');
    if (createRoleForm) {
      createRoleForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var name = document.getElementById('roleName').value.trim();
        if (!name) return;
        var perms = [];
        createRoleForm.querySelectorAll('input[name="permissions"]:checked').forEach(function (cb) {
          perms.push(cb.value);
        });
        fetch('/api/organizations/' + slug + '/roles', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': CsrfModule.getCsrfToken()
          },
          body: JSON.stringify({ name: name, permissions: perms })
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            location.reload();
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
      });
    }

    document.querySelectorAll('.delete-role-btn').forEach(function (delBtn) {
      delBtn.addEventListener('click', function () {
        if (!confirm('Supprimer ce r\u00f4le personnalis\u00e9 ? Les membres concern\u00e9s redeviendront "membre".')) return;
        var roleId = delBtn.getAttribute('data-role-id');
        fetch('/api/organizations/' + slug + '/roles/' + roleId, {
          method: 'DELETE',
          headers: { 'X-CSRF-TOKEN': CsrfModule.getCsrfToken() }
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            location.reload();
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
      });
    });

    var requestsList = document.getElementById('joinRequestsList');
    if (requestsList) {
      fetch('/api/organizations/' + slug + '/requests', {
        headers: { 'X-CSRF-TOKEN': CsrfModule.getCsrfToken() }
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (!data.length) return;
          requestsList.innerHTML = '';
          data.forEach(function (req) {
            var div = document.createElement('div');
            div.className = 'org-request-row';
            div.innerHTML =
              '<span class="org-request-user">' + req.user_name + ' (@' + req.user_pseudo + ')</span>' +
              '<span class="org-request-date">' + req.created_at + '</span>' +
              '<button class="org-btn org-btn-sm org-btn-primary approve-request-btn" data-request-id="' + req.id + '">Accepter</button>' +
              '<button class="org-btn org-btn-sm org-btn-outline reject-request-btn" data-request-id="' + req.id + '">Refuser</button>';
            requestsList.appendChild(div);
          });
        })
        .catch(function () {});
    }

    document.addEventListener('click', function (e) {
      var approveBtn = e.target.closest('.approve-request-btn');
      if (approveBtn) {
        var reqId = approveBtn.getAttribute('data-request-id');
        fetch('/api/organizations/' + slug + '/requests/' + reqId + '/approve', {
          method: 'POST',
          headers: { 'X-CSRF-TOKEN': CsrfModule.getCsrfToken() }
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            location.reload();
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
        return;
      }

      var rejectBtn = e.target.closest('.reject-request-btn');
      if (rejectBtn) {
        var reqId = rejectBtn.getAttribute('data-request-id');
        if (!confirm('Refuser cette demande d\'acc\u00e8s ?')) return;
        fetch('/api/organizations/' + slug + '/requests/' + reqId + '/reject', {
          method: 'POST',
          headers: { 'X-CSRF-TOKEN': CsrfModule.getCsrfToken() }
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            location.reload();
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
        return;
      }
    });
  });
})();