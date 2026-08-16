from flask import request, jsonify
from src.admin import bp, api_admin_required, login_required
from src.admin import _log_audit, _require_json, get_catalogues_status, _save_catalogues_status, _CATALOGUES_INFO


@bp.route("/api/admin/catalogues/<catalogue_type>/toggle", methods=["POST"])
@login_required
@api_admin_required
def toggle_catalogue(catalogue_type):
    valid_types = [info["type"] for info in _CATALOGUES_INFO]
    if catalogue_type not in valid_types:
        return jsonify({"error": "Type de catalogue invalide"}), 400

    data, error, code = _require_json()
    if error:
        return error, code
    active = data.get("active", True)

    status = get_catalogues_status()
    status[catalogue_type] = bool(active)
    _save_catalogues_status(status)

    _log_audit(
        "catalogue_toggle" if not active else "catalogue_enable",
        "catalogue", target_type=catalogue_type,
        details={"catalogue": catalogue_type, "active": bool(active)},
    )
    return jsonify({"status": "updated", "catalogue": catalogue_type, "active": bool(active)})