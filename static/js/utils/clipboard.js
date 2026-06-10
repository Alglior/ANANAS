/**
 * A.N.A.N.A.S. — Clipboard utility shared across modules
 */
var ClipboardModule = (function () {
  function copyText(element, successMsg, duration) {
    var text = element.getAttribute("data-text") || element.getAttribute("data-magnet");
    if (!text && element.textContent.trim()) text = element.textContent.trim();
    if (!text) return Promise.reject(new Error("No text to copy"));

    duration = duration || 2000;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(function () {
        var originalHTML = element.innerHTML;
        if (successMsg) {
          element.textContent = successMsg;
        } else {
          element.textContent = "Copié !";
        }
        setTimeout(function () {
          element.innerHTML = originalHTML;
        }, duration);
      });
    } else {
      return _copyFallback(text).then(function () {
        var originalHTML = element.innerHTML;
        if (successMsg) {
          element.textContent = successMsg;
        } else {
          element.textContent = "Copié !";
        }
        setTimeout(function () {
          element.innerHTML = originalHTML;
        }, duration);
      });
    }
  }

  function _copyFallback(text) {
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); resolve(); }
      catch (e) { reject(e); }
      document.body.removeChild(ta);
    });
  }

  function initCopyBtn(selector, successMsg, duration) {
    var btn = document.querySelector(selector);
    if (!btn) return;

    btn.addEventListener("click", function () {
      copyText(btn, successMsg, duration).catch(function () {
        btn.classList && btn.classList.add("error");
        setTimeout(function () {
          btn.classList && btn.classList.remove("error");
        }, 1500);
      });
    });
  }

  return {
    copyText: copyText,
    initCopyBtn: initCopyBtn
  };
})();
