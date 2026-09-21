import logging
import os
import re

from flask import render_template, redirect, url_for, request, Response, jsonify
import requests as http_requests

from app import db
from src.admin import bp, login_required, require_admin
from models import ItemImageJob, ItemGallery, Item


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


@bp.route("/api/admin/qbittorrent/cleanup", methods=["POST"])
@login_required
@require_admin
def admin_qbittorrent_cleanup():
    logger = logging.getLogger(__name__)
    qb_url = os.environ.get("QBITTORRENT_URL", "http://qbittorrent:8081")
    session = _qb_login()
    if session is None:
        return jsonify({"error": "Impossible de se connecter à qBittorrent"}), 502

    try:
        resp = session.get(f"{qb_url}/api/v2/torrents/info", timeout=10)
        resp.raise_for_status()
        torrents = resp.json()
    except Exception as e:
        logger.exception("qb cleanup: failed to fetch torrents")
        return jsonify({"error": f"Erreur lors de la récupération des torrents : {e}"}), 502

    try:
        magnets = set()
        rows = db.session.query(ItemImageJob.magnet_link).all()
        for (magnet_link,) in rows:
            m = (magnet_link or "").strip().lower()
            if m:
                magnets.add(m)
        rows = db.session.query(ItemGallery.data_json).all()
        for (data_json,) in rows:
            if data_json and isinstance(data_json, dict):
                m = (data_json.get("magnet_link") or "").strip().lower()
                if m:
                    magnets.add(m)
        rows = db.session.query(Item.image_magnet_links).all()
        for (links,) in rows:
            if isinstance(links, list):
                for link in links:
                    if isinstance(link, dict):
                        m = (link.get("magnet_link") or "").strip().lower()
                    elif isinstance(link, str):
                        m = link.strip().lower()
                    else:
                        continue
                    if m:
                        magnets.add(m)
    except Exception as e:
        logger.exception("qb cleanup: DB query error")
        return jsonify({"error": f"Erreur lors de l'interrogation de la base : {e}"}), 500

    known_hashes = set()
    for magnet in magnets:
        for m in re.findall(r"btih:([a-fA-F0-9]{40})", magnet):
            known_hashes.add(m.lower())
        for m in re.findall(r"btmh:1220([a-fA-F0-9]{64})", magnet):
            known_hashes.add(m[:40].lower())

    orphan_hashes = []
    for tor in torrents:
        info_hash = tor.get("hash", "").lower()
        if not info_hash:
            continue
        if info_hash in known_hashes:
            continue
        orphan_hashes.append(info_hash)

    cleaned = 0
    errors = 0
    qb_error = None

    if orphan_hashes:
        try:
            joined = "|".join(orphan_hashes)
            resp = session.post(
                f"{qb_url}/api/v2/torrents/delete",
                data={"hashes": joined, "deleteFiles": "true"},
                timeout=10,
            )
            if resp.status_code != 200:
                errors = len(orphan_hashes)
                qb_error = f"qBittorrent a répondu {resp.status_code}: {resp.text[:300]}"
                logger.error("qb cleanup: %s", qb_error)
            else:
                cleaned = len(orphan_hashes)
        except Exception as e:
            errors = len(orphan_hashes)
            qb_error = str(e)
            logger.exception("qb cleanup: delete request failed for %d torrent(s)", errors)

    return jsonify({
        "status": "ok",
        "cleaned": cleaned,
        "errors": errors,
        "message": f"{cleaned} torrent(s) orphelin(s) supprimé(s)" + (f", {errors} erreur(s)" if errors else ""),
        "qb_error": qb_error,
    })


def _qb_build_hash_to_magnet():
    """Construit la correspondance info_hash -> lien magnet depuis la base."""
    hash_to_magnet = {}

    def _register(magnet):
        magnet = (magnet or "").strip()
        if not magnet:
            return
        for m in re.findall(r"btih:([a-fA-F0-9]{40})", magnet):
            hash_to_magnet.setdefault(m.lower(), magnet)
        for m in re.findall(r"btmh:1220([a-fA-F0-9]{64})", magnet):
            hash_to_magnet.setdefault(m[:40].lower(), magnet)

    rows = db.session.query(ItemImageJob.magnet_link).all()
    for (magnet_link,) in rows:
        _register(magnet_link)
    rows = db.session.query(ItemGallery.data_json).all()
    for (data_json,) in rows:
        if data_json and isinstance(data_json, dict):
            _register(data_json.get("magnet_link"))
    rows = db.session.query(Item.image_magnet_links).all()
    for (links,) in rows:
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict):
                    _register(link.get("magnet_link"))
                elif isinstance(link, str):
                    _register(link)
    return hash_to_magnet


