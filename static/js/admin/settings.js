(function () {
  initSidebarTabs();
  initInnerTabs();
  initToggleSwitches();
  initSettingModal();

  /* ── Sidebar tab switching ── */
  function initSidebarTabs() {
    var tabs = document.querySelectorAll(".settings-sidebar-tab");
    var panels = document.querySelectorAll(".settings-tab-panel");

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var tabId = this.getAttribute("data-settings-tab");

        tabs.forEach(function (t) { t.classList.remove("active"); });
        panels.forEach(function (p) { p.classList.remove("active"); });

        this.classList.add("active");
        var target = document.getElementById("settings-tab-" + tabId);
        if (target) target.classList.add("active");
      });
    });
  }

  /* ── Inner tabs (Accueil sub-tabs) ── */
  function initInnerTabs() {
    document.querySelectorAll(".settings-inner-nav").forEach(function (nav) {
      nav.querySelectorAll(".settings-inner-tab").forEach(function (tab) {
        tab.addEventListener("click", function () {
          var tabId = this.getAttribute("data-inner-tab");
          var parent = this.closest(".settings-inner-tabs");

          parent.querySelectorAll(".settings-inner-tab").forEach(function (t) {
            t.classList.remove("active");
          });
          parent.querySelectorAll(".settings-inner-panel").forEach(function (p) {
            p.classList.remove("active");
          });

          this.classList.add("active");
          var target = parent.querySelector("#settings-inner-" + tabId);
          if (target) target.classList.add("active");
        });
      });
    });
  }

  /* ── Toggle Switches ── */
  function initToggleSwitches() {
    document.querySelectorAll(".toggle-input").forEach(function (input) {
      input.addEventListener("change", function () {
        var key = this.getAttribute("data-key");
        var value = this.checked ? "true" : "false";
        var label = document.getElementById("toggle-label-" + key);

        updateSetting(key, value, function () {
          if (label) {
            label.textContent = this.checked ? "Activ\u00e9" : "D\u00e9sactiv\u00e9";
            label.className = "toggle-label " + (this.checked ? "toggle-on" : "toggle-off");
          }
        }.bind(this));
      });
    });
  }

  /* ── Inline Edit Modal ── (same logic as before, adapted) */
  function initSettingModal() {
    var modal = document.getElementById("settingModal");
    var form = document.getElementById("settingForm");
    var keyInput = document.getElementById("settingKey");
    var textInput = document.getElementById("settingInput");
    var selectInput = document.getElementById("settingSelect");
    var feedback = document.getElementById("settingFeedback");
    var modalTitle = document.getElementById("settingModalTitle");
    var modalLabel = document.getElementById("settingLabel");

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

    /* Bind inline edit buttons and container */
    document.querySelectorAll(".inline-edit-btn").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        openModal(
          this.dataset.key,
          this.dataset.label,
          this.dataset.type,
          this.dataset.value
        );
      });
    });

    document.querySelectorAll(".inline-edit").forEach(function (container) {
      container.addEventListener("click", function () {
        var btn = this.querySelector(".inline-edit-btn");
        if (btn) {
          openModal(
            btn.dataset.key,
            btn.dataset.label,
            btn.dataset.type,
            btn.dataset.value
          );
        }
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

      updateSetting(key, value, function () {
        var row = document.querySelector('.setting-row[data-key="' + key + '"]');
        if (row) {
          var valSpan = row.querySelector(".inline-edit-value");
          if (valSpan) valSpan.textContent = value;
          var btn = row.querySelector(".inline-edit-btn");
          if (btn) btn.dataset.value = value;

          /* Also handle toggle if present */
          var toggle = row.querySelector(".toggle-input");
          if (toggle) {
            toggle.checked = value === "true";
            var label = document.getElementById("toggle-label-" + key);
            if (label) {
              label.textContent = value === "true" ? "Activ\u00e9" : "D\u00e9sactiv\u00e9";
              label.className = "toggle-label " + (value === "true" ? "toggle-on" : "toggle-off");
            }
          }
        }

        feedback.textContent = "Param\u00e8tre mis \u00e0 jour avec succ\u00e8s.";
        feedback.className = "form-feedback form-feedback-success";
        feedback.hidden = false;
        setTimeout(closeModal, 1200);
      }, function () {
        feedback.textContent = "Erreur lors de la mise \u00e0 jour.";
        feedback.className = "form-feedback form-feedback-error";
        feedback.hidden = false;
      });
    });
  }

  /* ── Shared API call ── */
  function updateSetting(key, value, onSuccess, onError) {
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
          if (onSuccess) onSuccess(data);
        }
      })
      .catch(function (err) {
        if (onError) onError(err);
      });
  }
})();