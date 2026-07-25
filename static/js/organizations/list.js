/**
 * A.N.A.N.A.S. — Organizations : create organization form
 */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var createBtn = document.getElementById('createOrgBtn');
    var cancelBtn = document.getElementById('cancelCreateOrgBtn');
    var form = document.getElementById('createOrgForm');

    if (createBtn && form) {
      createBtn.addEventListener('click', function () {
        form.classList.remove('form-hidden');
        createBtn.classList.add('form-hidden');
      });
    }

    if (cancelBtn && form) {
      cancelBtn.addEventListener('click', function () {
        form.classList.add('form-hidden');
        createBtn.classList.remove('form-hidden');
        form.reset();
      });
    }

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var name = document.getElementById('orgName').value.trim();
        if (!name || name.length < 2) {
          alert('Le nom doit contenir au moins 2 caract\u00e8res.');
          return;
        }

        var payload = {
          name: name,
          description: document.getElementById('orgDescription').value.trim(),
          website_url: document.getElementById('orgWebsite').value.trim()
        };

        fetch('/api/organizations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': CsrfModule.getCsrfToken()
          },
          body: JSON.stringify(payload)
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.error) { alert(data.error); return; }
            window.location.href = '/organizations/' + data.slug;
          })
          .catch(function () { alert('Erreur r\u00e9seau'); });
      });
    }
  });
})();