@bp.route("/api/admin/qbittorrent/restart", methods=["POST"])
@login_required
@require_admin
def admin_qbittorrent_restart():
    """Relance les téléchargements magnet en cours (non terminés).

    Couvre aussi l'arrêt Docker : les torrents laissés pausés/arrêtés côté
    qBittorrent sont repris, et le pipeline applicatif (attente de fin +
    sauvegarde en cache) est relancé pour les items dont des jobs d'images
    ne sont pas terminés (les threads sont morts au redémarrage).
    """
    logger = logging.getLogger(__name__)
    qb_url = os.environ.get("QBITTORRENT_URL", "http://qbittorrent:8081")
    session = _qb_login()
    if session is None:
        return jsonify({"error": "Impossible de se connecter à qBittorrent"}), 502

    try:
        hash_to_magnet = _qb_build_hash_to_magnet()
    except Exception as e:
        logger.exception("qb restart: DB query error")
        return jsonify({"error": f"Erreur lors de l'interrogation de la base : {e}"}), 500

    # 1) Reprise côté qBittorrent : on relance les téléchargements non terminés
    #    liés aux magnets du site, en particulier ceux restés pausés/arrêtés
    #    après un arrêt Docker.
    try:
        resp = session.get(f"{qb_url}/api/v2/torrents/info", timeout=10)
        resp.raise_for_status()
        torrents = resp.json()
    except Exception as e:
        logger.exception("qb restart: failed to fetch torrents")
        return jsonify({"error": f"Erreur lors de la récupération des torrents : {e}"}), 502

    paused_states = {
        "pausedDL", "stoppedDL", "queuedDL",
        "pausedUP", "stoppedUP", "queuedUP",
        "checkingResumeData", "error",
    }
    resumed = 0
    restarted = 0
    skipped = 0
    errors = 0
    qb_error = None

    for tor in torrents:
        info_hash = tor.get("hash", "").lower()
        if not info_hash:
            continue
        if tor.get("progress", 0) >= 1:
            continue
        if info_hash not in hash_to_magnet:
            skipped += 1
            continue
        try:
            # Torrent resté en pause/arrêt (ex. stop Docker) : on le relance.
            if tor.get("state", "") in paused_states:
                session.post(
                    f"{qb_url}/api/v2/torrents/start",
                    data={"hashes": info_hash},
                    timeout=10,
                )
                resumed += 1
            # Force l'annonce aux trackers (aide les torrents stalled / metadata manquante).
            session.post(
                f"{qb_url}/api/v2/torrents/reannounce",
                data={"hashes": info_hash},
                timeout=10,
            )
            restarted += 1
        except Exception as e:
            errors += 1
            qb_error = str(e)
            logger.exception("qb restart: failed to resume %s", info_hash)

    # 2) Relance du pipeline applicatif : les threads qui attendaient la fin des
    #    téléchargements sont morts au redémarrage ; on re-soumet les items aux
    #    images non terminées pour re-traiter (attente + sauvegarde en cache).
    kicked = 0
    cleaned = 0
    try:
        from src.user_routes import relaunch_unfinished_image_jobs
        kicked, cleaned = relaunch_unfinished_image_jobs()
    except Exception:
        logger.exception("qb restart: failed to relaunch image processing")

    parts = []
    if restarted:
        parts.append(f"{restarted} torrent(s) relancé(s) ({resumed} repris après arrêt)")
    if kicked:
        parts.append(f"{kicked} item(s) au traitement relancé(s)")
    if cleaned:
        parts.append(f"{cleaned} item(s) au statut 'en cours' corrigé(s)")
    if skipped:
        parts.append(f"{skipped} torrent(s) ignoré(s) (terminé ou non lié)")
    if errors:
        parts.append(f"{errors} erreur(s)")
    if not parts:
        parts.append("Aucun téléchargement à relancer")
    message = ", ".join(parts)
    if qb_error:
        message += f" — {qb_error}"

    return jsonify({
        "status": "ok",
        "restarted": restarted,
        "resumed": resumed,
        "kicked": kicked,
        "skipped": skipped,
        "errors": errors,
        "message": message,
        "qb_error": qb_error,
    })