/**
 * A.N.A.N.A.S. — Report modal (detail page)
 */
var ReportModalModule = (function () {
  function submitReport(e, modal) {
    e.preventDefault();
    var form = document.getElementById("reportForm");
    var data = {};
    var entries = new FormData(form).entries();
    for (var pair of entries) {
      data[pair[0]] = pair[1];
    }
    data.target_type = modal.getAttribute("data-target-type") || "geodonnee";
    data.target_id = parseInt(modal.getAttribute("data-target-id"), 10);

    fetch("/api/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }).then(function (r) { return r.json(); }).then(function (res) {
      modal.classList.remove("show");
    });
  }

  function closeModal(modal) {
    modal.classList.remove("show");
  }

  function openModal(modal) {
    modal.classList.add("show");
  }

  function init() {
    var openBtn = document.getElementById("open-report-modal");
    var modal = document.getElementById("reportModal");
    var reportForm = document.getElementById("reportForm");

    if (!openBtn || !modal) return;

    if (reportForm) {
      reportForm.addEventListener("submit", function (e) {
        submitReport(e, modal);
      });
    }

    openBtn.addEventListener("click", function () {
      openModal(modal);
    });

    var cancelBtns = modal.querySelectorAll("[type='button']");
    for (var i = 0; i < cancelBtns.length; i++) {
      cancelBtns[i].addEventListener("click", function () {
        closeModal(modal);
      });
    }

    document.addEventListener("click", function (e) {
      var isOpen = modal.classList.contains("show");
      if (!isOpen) return;
      if (!e.target.closest(".modal-box")) {
        closeModal(modal);
      }
    });

    document.addEventListener("keydown", function (e) {
      var isOpen = modal.classList.contains("show");
      if (!isOpen) return;
      if (e.key === "Escape") {
        closeModal(modal);
      }
    });
  }

  return { init: init };
})();
