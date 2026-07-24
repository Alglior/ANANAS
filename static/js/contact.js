(function () {
  var form = document.getElementById('contact-form');
  if (!form) return;

  var nameInput = document.getElementById('contact-name');
  var emailInput = document.getElementById('contact-email');
  var subjectInput = document.getElementById('contact-subject');
  var messageInput = document.getElementById('contact-message');
  var submitBtn = document.getElementById('contact-submit');
  var errorEl = document.getElementById('contact-error');
  var successEl = document.getElementById('contact-success');

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    errorEl.classList.add('hidden-section');
    successEl.classList.add('hidden-section');

    var name = nameInput.value.trim();
    var email = emailInput.value.trim();
    var subject = subjectInput.value.trim();
    var message = messageInput.value.trim();

    if (!name || !email || !subject || !message) {
      errorEl.textContent = 'Tous les champs sont requis.';
      errorEl.classList.remove('hidden-section');
      return;
    }

    if (email.indexOf('@') === -1 || email.split('@')[1].indexOf('.') === -1) {
      errorEl.textContent = 'Adresse email invalide.';
      errorEl.classList.remove('hidden-section');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Envoi en cours...';

    fetch('/api/contact', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': typeof CsrfModule !== 'undefined' ? CsrfModule.getCsrfToken() : ''
      },
      body: JSON.stringify({
        name: name,
        email: email,
        subject: subject,
        message: message
      })
    })
    .then(function (resp) { return resp.json(); })
    .then(function (data) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Envoyer';

      if (data.error) {
        errorEl.textContent = data.error;
        errorEl.classList.remove('hidden-section');
        return;
      }

      successEl.textContent = data.message || 'Votre message a bien été envoyé.';
      successEl.classList.remove('hidden-section');
      form.reset();
    })
    .catch(function () {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Envoyer';
      errorEl.textContent = 'Une erreur est survenue. Veuillez réessayer.';
      errorEl.classList.remove('hidden-section');
    });
  });
})();