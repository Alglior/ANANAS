import hashlib
import logging
import os
import re
import threading
import time
from pathlib import Path

import requests

from app import db
from models import Item, ItemGallery, ItemImageJob

logger = logging.getLogger(__name__)

CACHE_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "instance" / "image_cache"
CACHE_TTL = 86400 * 30

QBITTORRENT_URL = os.environ.get("QBITTORRENT_URL", "http://qbittorrent:8081")
QBITTORRENT_USERNAME = os.environ.get("QBITTORRENT_USERNAME") or ""
QBITTORRENT_PASSWORD = os.environ.get("QBITTORRENT_PASSWORD") or ""
QBITTORRENT_DOWNLOADS = Path("/qbittorrent_downloads")
QBITTORRENT_SAVE_PATH = "/downloads/ananas"

PUBLIC_TRACKERS = "\n".join([
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.moeking.me:6969/announce",
    "https://tracker.nanoha.org:443/announce",
    "https://tracker.lilithraws.org:443/announce",
])

# Registre de verrous par item : empêche que deux tâches de fond traitent le même
# item simultanément (édition rapide / double soumission -> doublons de galerie).
_item_locks = {}
_item_locks_guard = threading.Lock()


def _acquire_item_processing_lock(item_id):
    with _item_locks_guard:
        lock = _item_locks.setdefault(item_id, threading.Lock())
    acquired = lock.acquire(blocking=False)
    return lock if acquired else None


def _release_item_processing_lock(item_id, lock):
    lock.release()
    with _item_locks_guard:
        _item_locks.pop(item_id, None)


def _cache_path(magnet_link):
    h = hashlib.sha256(magnet_link.encode()).hexdigest()[:16]
    return CACHE_DIR / h


def get_cached_image(magnet_link):
    p = _cache_path(magnet_link)
    if p.exists():
        mtime = os.path.getmtime(p)
        if time.time() - mtime < CACHE_TTL:
            return p.read_bytes()
    return None


def cache_image(magnet_link, data, ext=".png"):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _cache_path(magnet_link)
    p.write_bytes(data)
    return "/static/cache/img/" + p.name + ext


def _qb_login():
    session = requests.Session()
    session.headers.update({"Referer": QBITTORRENT_URL + "/"})
    resp = session.post(
        f"{QBITTORRENT_URL}/api/v2/auth/login",
        data={"username": QBITTORRENT_USERNAME, "password": QBITTORRENT_PASSWORD},
        timeout=10,
    )
    resp.raise_for_status()
    return session


def _extract_info_hashes(magnet_link):
    v1 = re.search(r"btih:([a-fA-F0-9]{40})", magnet_link)
    v2 = re.search(r"btmh:1220([a-fA-F0-9]{64})", magnet_link)
    hashes = []
    if v1:
        hashes.append(v1.group(1).lower())
    if v2:
        hashes.append(v2.group(1)[:40].lower())
    return hashes


def _qb_await_complete(session, info_hash, on_progress=None):
    while True:

        resp = session.get(
            f"{QBITTORRENT_URL}/api/v2/torrents/info",
            params={"hashes": info_hash},
            timeout=10,
        )
        resp.raise_for_status()
        torrents = resp.json()
        if not torrents:
            return None

        torrent = torrents[0]
        state = torrent.get("state", "")
        progress = torrent.get("progress", 0)
        if on_progress is not None and progress != last_reported:
            on_progress(float(progress))
            last_reported = progress
        if progress >= 1:
            return torrent
        # Si le torrent est en échec (pas de seeds, stalled, etc.)
        if state in ("error", "missingFiles", "unknown"):
            logger.warning("Torrent %s in error state: %s", info_hash, state)
            return None
        time.sleep(2)


