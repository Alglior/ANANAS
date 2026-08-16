/**
 * A.N.A.N.A.S — Admin backup : download & restore
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var downloadBtn = document.getElementById("backup-download-btn");
    var restoreForm = document.getElementById("backup-restore-form");
    var restoreBtn = document.getElementById("backup-restore-btn");
    var fileInput = document.getElementById("backup-file");
    var fileNameSpan = document.getElementById("backup-file-name");
    var fileBrowseBtn = document.querySelector(".btn-file-browse");
    var errorDiv = document.getElementById("backup-restore-error");
    var successDiv = document.getElementById("backup-restore-success");

    function getCSRFToken() {
      var meta = document.querySelector('meta[name="csrf-token"]');
      return meta ? meta.getAttribute("content") : "";
    }

    function showError(msg) {
      errorDiv.textContent = msg;
      errorDiv.classList.remove("hidden-section");
      successDiv.classList.add("hidden-section");
    }

    function showSuccess(msg) {
      successDiv.textContent = msg;
      successDiv.classList.remove("hidden-section");
      errorDiv.classList.add("hidden-section");
    }

    function setLoading(btn, loading) {
      var label = btn.querySelector(".btn-label");
      var spinner = btn.querySelector(".btn-spinner");
      if (loading) {
        label.classList.add("hidden-section");
        spinner.classList.remove("hidden-section");
        btn.disabled = true;
      } else {
        label.classList.remove("hidden-section");
        spinner.classList.add("hidden-section");
        btn.disabled = false;
      }
    }

    // ── Custom file input ──
    if (fileBrowseBtn) {
      fileBrowseBtn.addEventListener("click", function () {
        fileInput.click();
      });
    }

    fileInput.addEventListener("change", function () {
      if (fileInput.files && fileInput.files[0]) {
        fileNameSpan.textContent = fileInput.files[0].name;
      } else {
        fileNameSpan.textContent = "Aucun fichier choisi";
      }
    });

    // ── Download backup ──
    downloadBtn.addEventListener("click", function () {
      setLoading(downloadBtn, true);
      showError("");
      showSuccess("");

      var xhr = new XMLHttpRequest();
      xhr.open("GET", "/api/admin/backup/download", true);
      xhr.responseType = "blob";
      xhr.setRequestHeader("X-CSRF-Token", getCSRFToken());

      xhr.onload = function () {
        setLoading(downloadBtn, false);
        if (xhr.status !== 200) {
          showError("Erreur lors de la génération de la sauvegarde.");
          return;
        }
        var disposition = xhr.getResponseHeader("Content-Disposition") || "";
        var match = disposition.match(/filename=([^;]+)/);
        var filename = match ? match[1].trim() : "ananas_backup.sql.gz";
        var blob = xhr.response;
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showSuccess("Sauvegarde téléchargée avec succès.");
      };

      xhr.onerror = function () {
        setLoading(downloadBtn, false);
        showError("Erreur réseau lors du téléchargement.");
      };

      xhr.send();
    });

    // ── Restore backup ──
    restoreForm.addEventListener("submit", function (e) {
      e.preventDefault();
      showError("");
      showSuccess("");

      var file = fileInput.files[0];
      if (!file) {
        showError("Veuillez sélectionner un fichier .sql.gz.");
        return;
      }
      if (!file.name.endsWith(".sql.gz")) {
        showError("Le fichier doit être au format .sql.gz.");
        return;
      }

      if (!confirm(
        "⚠️ Cette action va REMPLACER toutes les données actuelles par celles du fichier importé.\n\n" +
        "Cette opération est irréversible. Continuer ?"
      )) {
        return;
      }

      setLoading(restoreBtn, true);

      var formData = new FormData();
      formData.append("file", file);

      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/admin/backup/restore", true);
      xhr.setRequestHeader("X-CSRF-Token", getCSRFToken());

      xhr.onload = function () {
        setLoading(restoreBtn, false);
        var resp;
        try {
          resp = JSON.parse(xhr.responseText);
        } catch (_) {
          showError("Réponse invalide du serveur.");
          return;
        }

        if (xhr.status === 200) {
          showSuccess(resp.message || "Restauration terminée.");
        } else {
          var msg = resp.error || "Erreur lors de la restauration.";
          if (resp.errors && resp.errors.length) {
            msg += " " + resp.errors.map(function (e) {
              return e.error || e;
            }).join(" ");
          }
          showError(msg);
        }
      };

      xhr.onerror = function () {
        setLoading(restoreBtn, false);
        showError("Erreur réseau lors de la restauration.");
      };

      xhr.send(formData);
    });
  });
})();