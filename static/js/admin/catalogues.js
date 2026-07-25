/**
 * A.N.A.N.A.S. — Admin catalogues : toggle visibility
 */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.toggle-catalogue-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var type = btn.getAttribute('data-type');
        var active = btn.getAttribute('data-active') === 'true';

        fetch('/api/admin/catalogues/' + type + '/toggle', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': CsrfModule.getCsrfToken()
          },
          body: JSON.stringify({ active: !active })
        })
        .then(function () { location.reload(); })
        .catch(function () { location.reload(); });
      });
    });
  });
})();