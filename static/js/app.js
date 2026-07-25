/**
 * A.N.A.N.A.S. — Application entry point
 * Orchestre tous les modules dans l'ordre déterministe.
 */
document.addEventListener("DOMContentLoaded", function () {
  MainModule.initSearch();
  MainModule.initCopyBtn();
  MainModule.validatePasswordMatch();
  MainModule.initDropdown();
  MainModule.initUserDropdown();
  if (typeof CatalogueModule !== "undefined") CatalogueModule.init();
  if (typeof InlineGalleryModule !== "undefined") InlineGalleryModule.init();
  if (typeof ImageModalModule !== "undefined") ImageModalModule.init();
  if (typeof CopyMagnetModule !== "undefined") CopyMagnetModule.init();
  if (typeof StarRatingModule !== "undefined") StarRatingModule.init();
  if (typeof ReportModalModule !== "undefined") ReportModalModule.init();
});
