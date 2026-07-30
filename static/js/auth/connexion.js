(function () {
  var pseudoEl = document.getElementById('newPseudo');
  var copyBtn = document.getElementById('copyPseudoBtn');
  if (!pseudoEl || !copyBtn) return;

  copyBtn.addEventListener('click', function () {
    var text = pseudoEl.textContent.trim();
    if (!text) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        var original = copyBtn.textContent;
        copyBtn.textContent = 'Copie !';
        setTimeout(function () { copyBtn.textContent = original; }, 2000);
      });
    }
  });
})();