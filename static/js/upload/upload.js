/**
 * A.N.A.N.A.S — Upload : shared namespace + state
 */
var UploadModule = window.UploadModule || {};

(function () {
  var scriptEl = document.getElementById('edit-data-json');
  var editData = null;
  if (scriptEl) {
    try {
      editData = JSON.parse(scriptEl.textContent);
    } catch (e) {
      editData = null;
    }
  }

  UploadModule.getEditData = function () { return editData; };
  UploadModule.EDITING = !!editData;
  UploadModule.EDIT_ITEM_ID = UploadModule.EDITING ? editData.id : null;
})();