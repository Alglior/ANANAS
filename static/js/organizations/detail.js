/**
 * A.N.A.N.A.S. — Organization detail : join/leave, roles, members, invites
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

    document.querySelectorAll('.role-select').forEach(function (sel) {
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

    document.querySelectorAll('.btn-remove-member').forEach(function (rmBtn) {
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
        var email = document.getElementById('inviteEmail').value.trim();
        if (!email) return;
        fetch('/api/organizations/' + slug + '/invite', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': CsrfModule.getCsrfToken()
          },
          body: JSON.stringify({ email: email })
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
  });
})();