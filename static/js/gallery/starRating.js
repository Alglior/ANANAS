/**
 * A.N.A.N.A.S — Star rating hover + auto-submit (detail page)
 */
var StarRatingModule = (function () {
  var initialized = false;

  function init() {
    if (initialized) return;
    initialized = true;

    var rateForms = document.querySelectorAll(".rate-form");
    rateForms.forEach(function (form) {
      var labels = Array.from(form.querySelectorAll("label"));
      var inputs = Array.from(form.querySelectorAll("input[type='radio']"));
      if (!labels.length) return;

      labels.forEach(function (label, idx) {
        var hoverIdx = idx + 1;
        label.setAttribute("data-hover", hoverIdx);
        label.addEventListener("mouseenter", function () {
          labels.forEach(function (s, i) {
            if (i < hoverIdx) s.classList.add("star-hovered");
            else s.classList.remove("star-hovered");
          });
        });

        label.addEventListener("mouseleave", function () {
          labels.forEach(function (s) {
            s.classList.remove("star-hovered");
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
