/**
 * A.N.A.N.A.S. — Upload : data textarea (CSV line count, paste guard)
 */
UploadModule.dataInput = (function () {
  var MAX_LINES = 50;

  function init() {
    var dataInput = document.getElementById('data_input');
    var dataLineCount = document.getElementById('dataLineCount');
    if (!dataInput) return;

    function updateLineCount() {
      var lines = dataInput.value.split('\n').filter(function(line) { return line.trim(); });
      var count = Math.min(lines.length, MAX_LINES);
      dataLineCount.textContent = count + ' ligne(s) / ' + MAX_LINES + ' max';
      if (lines.length > MAX_LINES) {
        dataLineCount.classList.add('color-error');
      } else {
        dataLineCount.classList.remove('color-error');
      }
    }

    dataInput.addEventListener('input', updateLineCount);
    dataInput.addEventListener('change', updateLineCount);
    updateLineCount();

    dataInput.addEventListener('paste', function(e) {
      setTimeout(function() {
        var lines = dataInput.value.split('\n').filter(function(line) { return line.trim(); });
        if (lines.length > MAX_LINES) {
          e.preventDefault();
          alert('Attention : vous avez collé ' + lines.length + ' lignes. Seules les ' + MAX_LINES + ' premières seront conservées.');
          dataInput.value = lines.slice(0, MAX_LINES).join('\n');
          updateLineCount();
        }
      }, 10);
    });
  }

  return { init: init };
})();