def _qb_get_file_paths(session, info_hash):
    resp = session.get(
        f"{QBITTORRENT_URL}/api/v2/torrents/files",
        params={"hash": info_hash},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _qb_delete_torrent(session, info_hash):
    session.post(
        f"{QBITTORRENT_URL}/api/v2/torrents/delete",
        params={"hashes": info_hash, "deleteFiles": False},
    )


def _qb_get_torrent(session, info_hash):
    resp = session.get(
        f"{QBITTORRENT_URL}/api/v2/torrents/info",
        params={"hashes": info_hash},
        timeout=10,
    )
    resp.raise_for_status()
    torrents = resp.json()
    return torrents[0] if torrents else None


def download_image_from_magnet(magnet_link, on_progress=None):
    info_hashes = _extract_info_hashes(magnet_link)
    if not info_hashes:
        return None, None

    try:
        session = _qb_login()
    except Exception as e:
        logger.error("qBittorrent login failed: %s", e)
        return None, None

    try:
        resp = session.post(
            f"{QBITTORRENT_URL}/api/v2/torrents/add",
            data={"urls": magnet_link, "savepath": QBITTORRENT_SAVE_PATH, "trackers": PUBLIC_TRACKERS},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        if hasattr(e, "response") and e.response is not None and e.response.status_code == 409:
            torrent = None
            for h in info_hashes:
                existing = _qb_get_torrent(session, h)
                if existing and existing.get("progress", 0) >= 1:
                    torrent = existing
                    break
                elif existing:
                    torrent = _qb_await_complete(session, h, on_progress)
                    if torrent:
                        break
            if torrent is None:
                logger.error("qBittorrent add magnet failed (409 but torrent not found): %s", e)
                return None, None
        else:
            logger.error("qBittorrent add magnet failed: %s", e)
            return None, None
    else:
        torrent = None
        for h in info_hashes:
            torrent = _qb_await_complete(session, h, on_progress)
            if torrent:
                break
        if torrent is None:
            return None, None

    files = _qb_get_file_paths(session, torrent["hash"])
    image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    image_file = None
    for f in files:
        name = f.get("name", "")
        if any(name.lower().endswith(ext) for ext in image_extensions):
            image_file = f
            break

    if image_file is None:
        return None, None

    ext = Path(image_file["name"]).suffix.lower()
    content_path = torrent.get("content_path", "")

    candidates = []
    if content_path:
        cp = str(content_path)
        candidates.append(str(Path(cp) / image_file["name"]))
        candidates.append(cp)
    else:
        name = torrent.get("name", info_hashes[0] if info_hashes else "")
        candidates.append(str(Path(QBITTORRENT_SAVE_PATH) / name / image_file["name"]))
        candidates.append(str(Path(torrent["save_path"]) / image_file["name"]))

    data = None
    for candidate in candidates:
        rel_for_mount = candidate
        for prefix in ["/downloads/", "/qbittorrent_downloads/"]:
            if rel_for_mount.startswith(prefix):
                rel_for_mount = rel_for_mount[len(prefix):]
                break
        abs_path = QBITTORRENT_DOWNLOADS / rel_for_mount
        if abs_path.exists():
            data = abs_path.read_bytes()
            break

    if data is None:
        return None, None

    try:
        _qb_delete_torrent(session, torrent["hash"])
    except Exception:
        pass

    return data, ext


def process_image_magnets(item_id, image_magnets):
    lock = _acquire_item_processing_lock(item_id)
    if lock is None:
        logger.info("Image processing already running for item %s; skipping duplicate.", item_id)
        return

    first_image = True
    processed = 0
    failed = 0

    try:
        ItemImageJob.query.filter_by(item_id=item_id).delete()
        jobs = []
        for i, img in enumerate(image_magnets):
            if not isinstance(img, dict):
                continue
            magnet = (img.get("magnet_link") or "").strip()
            if not magnet:
                continue
            jobs.append(ItemImageJob(
                item_id=item_id, idx=i, magnet_link=magnet,
                label=(img.get("label") or "").strip() or "Image",
                status="pending", progress=0.0,
            ))
        for j in jobs:
            db.session.add(j)
        item = db.session.get(Item, item_id)
        if item:
            item.image_magnets_pending = True
            item.image_magnets_total = len(jobs)
        db.session.commit()

        for job in jobs:
            magnet = job.magnet_link
            label = job.label or "Image"

            try:
                data = get_cached_image(magnet)
                ext = ".png"
                if data is None:
                    job.status = "downloading"
                    job.progress = 0.0
                    job.details = "Téléchargement du torrent en cours..."
                    db.session.commit()

                    def _on_progress(p, _job=job):
                        _job.progress = p
                        if _job.status != "downloading":
                            _job.status = "downloading"
                        _job.details = f"Téléchargement en cours ({round(p * 100)} %)"
                        db.session.commit()

                    data, ext = download_image_from_magnet(magnet, on_progress=_on_progress)
                    if data is None:
                        failed += 1
                        job.status = "failed"
                        job.progress = 0.0
                        job.details = "Échec : aucune source disponible ou délai dépassé"
                        db.session.commit()
                        continue
                    ext = ext or ".png"

                job.status = "saving"
                job.details = "Enregistrement de l'image..."
                db.session.commit()

                src = cache_image(magnet, data, ext)

                gallery = ItemGallery(
                    item_id=item_id,
                    media_type="image",
                    src=src,
                    label=label,
                    data_json={
                        "magnet_link": magnet,
                        "original_filename": "image" + ext,
                    },
                )
                db.session.add(gallery)
                processed += 1

                job.status = "done"
                job.progress = 1.0
                job.details = "Terminé"
                db.session.commit()

                if first_image:
                    item = db.session.get(Item, item_id)
                    if item:
                        item.image_path = src
                        db.session.commit()
                    first_image = False
            except Exception as e:
                failed += 1
                logger.exception("Item %s: error downloading image magnet %s: %s", item_id, magnet, e)
                job.status = "failed"
                job.details = str(e)[:200]
                db.session.commit()
                continue
    finally:
        item = db.session.get(Item, item_id)
        if item:
            item.image_magnets_pending = False
            item.image_magnets_total = 0
            item.refresh_imod_cache()
        db.session.commit()
        _release_item_processing_lock(item_id, lock)
        logger.info(
            "Item %s: image processing done (processed=%s, failed=%s)",
            item_id, processed, failed,
        )