/**
 * A.N.A.N.A.S — Script principal
 * Gérer la recherche, la copie d'email et les validations communes aux formulaires.
 */
var MainModule = (function () {

  /* -------------------------------------------------------------------------- */
  /* Toast notification (non-blocking feedback)                               */
  /* -------------------------------------------------------------------------- */

  function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast-notification";
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(function () {
      toast.classList.add("toast-show");
    });
    setTimeout(function () {
      toast.classList.remove("toast-show");
      setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, 2500);
  }

  /* -------------------------------------------------------------------------- */
  /* Search                                                                   */
  /* -------------------------------------------------------------------------- */

  function initSearch() {
    const form = document.querySelector(".search-bar");
    const input = document.getElementById("site-search");
    const select = form ? form.querySelector(".search-catalogue-select") : null;

    if (!form || !input) return;

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const term = input.value.trim();
      if (!term) return;
      const catalogue = select ? select.value : "donnees";
      window.location.href = "/catalogue/" + catalogue + "?q=" + encodeURIComponent(term);
    });
  }

  /* -------------------------------------------------------------------------- */
  /* Copy email                                                               */
  /* -------------------------------------------------------------------------- */

  function initCopyBtn() {
    const btn = document.getElementById("copy-btn");
    const feedback = document.getElementById("copy-feedback");
    const emailEl = document.getElementById("email-text");

    if (!btn || !emailEl) return;

    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(emailEl.textContent.trim());
        btn.classList.add("copied");
        btn.textContent = "✓ Copié";
        if (feedback) feedback.classList.add("copy-feedback-visible");

        setTimeout(() => {
          btn.classList.remove("copied");
          btn.textContent = "Copier l'email";
          if (feedback) feedback.classList.remove("copy-feedback-visible");
        }, 2000);
      } catch {
        btn.classList.add("error");
        setTimeout(() => btn.classList.remove("error"), 1500);
      }
    });
  }

  /* -------------------------------------------------------------------------- */
  /* Password match validation (inscription)                                  */
  /* -------------------------------------------------------------------------- */

  function validatePasswordMatch() {
    const pw = document.getElementById("password");
    const confirm = document.getElementById("password_confirm");

    if (!pw || !confirm) return;

    confirm.addEventListener("input", () => {
      const group = confirm.closest(".form-group");
      if (pw.value !== confirm.value) {
        group.classList.add("has-error");
        confirm.setCustomValidity("Les mots de passe ne correspondent pas.");
      } else {
        group.classList.remove("has-error");
        confirm.setCustomValidity("");
      }
    });
  }

  /* -------------------------------------------------------------------------- */
  /* Catalogue dropdown toggle                                                 */
  /* -------------------------------------------------------------------------- */

  function initDropdown() {
    const wrappers = document.querySelectorAll(".catalogue-dropdown-wrapper");
    
    wrappers.forEach(wrapper => {
      const toggle = wrapper.querySelector(".dropdown-toggle");
      const menu = wrapper.querySelector(".catalogue-dropdown");

      if (!toggle || !menu) return;

      function open() { menu.classList.add("open"); toggle.setAttribute("aria-expanded", "true"); }
      function close() { menu.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }

      toggle.addEventListener("click", (e) => {
        e.stopPropagation();
        menu.classList.contains("open") ? close() : open();
      });

      document.addEventListener("click", (e) => {
        if (!menu.contains(e.target) && !toggle.contains(e.target)) close();
      });

      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && menu.classList.contains("open")) close();
      });
    });
  }

  /* -------------------------------------------------------------------------- */
  /* User dropdown toggle                                                      */
  /* -------------------------------------------------------------------------- */

  function initUserDropdown() {
    const wrapper = document.getElementById("userDropdownWrapper");
    const toggle = wrapper ? wrapper.querySelector(".user-dropdown-toggle") : null;
    const menu = document.getElementById("userDropdown");

    if (!toggle || !menu) return;

    function open() {
      menu.classList.add("open");
      toggle.setAttribute("aria-expanded", "true");
      const arrow = toggle.querySelector(".dropdown-arrow");
      if (arrow) arrow.classList.add("rotated");
    }
    function close() {
      menu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      const arrow = toggle.querySelector(".dropdown-arrow");
      if (arrow) arrow.classList.remove("rotated");
    }

    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      menu.classList.contains("open") ? close() : open();
    });

    document.addEventListener("click", (e) => {
      if (!menu.contains(e.target) && !toggle.contains(e.target)) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menu.classList.contains("open")) close();
    });
  }

  /* -------------------------------------------------------------------------- */
  /* Public API                                                               */
  /* -------------------------------------------------------------------------- */

  return {
    initSearch: initSearch,
    initCopyBtn: initCopyBtn,
    validatePasswordMatch: validatePasswordMatch,
    initDropdown: initDropdown,
    initUserDropdown: initUserDropdown
  };
})();
