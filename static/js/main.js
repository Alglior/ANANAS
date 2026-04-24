/**
 * A.N.A.N.A.S. — Script principal
 * Gérer la recherche, la copie d'email et les validations communes aux formulaires.
 */

document.addEventListener("DOMContentLoaded", () => {
  initSearch();
  initCopyBtn();
  validatePasswordMatch();
});

/* -------------------------------------------------------------------------- */
/* Search                                                                   */
/* -------------------------------------------------------------------------- */

function initSearch() {
  const form = document.querySelector(".search-bar");
  const input = document.getElementById("site-search");

  if (!form || !input) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const term = input.value.trim();
    if (term) {
      alert("Recherche lancée pour : " + term);
    }
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
      feedback.style.opacity = "1";

      setTimeout(() => {
        btn.classList.remove("copied");
        btn.textContent = "Copier l'email";
        feedback.style.opacity = "0";
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
