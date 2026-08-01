(function () {
  initSidebarTabs();
  initInnerTabs();
  initToggleSwitches();
  initSettingModal();
  initLogoUpload();

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

  /* ── Inline Edit Modal ── */
  function initSettingModal() {
    var modal = document.getElementById("settingModal");
    var form = document.getElementById("settingForm");
    var keyInput = document.getElementById("settingKey");
    var textInput = document.getElementById("settingInput");
    var textareaInput = document.getElementById("settingTextarea");
    var selectInput = document.getElementById("settingSelect");
    var feedback = document.getElementById("settingFeedback");
    var modalTitle = document.getElementById("settingModalTitle");
    var modalLabel = document.getElementById("settingLabel");

    if (!modal || !form) return;

    function openModal(key, label, type, value) {
      keyInput.value = key;
      modalTitle.textContent = "Modifier : " + label;
      modalLabel.textContent = label;

      textInput.hidden = true;
      textareaInput.hidden = true;
      selectInput.hidden = true;

      if (type === "boolean") {
        selectInput.hidden = false;
        selectInput.value = value;
      } else if (value && value.length > 80) {
        textareaInput.hidden = false;
        textareaInput.value = value;
      } else {
        textInput.hidden = false;
        textInput.value = value;
        textInput.type = type === "number" ? "number" : "text";
      }

      feedback.hidden = true;
      modal.hidden = false;
    }

    function getEditedValue() {
      if (!textInput.hidden) return textInput.value.trim();
      if (!textareaInput.hidden) return textareaInput.value.trim();
      return selectInput.value;
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
      var value = getEditedValue();

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
  function getCsrf() {
    return typeof CsrfModule !== "undefined" ? CsrfModule.getCsrfToken() : "";
  }

  function updateSetting(key, value, onSuccess, onError) {
    var payload = {};
    payload[key] = value;

    fetch("/api/admin/settings/update", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": getCsrf() },
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

  /* ── Logo drag & drop upload ── */
  function initLogoUpload() {
    var dropzone = document.getElementById("logo-dropzone");
    var fileInput = document.getElementById("logo-file-input");
    var preview = document.getElementById("logo-preview");
    var feedback = document.getElementById("logo-upload-feedback");

    if (!dropzone || !fileInput) return;

    function showFeedback(msg, isError) {
      if (!feedback) return;
      feedback.textContent = msg;
      feedback.className = "form-feedback " + (isError ? "form-feedback-error" : "form-feedback-success");
      feedback.hidden = false;
      setTimeout(function () { feedback.hidden = true; }, 4000);
    }

    function uploadFile(file) {
      if (!file) return;
      var allowed = ["image/png", "image/jpeg", "image/webp", "image/svg+xml", "image/x-icon"];
      if (allowed.indexOf(file.type) === -1) {
        showFeedback("Format non support\u00e9 (png, jpg, webp, svg, ico)", true);
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        showFeedback("Fichier trop volumineux (max 5 Mo)", true);
        return;
      }

      var formData = new FormData();
      formData.append("logo", file);

      dropzone.classList.add("uploading");

      fetch("/api/admin/settings/logo-upload", {
        method: "POST",
        headers: { "X-CSRF-Token": getCsrf() },
        body: formData,
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          dropzone.classList.remove("uploading");
          if (data.error) {
            showFeedback(data.error, true);
            return;
          }
          if (data.logo_path) {
            preview.src = data.logo_path + "?t=" + Date.now();
            var pathDisplay = document.getElementById("logo-path-display");
            if (pathDisplay) pathDisplay.textContent = data.logo_path;
            var row = document.querySelector('.setting-row[data-key="site_logo"]');
            if (row) {
              var valSpan = row.querySelector(".inline-edit-value");
              if (valSpan) valSpan.textContent = data.logo_path;
              var btn = row.querySelector(".inline-edit-btn");
              if (btn) btn.dataset.value = data.logo_path;
            }
          }
          showFeedback("Logo mis \u00e0 jour avec succ\u00e8s.", false);
        })
        .catch(function () {
          dropzone.classList.remove("uploading");
          showFeedback("Erreur lors de l'upload du logo.", true);
        });
    }

    /* Click to browse */
    dropzone.addEventListener("click", function () { fileInput.click(); });
    fileInput.addEventListener("change", function () {
      if (this.files && this.files[0]) uploadFile(this.files[0]);
    });

    /* Drag & drop */
    dropzone.addEventListener("dragover", function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("drag-over");
    });
    dropzone.addEventListener("dragleave", function () {
      dropzone.classList.remove("drag-over");
    });
    dropzone.addEventListener("drop", function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("drag-over");
      var files = e.dataTransfer.files;
      if (files && files[0]) uploadFile(files[0]);
    });
  }
})();