/**
 * A.N.A.N.A.S. — Star rating hover + auto-submit (detail page)
 */
var StarRatingModule = (function () {
  function init() {
    var rateForms = document.querySelectorAll(".rate-form");
    rateForms.forEach(function (form) {
      var labels = Array.from(form.querySelectorAll("label"));
      var inputs = Array.from(form.querySelectorAll("input[type='radio']"));
      if (!labels.length) return;

      labels.forEach(function (label, idx) {
        label.addEventListener("mouseenter", function () {
          var hoverIdx = idx + 1;
          labels.forEach(function (s, i) {
            s.style.color = i < hoverIdx ? "#daa520" : "";
          });
        });

        label.addEventListener("mouseleave", function () {
          labels.forEach(function (s) {
            s.style.color = "";
          });
        });

        label.addEventListener("click", function () {
          console.log("[STAR] Clicked idx=" + idx + " value=" + inputs[idx].value);
          console.log("[STAR] All inputs:", Array.from(inputs).map(function (inp) { return inp.value; }).join(", "));
          inputs[idx].checked = true;
          console.log("[STAR] After check, checked:", Array.from(inputs).map(function (inp) { return inp.value + "=" + inp.checked; }).join(", "));
          form.submit();
        });
      });
    });
  }

  return { init: init };
})();
