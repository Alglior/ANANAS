/**
 * A.N.A.N.A.S — CSRF token utility
 * Reads the token from a non-HttpOnly cookie set by the server.
 */
var CsrfModule = (function () {
  function getCsrfToken() {
    var name = 'csrf_token=';
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var c = cookies[i].trim();
      if (c.indexOf(name) === 0) {
        return decodeURIComponent(c.substring(name.length));
      }
    }
    return '';
  }

  return {
    getCsrfToken: getCsrfToken
  };
})();