import os

from flask import render_template, redirect, url_for, request, Response, jsonify
import requests as http_requests

from src.admin import bp, login_required, require_admin


@bp.route("/admin/reports")
@login_required
@require_admin
def admin_reports():
    return redirect(url_for("admin.admin_moderation"))


@bp.route("/admin/moderation")
@login_required
@require_admin
def admin_moderation():
    return render_template("admin/moderation.html", title="Administration — Modération", meta_description="Modération des contenus et commentaires")


@bp.route("/admin/audit")
@login_required
@require_admin
def admin_audit():
    return render_template("admin/audit.html", title="Administration — Journal d'audits", meta_description="Journal des actions administratives")


@bp.route("/admin/contact-messages")
@login_required
@require_admin
def admin_contact_messages():
    return redirect(url_for("admin.admin_moderation"))


@bp.route("/admin/mirrors")
@login_required
@require_admin
def admin_mirrors():
    return render_template("admin/mirrors.html", title="Administration — Sites miroirs", meta_description="Gestion des sites miroirs")


@bp.route("/admin/featured")
@login_required
@require_admin
def admin_featured():
    return render_template("admin/featured.html", title="Administration — Données en avant", meta_description="Gestion des données mises en avant")


@bp.route("/admin/geopackages")
@login_required
@require_admin
def admin_geopackages():
    return render_template("admin/geopackages.html", title="Administration — GeoPackages", meta_description="Gestion des packs GeoPackage")


@bp.route("/admin/replication")
@login_required
@require_admin
def admin_replication():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/admin/tags")
@login_required
@require_admin
def admin_tags():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/admin/accueil")
@login_required
@require_admin
def admin_home():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/admin/catalogues")
@login_required
@require_admin
def admin_catalogues():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/admin/qbittorrent")
@login_required
@require_admin
def admin_qbittorrent():
    return render_template(
        "admin/qbittorrent.html",
        title="Administration — qBittorrent",
        meta_description="Statut du client BitTorrent",
    )


def _qb_login():
    session = http_requests.Session()
    session.headers.update({"Referer": os.environ.get("QBITTORRENT_URL", "http://qbittorrent:8081") + "/"})
    try:
        resp = session.post(
            f"{os.environ.get('QBITTORRENT_URL', 'http://qbittorrent:8081')}/api/v2/auth/login",
            data={
                "username": os.environ.get("QBITTORRENT_USERNAME", ""),
                "password": os.environ.get("QBITTORRENT_PASSWORD", ""),
            },
            timeout=10,
        )
        resp.raise_for_status()
        return session
    except Exception as e:
        return None


@bp.route("/api/admin/qbittorrent/status")
@login_required
@require_admin
def admin_qbittorrent_status():
    qb_url = os.environ.get("QBITTORRENT_URL", "http://qbittorrent:8081")
    session = _qb_login()
    if session is None:
        return jsonify({"error": "Impossible de se connecter à qBittorrent"}), 502

    try:
        resp = session.get(f"{qb_url}/api/v2/transfer/info", timeout=10)
        resp.raise_for_status()
        transfer = resp.json()
    except Exception:
        transfer = {}

    try:
        resp = session.get(f"{qb_url}/api/v2/torrents/info", timeout=10)
        resp.raise_for_status()
        torrents = resp.json()
    except Exception:
        torrents = []

    return jsonify({
        "connected": True,
        "transfer": {
            "dl_speed": transfer.get("dl_info_speed", 0),
            "up_speed": transfer.get("up_info_speed", 0),
            "dl_data": transfer.get("dl_info_data", 0),
            "up_data": transfer.get("up_info_data", 0),
        },
        "torrents": [
            {
                "hash": t.get("hash", ""),
                "name": t.get("name", ""),
                "size": t.get("size", 0),
                "progress": round(t.get("progress", 0) * 100, 1),
                "state": t.get("state", ""),
                "dl_speed": t.get("dlspeed", 0),
                "up_speed": t.get("upspeed", 0),
                "eta": t.get("eta", 0),
                "added_on": t.get("added_on", 0),
            }
            for t in torrents
        ],
    })