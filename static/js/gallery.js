/**
 * A.N.A.N.A.S. — Gallery module
 * - Detail page inline: simple image strip, click to swap main image
 */

/* ==========================================================================
 * Inline gallery (detail page — Cdiscount style image swap)
 * ========================================================================== */
function initInlineGallery() {
  var thumbStrip = document.getElementById("inlineGallery");
  if (!thumbStrip) return;

  var thumbs = thumbStrip.querySelectorAll(".gallery-thumb-img");
  var mainImg = document.getElementById("mainProductImg");
  if (!mainImg || !thumbs.length) return;

  thumbs.forEach(function (thumb) {
    thumb.addEventListener("click", function () {
      // Remove active from all thumbnails
      thumbs.forEach(function (t) { t.classList.remove("active"); });
      // Add active to clicked thumbnail
      this.classList.add("active");
      // Swap main image
      var newSrc = this.getAttribute("data-src");
      if (newSrc) {
        mainImg.style.opacity = "0";
        setTimeout(function () {
          mainImg.src = newSrc;
          mainImg.addEventListener("load", function () {
            mainImg.style.opacity = "1";
          }, { once: true });
          // If image is cached, force reload by appending a random param
          mainImg.src = newSrc + "?t=" + Date.now();
          mainImg.style.opacity = "1";
        }, 150);
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", function () {

  // ── Inline gallery init ──
  initInlineGallery();

  // ── Copy magnet buttons ──
  var copyBtns = document.querySelectorAll("[data-magnet]");
  copyBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var magnet = btn.getAttribute("data-magnet");
      if (!magnet) return;
      navigator.clipboard.writeText(magnet).then(function () {
        var original = btn.innerHTML;
        btn.textContent = "Copié !";
        setTimeout(function () {
          btn.innerHTML = original;
        }, 2000);
      });
    });
  });

  // ── Star rating hover + selection ──
  var rateForms = document.querySelectorAll(".rate-form");
  rateForms.forEach(function (form) {
    var stars = form.querySelectorAll(".rate-stars label");
    var inputs = form.querySelectorAll(".rate-stars input");

    stars.forEach(function (star, idx) {
      star.addEventListener("mouseenter", function () {
        stars.forEach(function (s, i) {
          s.style.color = i <= idx ? "#daa520" : "#d5d5d5";
        });
      });

      star.addEventListener("mouseleave", function () {
        var checkedIdx = Array.from(inputs).findIndex(function (inp) { return inp.checked; });
        stars.forEach(function (s, i) {
          s.style.color = checkedIdx >= 0 && i <= checkedIdx ? "#daa520" : "";
        });
      });

      star.addEventListener("click", function () {
        form.querySelector('[name="rating"]').value = idx + 1;
        stars.forEach(function (s, i) {
          if (i <= idx) {
            s.style.color = "#daa520";
            inputs[i].checked = true;
          } else {
            s.style.color = "#d5d5d5";
          }
        });
      });
    });
  });

});
