/**
 * A.N.A.N.A.S. — Star rating hover + auto-submit (detail page)
 */
var StarRatingModule = (function () {
  function init() {
    var rateForms = document.querySelectorAll(".rate-form");
    rateForms.forEach(function (form) {
      var labels = Array.from(form.querySelectorAll("label"));
      var inputs = Array.from(form.querySelectorAll("input"));
      if (!labels.length) return;

      labels.forEach(function (label, idx) {
        label.addEventListener("mouseenter", function () {
          labels.forEach(function (s, i) {
            s.style.color = i <= idx ? "#daa520" : "#d5d5d5";
          });
        });

        label.addEventListener("mouseleave", function () {
          var checkedIdx = inputs.findIndex(function (inp) { return inp.checked; });
          labels.forEach(function (s, i) {
            s.style.color = "";
          });
        });

        label.addEventListener("click", function () {
          inputs[idx].checked = true;
          form.submit();
        });
      });
    });
  }

  return { init: init };
})();
