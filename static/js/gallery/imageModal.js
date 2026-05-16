/**
 * A.N.A.N.A.S. — Image modal (detail page full-screen gallery)
 */
var ImageModalModule = (function () {
  function init() {
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

    var images = [];
    var currentIndex = 0;
    var seenUrls = {};

    function addImage(src) {
      if (!src) return;
      if (seenUrls[src]) return;
      seenUrls[src] = true;
      images.push(src);
    }

    var rawSrc = mainImg.getAttribute("src");
    addImage(rawSrc);

    var inlineGallery = document.getElementById("inlineGallery");
    if (inlineGallery) {
      var iThumbs = inlineGallery.querySelectorAll(".gallery-thumb-img");
      for (var i = 0; i < iThumbs.length; i++) {
        addImage(iThumbs[i].getAttribute("data-src"));
      }
    }

    if (thumbContainer) {
      var mThumbs = thumbContainer.querySelectorAll(".modal-thumb");
      for (var j = 0; j < mThumbs.length; j++) {
        addImage(mThumbs[j].getAttribute("src"));
      }
    }

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
      if (prevBtn) {
        prevBtn.classList.toggle("modal-nav-hidden", !showNav);
      }
      if (nextBtn) {
        nextBtn.classList.toggle("modal-nav-hidden", !showNav);
      }
    }

    function showModal(index) {
      if (typeof index === "number" && !isNaN(index)) {
        currentIndex = Math.min(index, images.length - 1);
      }
      modalImg.setAttribute("src", images[currentIndex]);
      modal.classList.add("open");
      document.body.classList.add("modal-open");
      updateActiveThumb();
    }

    function hideModal() {
      modal.classList.remove("open", "modal-active");
      document.body.classList.remove("modal-open");
    }

    function navigate(direction) {
      if (images.length <= 1) return;
      currentIndex = (currentIndex + direction + images.length) % images.length;
      modalImg.setAttribute("src", images[currentIndex]);
      updateActiveThumb();
    }

    mainImg.addEventListener("click", function () {
      currentIndex = 0;
      showModal();
    });

    if (backdrop) backdrop.addEventListener("click", hideModal);
    if (closeBtn) closeBtn.addEventListener("click", hideModal);
    if (prevBtn) prevBtn.addEventListener("click", function () { navigate(-1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { navigate(1); });

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

    document.addEventListener("keydown", function (e) {
      if (!modal.classList.contains("open")) return;
      if (e.key === "Escape") hideModal();
      else if (e.key === "ArrowLeft") navigate(-1);
      else if (e.key === "ArrowRight") navigate(1);
    });

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

  return { init: init };
})();
