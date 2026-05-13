/**
 * A.N.A.N.A.S. — Inline gallery (detail page image strip)
 */
var InlineGalleryModule = (function () {
  function init() {
    var thumbStrip = document.getElementById("inlineGallery");
    if (!thumbStrip) return;

    var thumbs = thumbStrip.querySelectorAll(".gallery-thumb-img");
    var mainImg = document.getElementById("mainProductImg");
    if (!mainImg || !thumbs.length) return;

    thumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        thumbs.forEach(function (t) { t.classList.remove("active"); });
        this.classList.add("active");
        var newSrc = this.getAttribute("data-src");
        if (newSrc) {
          mainImg.style.opacity = "0";
          setTimeout(function () {
            mainImg.src = newSrc + "?t=" + Date.now();
            mainImg.addEventListener("load", function () {
              mainImg.style.opacity = "1";
            }, { once: true });
            mainImg.style.opacity = "1";
          }, 150);
        }
      });
    });
  }

  return { init: init };
})();
