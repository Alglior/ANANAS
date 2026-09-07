/**
 * A.N.A.N.A.S — Report modal (detail page)
 */
(function () {
  var modal = document.getElementById("reportModal");
  var openBtn = document.getElementById("open-report-modal");
  var reportForm = document.getElementById("reportForm");

  if (!openBtn || !modal || !reportForm) return;

  function showModal(e) {
    if (e) e.stopPropagation();
    modal.style.display = "block";
  }

  function hideModal() {
    modal.style.display = "none";
    reportForm.reset();
  }

  openBtn.addEventListener("click", showModal);

  reportForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var data = {};
    var entries = new FormData(reportForm).entries();
    for (var pair of entries) {
      data[pair[0]] = pair[1];
    }
    data.target_type = modal.getAttribute("data-target-type") || "geodonnee";
    data.target_id = parseInt(modal.getAttribute("data-target-id"), 10);

    var submitBtn = reportForm.querySelector("[type='submit']");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Envoi en cours...";
    }

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/reports", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("X-CSRF-Token", CsrfModule.getCsrfToken());
    xhr.onload = function () {
      try {
        var res = JSON.parse(xhr.responseText);
        if (res.status === "created") {
          hideModal();
        } else {
          alert(res.error || "Erreur lors de l'envoi du signalement");
        }
      } catch (e) {
        alert("Erreur serveur");
      }
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Envoyer le signalement";
      }
    };
    xhr.onerror = function () {
      alert("Erreur réseau. Veuillez réessayer.");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Envoyer le signalement";
      }
    };
    xhr.send(JSON.stringify(data));
  });

  var cancelBtns = modal.querySelectorAll("[type='button']");
  for (var i = 0; i < cancelBtns.length; i++) {
    cancelBtns[i].addEventListener("click", hideModal);
  }

  document.addEventListener("click", function (e) {
    if (modal.style.display !== "block") return;
    if (e.target.closest("#open-report-modal")) return;
    if (!e.target.closest(".modal-box")) {
      hideModal();
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.style.display === "block") {
      hideModal();
    }
  });
})();