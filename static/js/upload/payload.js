/**
 * A.N.A.N.A.S — Upload : payload builder + safeFetchJson utility
 */
UploadModule.payload = (function () {
  function buildItemPayload(magnetLinks, isDraft) {
    var typeSelect = document.getElementById('type');
    var formatTypeSelect = document.getElementById('format_type');
    var customLicenseText = document.getElementById('custom_license_text');

    var payload = {
      title: document.getElementById('title').value.trim(),
      type: typeSelect.value,
      format_type: formatTypeSelect.value,
      description: document.getElementById('description').value.trim(),
      organization_id: document.getElementById('organization_id').value || '',
      license_type: document.getElementById('license_type').value || '',
      custom_license_text: customLicenseText ? customLicenseText.value || '' : '',
    };

    if (isDraft) {
      payload.status = 'draft';
    }

    if (!isDraft) {
      var dataFormatLevel = document.querySelector('input[name="data_format_level"]:checked');
      var level = dataFormatLevel ? dataFormatLevel.value : 'pack';

      if (level === 'simple' || level === 'pack') {
        payload.data_format_level = level;
        payload.magnet_link = magnetLinks.length > 0 ? magnetLinks[0].magnet_link : '';
        if (magnetLinks.length > 0) {
          if (level === 'pack' && magnetLinks[0].zoom_levels && magnetLinks[0].zoom_levels.length > 0) {
            payload.zoom_levels = magnetLinks[0].zoom_levels;
          } else if (level === 'simple') {
            payload.zoom_level = magnetLinks[0].zoom_level || 'regions';
          }
        }
      } else {
        payload.data_format_level = 'individual';
        payload.magnet_links = magnetLinks;
      }
    }

    var vizName = document.getElementById('viz_name');
    var vizUrl = document.getElementById('viz_url');
    if (vizName && vizUrl && vizName.value && vizUrl.value) {
      payload.viz_link_name = vizName.value.trim();
      payload.viz_link_url = vizUrl.value.trim();
    }

    var imageMagnets = UploadModule.imageMagnets.collectLinks();
    if (imageMagnets.length > 0) {
      payload.image_magnets = imageMagnets;
    }

    var tagsInput = document.getElementById('tags');
    if (tagsInput) {
      var tags = tagsInput.value.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t; });
      if (tags.length > 0) {
        payload.tags = tags;
      }
    }

    return payload;
  }

  async function safeFetchJson(url, options) {
    var resp = await fetch(url, options);
    var contentType = resp.headers.get('content-type') || '';
    if (resp.redirected) {
      throw new Error('SESSION_EXPIRED');
    }
    if (!contentType.includes('application/json')) {
      var text = await resp.text();
      console.error('R\u00e9ponse non-JSON de ' + url + ' (status ' + resp.status + '):', text.substring(0, 300));
      throw new Error('NON_JSON_RESPONSE');
    }
    var data = await resp.json();
    return { response: resp, data: data };
  }

  return { buildItemPayload: buildItemPayload, safeFetchJson: safeFetchJson };
})();