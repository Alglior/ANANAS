/* A.N.A.N.A.S — Catalogue */
var CatalogueModule = (function () {
  var openDropdowns = [];

  function registerDropdown(container) {
    var btn = container.querySelector("button[aria-haspopup]");
    var menu = container.querySelector("[hidden]");
    if (!btn || !menu) return null;
    var handle = { btn: btn, menu: menu, container: container };
    openDropdowns.push(handle);
    return handle;
  }

  function closeDropdown(handle) {
    if (!handle) return;
    handle.btn.setAttribute("aria-expanded", "false");
    handle.menu.hidden = true;
  }

  function closeOtherDropdowns(handle) {
    openDropdowns.forEach(function (d) {
      if (d !== handle) closeDropdown(d);
    });
  }

  function isOpen(handle) {
    return handle.btn.getAttribute("aria-expanded") === "true";
  }

  function toggleDropdown(handle) {
    if (isOpen(handle)) {
      closeDropdown(handle);
    } else {
      closeOtherDropdowns(handle);
      handle.btn.setAttribute("aria-expanded", "true");
      handle.menu.hidden = false;
    }
  }

  function init() {
    initExpandButtons();
    initCategoryFilter();
    initYearFilter();
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
        btn.textContent = expanded ? "Plus" : "Moins";

        preview.hidden = !expanded;
        full.hidden = expanded;
      });
    });
  }

  function initCategoryFilter() {
    const container = document.querySelector(".filter-category-dropdown");
    if (!container) return;

    const handle = registerDropdown(container);
    if (!handle) return;

    const btn = handle.btn;
    const menu = handle.menu;
    const search = container.querySelector(".filter-category-search");
    const list = container.querySelector(".filter-category-list");
    const options = list ? list.querySelectorAll(".filter-category-option") : [];

    /* Toggle dropdown */
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const wasOpen = isOpen(handle);
      toggleDropdown(handle);
      if (!wasOpen && search) {
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
          closeDropdown(handle);
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
        closeDropdown(handle);
      }
    });

    /* Close on Escape */
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && isOpen(handle)) {
        closeDropdown(handle);
      }
    });
  }

  function initYearFilter() {
    const container = document.querySelector(".filter-year-dropdown");
    if (!container) return;

    const handle = registerDropdown(container);
    if (!handle) return;

    const btn = handle.btn;
    const input = container.querySelector(".filter-year-input");
    const applyBtn = container.querySelector(".filter-year-apply");
    const clearLink = container.querySelector(".filter-year-clear");

    /* Toggle dropdown */
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      toggleDropdown(handle);
      if (isOpen(handle) && input) input.focus();
    });

    function applyYear() {
      if (!input) return;
      var value = input.value.trim();
      var url = new URL(window.location.href);
      if (value) {
        url.searchParams.set("year", value);
      } else {
        url.searchParams.delete("year");
      }
      url.searchParams.delete("page");
      window.location.href = url.toString();
    }

    if (applyBtn) {
      applyBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        applyYear();
      });
    }

    if (input) {
      input.addEventListener("keydown", function (e) {
        e.stopPropagation();
        if (e.key === "Enter") applyYear();
      });
    }

    /* Close on outside click */
    document.addEventListener("click", function (e) {
      if (!container.contains(e.target)) {
        closeDropdown(handle);
      }
    });

    /* Close on Escape */
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && isOpen(handle)) {
        closeDropdown(handle);
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

  return { init: init };
})();