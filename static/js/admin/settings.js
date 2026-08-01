/* A.N.A.N.A.S — Admin Settings */
(function () {
  initSubTabs();
  initSettingModal();

  function initSubTabs() {
    document.querySelectorAll(".admin-sub-nav").forEach(function (nav) {
      nav.querySelectorAll(".admin-sub-tab").forEach(function (tab) {
        tab.addEventListener("click", function () {
          var tabId = this.getAttribute("data-tab");
          var parent = this.closest(".admin-settings-tabs, .admin-home-tabs");

          parent.querySelectorAll(".admin-sub-tab").forEach(function (t) {
            t.classList.remove("active");
          });
          parent.querySelectorAll(".admin-sub-tab-content").forEach(function (
            c
          ) {
            c.classList.remove("active");
          });

          this.classList.add("active");
          var target = parent.querySelector("#tab-" + tabId);
          if (target) target.classList.add("active");
        });
      });
    });
  }

  function initSettingModal() {
    const modal = document.getElementById("settingModal");
    const form = document.getElementById("settingForm");
    const keyInput = document.getElementById("settingKey");
    const textInput = document.getElementById("settingInput");
    const selectInput = document.getElementById("settingSelect");
    const feedback = document.getElementById("settingFeedback");
    const modalTitle = document.getElementById("settingModalTitle");
    const modalLabel = document.getElementById("settingLabel");

    if (!modal || !form) return;

  function openModal(key, label, type, value) {
    keyInput.value = key;
    modalTitle.textContent = "Modifier : " + label;
    modalLabel.textContent = label;

    if (type === "boolean") {
      textInput.hidden = true;
      selectInput.hidden = false;
      selectInput.value = value;
    } else {
      selectInput.hidden = true;
      textInput.hidden = false;
      textInput.value = value;
      textInput.type = type === "number" ? "number" : "text";
    }

    feedback.hidden = true;
    modal.hidden = false;
  }

  function closeModal() {
    modal.hidden = true;
    feedback.hidden = true;
  }

  document.querySelectorAll(".edit-setting-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      openModal(
        this.dataset.key,
        this.dataset.label,
        this.dataset.type,
        this.dataset.value
      );
    });
  });

  document.querySelectorAll(".modal-cancel").forEach(function (btn) {
    btn.addEventListener("click", closeModal);
  });

  modal.addEventListener("click", function (e) {
    if (e.target === modal) closeModal();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) closeModal();
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var key = keyInput.value;
    var value = selectInput.hidden
      ? textInput.value.trim()
      : selectInput.value;

    var payload = {};
    payload[key] = value;

    fetch("/api/admin/settings/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) {
        if (!r.ok) throw new Error("Erreur serveur");
        return r.json();
      })
      .then(function (data) {
        if (data.status === "updated") {
          feedback.textContent = "Paramètre mis à jour avec succès.";
          feedback.className = "form-feedback form-feedback-success";
          feedback.hidden = false;

          /* Update the table row */
          var row = document.querySelector('tr[data-key="' + key + '"]');
          if (row) {
            var cell = row.querySelector(".setting-value-cell");
            var badge = cell.querySelector(".setting-badge");
            var valSpan = cell.querySelector(".setting-value");
            if (badge) {
              badge.textContent = value === "true" ? "Activé" : "Désactivé";
              badge.className =
                "badge " +
                (value === "true" ? "badge-success" : "badge-danger") +
                " setting-badge";
            }
            if (valSpan) valSpan.textContent = value;
            var btn = row.querySelector(".edit-setting-btn");
            if (btn) btn.dataset.value = value;
          }

          setTimeout(closeModal, 1200);
        }
      })
      .catch(function (err) {
        feedback.textContent = "Erreur : " + err.message;
        feedback.className = "form-feedback form-feedback-error";
        feedback.hidden = false;
      });
  });
  }
})();