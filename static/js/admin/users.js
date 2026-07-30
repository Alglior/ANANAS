/**
 * A.N.A.N.A.S — Admin users : ban / tempban / mute / warn / kick actions
 */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var modal = document.getElementById('user-action-modal');
    var modalTitle = document.getElementById('user-action-modal-title');
    var modalClose = document.getElementById('user-action-modal-close');
    var modalCancel = document.getElementById('user-action-cancel');
    var actionId = document.getElementById('user-action-id');
    var actionType = document.getElementById('user-action-type');
    var durationGroup = document.getElementById('user-action-duration-group');
    var reasonGroup = document.getElementById('user-action-reason-group');
    var durationInput = document.getElementById('user-action-duration');
    var reasonInput = document.getElementById('user-action-reason');
    var errorDiv = document.getElementById('user-action-error');
    var form = document.getElementById('user-action-form');

    var actionLabels = {
      'ban': 'Bannir d\u00e9finitivement cet utilisateur ?',
      'tempban': 'Bannir temporairement',
      'mute': 'Mute temporaire',
      'warn': 'Avertir l\'utilisateur',
      'kick': 'D\u00e9connecter l\'utilisateur',
      'unban': 'D\u00e9bannir',
      'unmute': 'D\u00e9mute',
      'unwarn': 'Effacer les avertissements',
    };

    document.querySelectorAll('.admin-user-action').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var userId = btn.getAttribute('data-user-id');
        var action = btn.getAttribute('data-action');
        actionId.value = userId;
        actionType.value = action;
        modalTitle.textContent = actionLabels[action] || action;
        errorDiv.classList.add('hidden-section');

        if (action === 'tempban' || action === 'mute') {
          durationGroup.classList.remove('hidden-section');
          reasonGroup.classList.add('hidden-section');
        } else if (action === 'warn') {
          durationGroup.classList.add('hidden-section');
          reasonGroup.classList.remove('hidden-section');
        } else {
          durationGroup.classList.add('hidden-section');
          reasonGroup.classList.add('hidden-section');
        }

        if (action === 'ban' || action === 'unban' || action === 'unmute' || action === 'unwarn' || action === 'kick') {
          doAction(userId, action, null, null);
          return;
        }

        modal.classList.remove('hidden-section');
      });
    });

    function doAction(userId, action, duration, reason) {
      var body = { action: action };
      if (duration !== null) body.duration = duration;
      if (reason !== null) body.reason = reason;

      fetch('/api/users/' + userId + '/ban', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-TOKEN': CsrfModule.getCsrfToken()
        },
        body: JSON.stringify(body)
      })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) { errorDiv.textContent = data.error; errorDiv.classList.remove('hidden-section'); return; }
        location.reload();
      })
      .catch(function () { location.reload(); });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var userId = actionId.value;
      var action = actionType.value;
      var duration = durationGroup.classList.contains('hidden-section') ? null : durationInput.value;
      var reason = reasonGroup.classList.contains('hidden-section') ? null : reasonInput.value;
      modal.classList.add('hidden-section');
      doAction(userId, action, duration, reason);
    });

    function closeModal() {
      modal.classList.add('hidden-section');
    }
    modalClose.addEventListener('click', closeModal);
    modalCancel.addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
  });
})();