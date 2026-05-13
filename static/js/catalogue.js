/* A.N.A.N.A.S. — Catalogue */
var CatalogueModule = (function () {
  function init() {
    document.querySelectorAll(".catalogue-item").forEach(function (item) {
      const full = item.querySelector(".catalogue-desc-full");
      const preview = item.querySelector(".catalogue-desc-preview");
      const btn = item.querySelector(".btn-expand");
      if (!full || !preview || !btn) return;

      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        const expanded = btn.getAttribute("aria-expanded") === "true";

        btn.setAttribute("aria-expanded", String(!expanded));
        btn.textContent = expanded ? "Moins" : "Plus";

        preview.hidden = !expanded;
        full.hidden = expanded;
      });
    });
  }

  return { init: init };
})();
