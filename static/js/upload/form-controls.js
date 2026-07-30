/**
 * A.N.A.N.A.S — Upload : form controls (type, format, license selectors)
 */
UploadModule.formControls = (function () {
  var formatDict = {
    geodonnee: [
      { value: 'geopackage', label: 'Geopackage (.gpkg)' },
      { value: 'csv', label: 'CSV' },
      { value: 'shp', label: 'Shapefile (.shp)' },
      { value: 'geojson', label: 'GeoJSON' },
      { value: 'kml', label: 'KML' },
      { value: 'gml', label: 'GML' },
      { value: 'gpx', label: 'GPX' },
      { value: 'topojson', label: 'TopoJSON' },
      { value: 'geoparquet', label: 'GeoParquet' },
      { value: 'tab', label: 'MapInfo TAB' },
      { value: 'xml', label: 'XML' }
    ],
    carte: [
      { value: 'png', label: 'PNG' },
      { value: 'jpg', label: 'JPG/JPEG' },
      { value: 'tiff', label: 'TIFF' },
      { value: 'gif', label: 'GIF' },
      { value: 'bmp', label: 'BMP' },
      { value: 'webp', label: 'WebP' }
    ],
    application: [
      { value: 'python', label: 'Python (.py)' },
      { value: 'rust', label: 'Rust (.rs)' },
      { value: 'javascript', label: 'JavaScript (.js)' },
      { value: 'typescript', label: 'TypeScript (.ts)' },
      { value: 'java', label: 'Java (.java)' },
      { value: 'go', label: 'Go (.go)' },
      { value: 'cpp', label: 'C++ (.cpp/.h)' },
      { value: 'html', label: 'HTML/CSS' }
    ]
  };

  function init() {
    var licenseTypeSelect = document.getElementById('license_type');
    var licenseOtherGroup = document.getElementById('licenseOtherGroup');
    var customLicenseText = document.getElementById('custom_license_text');

    if (licenseTypeSelect) {
      licenseTypeSelect.addEventListener('change', function() {
        if (licenseOtherGroup && customLicenseText) {
          if (this.value === 'other') {
            licenseOtherGroup.classList.remove('hidden-section');
            customLicenseText.required = true;
          } else {
            licenseOtherGroup.classList.add('hidden-section');
            customLicenseText.required = false;
            customLicenseText.value = '';
          }
        }
      });
    }

    var typeSelect = document.getElementById('type');
    var formatTypeSelect = document.getElementById('format_type');
    var dataTextInputGroup = document.getElementById('dataTextInputGroup');
    var magnetActions = document.querySelector('#magnetSection .magnet-actions');

    function populateFormats(type) {
      if (!formatTypeSelect || !formatDict[type]) return;
      formatTypeSelect.innerHTML = '';
      formatDict[type].forEach(function(opt) {
        var option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        formatTypeSelect.appendChild(option);
      });
    }

    function isNonData() {
      return typeSelect && (typeSelect.value === 'carte' || typeSelect.value === 'application');
    }

    if (typeSelect) {
      typeSelect.addEventListener('change', function() {
        populateFormats(this.value);
        if (dataTextInputGroup) {
          if (isNonData()) {
            dataTextInputGroup.classList.add('hidden-section');
          } else {
            dataTextInputGroup.classList.remove('hidden-section');
          }
        }
        if (magnetActions) {
          if (isNonData()) {
            magnetActions.classList.add('hidden-section');
          } else {
            magnetActions.classList.remove('hidden-section');
          }
        }
      });
    }

    if (typeSelect) {
      populateFormats(typeSelect.value);
    }
  }

  return { init: init };
})();