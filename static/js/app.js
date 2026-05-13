/**
 * A.N.A.N.A.S. — Application entry point
 * Orchestre tous les modules dans l'ordre déterministe.
 */
document.addEventListener("DOMContentLoaded", function () {
  MainModule.initSearch();
  MainModule.initCopyBtn();
  MainModule.validatePasswordMatch();
  CatalogueModule.init();
  InlineGalleryModule.init();
  ImageModalModule.init();
  CopyMagnetModule.init();
  StarRatingModule.init();
});
