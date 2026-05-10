/* A.N.A.N.A.S. — Catalogue */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".catalogue-item").forEach(function (item) {
    var full = item.querySelector(".catalogue-desc-full");
    var preview = item.querySelector(".catalogue-desc-preview");
    var btn = item.querySelector(".btn-expand");
    if (!full || !preview || !btn) return;

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      var expanded = btn.getAttribute("aria-expanded") === "true";

      btn.setAttribute("aria-expanded", String(!expanded));
      btn.textContent = expanded ? "Plus" : "Moins";

      preview.hidden = !expanded;
      full.hidden = expanded;
    });
  });
});
