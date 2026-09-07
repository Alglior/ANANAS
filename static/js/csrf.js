/**
 * A.N.A.N.A.S — CSRF token utility
 * Reads the token from a <meta name="csrf-token"> tag set by the server.
 */
var CsrfModule = (function () {
  function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  return {
    getCsrfToken: getCsrfToken
  };
})();