/**
 * A.N.A.N.A.S. — Copy magnet buttons (detail page)
 */
var CopyMagnetModule = (function () {
  function init() {
    var copyBtns = document.querySelectorAll("[data-magnet]");
    copyBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var magnet = btn.getAttribute("data-magnet");
        if (!magnet) return;
        ClipboardModule.copyText(btn, "Copié !", 2000).catch(function () {
          btn.classList.add("error");
          setTimeout(function () { btn.classList.remove("error"); }, 1500);
        });
      });
    });
  }

  return { init: init };
})();
