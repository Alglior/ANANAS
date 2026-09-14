/**
 * A.N.A.N.A.S — Recherche avancée par étiquettes
 * Gère le toggle inclure/exclure/ignorer pour chaque tag et la soumission du formulaire.
 */
var AdvancedSearchModule = (function () {

  function init() {
    var form = document.querySelector(".advanced-search-form");
    if (!form) return;

    form.addEventListener("submit", function (e) {
      var rows = form.querySelectorAll(".advanced-search-tag-row");
      for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        var modeInput = row.querySelector(".tag-mode-input");
        var mode = modeInput.value;
        if (mode === "include") {
          var inp = document.createElement("input");
          inp.type = "hidden";
          inp.name = "tag";
          inp.value = row.getAttribute("data-tag");
          form.appendChild(inp);
        } else if (mode === "exclude") {
          var inp = document.createElement("input");
          inp.type = "hidden";
          inp.name = "exclude_tag";
          inp.value = row.getAttribute("data-tag");
          form.appendChild(inp);
        }
      }
    });

    var btns = form.querySelectorAll(".advanced-search-tag-btn");
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener("click", function () {
        var row = this.closest(".advanced-search-tag-row");
        var modeInput = row.querySelector(".tag-mode-input");
        var action = this.getAttribute("data-action");
        var currentMode = modeInput.value;

        if (currentMode === action) {
          modeInput.value = "ignore";
          row.classList.remove("mode-include", "mode-exclude");
        } else {
          modeInput.value = action;
          row.classList.remove("mode-include", "mode-exclude");
          row.classList.add("mode-" + action);
        }
      });
    }

    var clearBtns = form.querySelectorAll(".btn-advanced-search-clear");
    for (var i = 0; i < clearBtns.length; i++) {
      clearBtns[i].addEventListener("click", function () {
        var rows = form.querySelectorAll(".advanced-search-tag-row");
        for (var j = 0; j < rows.length; j++) {
          var modeInput = rows[j].querySelector(".tag-mode-input");
          modeInput.value = "ignore";
          rows[j].classList.remove("mode-include", "mode-exclude");
        }
      });
    }
  }

  return {
    init: init
  };
})();