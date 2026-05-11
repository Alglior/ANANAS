/**
 * A.N.A.N.A.S. — Gallery module
 * - Detail page inline: simple image strip, click to swap main image
 * - Detail page modal: click product image to open full-screen gallery
 */

/* ==========================================================================
 * Inline gallery (detail page — image strip)
 * ========================================================================== */
function initInlineGallery() {
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

/* ==========================================================================
 * Image modal (detail page — full-screen gallery)
 * ========================================================================== */
function initImageModal() {
  var modal = document.getElementById("imageModal");
  if (!modal) return;

  var mainImg = document.getElementById("mainProductImg");
  if (!mainImg) return;

  var modalImg = modal.querySelector(".modal-img");
  if (!modalImg) return;

  var backdrop = modal.querySelector(".modal-backdrop");
  var closeBtn = modal.querySelector(".modal-close");
  var prevBtn = modal.querySelector(".modal-prev");
  var nextBtn = modal.querySelector(".modal-next");
  var thumbContainer = modal.querySelector(".modal-thumbnails");

  // Build image list from inline gallery thumbnails and modal thumbs
  var images = [];
  var currentIndex = 0;
  var seenUrls = {};

  function addImage(src) {
    if (!src) return;
    if (seenUrls[src]) return;
    seenUrls[src] = true;
    images.push(src);
  }

  // Start with main product image source (raw attribute, not resolved URL)
  var rawSrc = mainImg.getAttribute("src");
  addImage(rawSrc);

  // Collect from inline gallery thumbs
  var inlineGallery = document.getElementById("inlineGallery");
  if (inlineGallery) {
    var iThumbs = inlineGallery.querySelectorAll(".gallery-thumb-img");
    for (var i = 0; i < iThumbs.length; i++) {
      addImage(iThumbs[i].getAttribute("data-src"));
    }
  }

  // Collect from modal thumbs
  if (thumbContainer) {
    var mThumbs = thumbContainer.querySelectorAll(".modal-thumb");
    for (var j = 0; j < mThumbs.length; j++) {
      addImage(mThumbs[j].getAttribute("src"));
    }
  }

  // Ensure at least one image
  if (images.length === 0) {
    images.push(rawSrc);
  }

  function updateActiveThumb() {
    if (!thumbContainer) return;
    var thumbs = thumbContainer.querySelectorAll(".modal-thumb");
    for (var i = 0; i < thumbs.length; i++) {
      var idx = parseInt(thumbs[i].getAttribute("data-index"), 10);
      if (!isNaN(idx) && idx === currentIndex) {
        thumbs[i].classList.add("active");
        thumbs[i].scrollIntoView({ behavior: "smooth", block: "nearest" });
      } else {
        thumbs[i].classList.remove("active");
      }
    }

    var showNav = images.length > 1;
    if (prevBtn) prevBtn.style.display = showNav ? "flex" : "none";
    if (nextBtn) nextBtn.style.display = showNav ? "flex" : "none";
  }

  function showModal(index) {
    if (typeof index === "number" && !isNaN(index)) {
      currentIndex = Math.min(index, images.length - 1);
    }
    modalImg.setAttribute("src", images[currentIndex]);
    modal.style.display = "flex";
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    updateActiveThumb();
  }

  function hideModal() {
    modal.style.display = "none";
    modal.classList.remove("open");
    document.body.style.overflow = "";
  }

  function navigate(direction) {
    if (images.length <= 1) return;
    currentIndex = (currentIndex + direction + images.length) % images.length;
    modalImg.setAttribute("src", images[currentIndex]);
    updateActiveThumb();
  }

  // Main image click opens modal
  mainImg.addEventListener("click", function () {
    currentIndex = 0;
    showModal();
  });

  // Close handlers
  if (backdrop) backdrop.addEventListener("click", hideModal);
  if (closeBtn) closeBtn.addEventListener("click", hideModal);
  if (prevBtn) prevBtn.addEventListener("click", function () { navigate(-1); });
  if (nextBtn) nextBtn.addEventListener("click", function () { navigate(1); });

  // Thumbnail clicks via data-index
  if (thumbContainer) {
    var allThumbs = thumbContainer.querySelectorAll(".modal-thumb");
    for (var k = 0; k < allThumbs.length; k++) {
      (function (idx) {
        allThumbs[idx].addEventListener("click", function () {
          currentIndex = Math.min(idx, images.length - 1);
          showModal();
        });
      })(k);
    }
  }

  // Keyboard controls
  document.addEventListener("keydown", function (e) {
    if (!modal.classList.contains("open")) return;
    if (e.key === "Escape") hideModal();
    else if (e.key === "ArrowLeft") navigate(-1);
    else if (e.key === "ArrowRight") navigate(1);
  });

  // Touch swipe support
  var touchStartX = 0;
  var touchEndX = 0;
  modalImg.addEventListener("touchstart", function (e) {
    touchStartX = e.changedTouches[0].screenX;
  }, { passive: true });
  modalImg.addEventListener("touchend", function (e) {
    touchEndX = e.changedTouches[0].screenX;
    var diff = touchStartX - touchEndX;
    if (Math.abs(diff) > 60) {
      if (diff > 0) navigate(1);
      else navigate(-1);
    }
  }, { passive: true });
}

document.addEventListener("DOMContentLoaded", function () {

  // ── Inline gallery init ──
  initInlineGallery();

  // ── Image modal init ──
  initImageModal();

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
