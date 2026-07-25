/**
 * A.N.A.N.A.S. — Upload : shared namespace + state
 */
var UploadModule = window.UploadModule || {};
UploadModule.EDITING = !!window.EDIT_DATA;
UploadModule.EDIT_ITEM_ID = UploadModule.EDITING ? window.EDIT_DATA.id : null;