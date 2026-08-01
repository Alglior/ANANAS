/* A.N.A.N.A.S — Catalogue */
var CatalogueModule = (function () {
  function init() {
    initExpandButtons();
    initCategoryFilter();
  }

  function initExpandButtons() {
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

  function initCategoryFilter() {
    const container = document.querySelector(".filter-category-dropdown");
    if (!container) return;

    const btn = container.querySelector(".filter-category-btn");
    const menu = container.querySelector(".filter-category-menu");
    const search = container.querySelector(".filter-category-search");
    const list = container.querySelector(".filter-category-list");
    const options = list ? list.querySelectorAll(".filter-category-option") : [];

    if (!btn || !menu || !list) return;

    /* Toggle dropdown */
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!expanded));
      menu.hidden = expanded;
      if (!expanded && search) {
        search.value = "";
        search.focus();
        filterOptions(search, options);
      }
    });

    /* Search filter */
    if (search) {
      search.addEventListener("input", function () {
        filterOptions(this, options);
      });

      search.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          closeDropdown(btn, menu);
        }
        if (e.key === "Enter") {
          const visible = list.querySelector(
            ".filter-category-option:not(.hidden)"
          );
          if (visible) {
            selectOption(visible, container);
          }
        }
      });
    }

    /* Option clicks */
    options.forEach(function (opt) {
      opt.addEventListener("click", function (e) {
        e.stopPropagation();
        selectOption(this, container);
      });
    });

    /* Close on outside click */
    document.addEventListener("click", function (e) {
      if (!container.contains(e.target)) {
        closeDropdown(btn, menu);
      }
    });

    /* Close on Escape */
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && btn.getAttribute("aria-expanded") === "true") {
        closeDropdown(btn, menu);
      }
    });
  }

  function filterOptions(input, options) {
    var q = input.value.toLowerCase();
    options.forEach(function (opt) {
      var text = opt.textContent.toLowerCase();
      opt.classList.toggle("hidden", text.indexOf(q) === -1);
    });
  }

  function selectOption(opt, container) {
    var value = opt.getAttribute("data-value");
    var url = new URL(window.location.href);
    if (value) {
      url.searchParams.set("category", value);
    } else {
      url.searchParams.delete("category");
    }
    url.searchParams.delete("page");
    window.location.href = url.toString();
  }

  function closeDropdown(btn, menu) {
    btn.setAttribute("aria-expanded", "false");
    menu.hidden = true;
  }

  return { init: init };
})();
