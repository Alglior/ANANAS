/**
 * A.N.A.N.A.S. — CSRF token utility
 * Reads the token from a hidden input rather than exposing it in <meta> tags.
 */
var CsrfModule = (function () {
  function getCsrfToken() {
    var container = document.getElementById('csrf-token-container');
    if (container) {
      var input = container.querySelector('input[name="_csrf_token"]');
      if (input && input.value) return input.value;
    }
    var forms = document.querySelectorAll('form');
    for (var i = 0; i < forms.length; i++) {
      var input = forms[i].querySelector('input[name="_csrf_token"]');
      if (input && input.value) return input.value;
    }
    var globalInput = document.querySelector('input[name="_csrf_token"]');
    if (globalInput && globalInput.value) return globalInput.value;
    return '';
  }

  return {
    getCsrfToken: getCsrfToken
  };
})();
