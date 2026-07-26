/**
 * A.N.A.N.A.S. — Activite : publication delete handler
 */
(function () {
  function showConfirm(message, onConfirm) {
    var overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML =
      '<div class="confirm-dialog"><p>' + message + '</p><div class="confirm-actions"><button class="btn-cancel">Annuler</button><button class="btn-danger">Supprimer</button></div></div>';
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
          headers: { 'X-CSRF-Token': CsrfModule.getCsrfToken() },
        }).then(function (resp) {
          if (resp.ok) window.location.reload();
        });
      }
    );
  });
})();