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
      if (magnetLinks.length === 1) {
        payload.data_format_level = 'pack';
        payload.magnet_link = magnetLinks[0].magnet_link;
      } else if (magnetLinks.length > 1) {
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