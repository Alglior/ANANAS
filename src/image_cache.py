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

# Délai maximal d'un téléchargement d'image (2 h). Au-delà, le job est marqué
# en échec et un nouveau téléchargement est retenté.
DOWNLOAD_TIMEOUT = 2 * 60 * 60
MAX_DOWNLOAD_ATTEMPTS = 10

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


def purge_expired_cache(cache_dir=None, max_age=None):
    """Supprime les fichiers de cache plus vieux que le TTL et plus référencés.

    Le TTL n'est jusqu'ici vérifié qu'à la réutilisation d'un magnet : sans purge,
    les fichiers non réutilisés restent sur le disque indéfiniment. Cette fonction
    nettoie les entrées expirées qui ne sont plus référencées par aucun item
    (image principale ou galerie), afin de borner la taille du cache.
    """
    cache_dir = Path(cache_dir or CACHE_DIR)
    max_age = max_age if max_age is not None else CACHE_TTL
    if not cache_dir.is_dir():
        return 0
    cutoff = time.time() - max_age
    deleted = 0
    skipped = 0
    for p in sorted(cache_dir.iterdir()):
        if not p.is_file():
            continue
        try:
            if os.path.getmtime(p) >= cutoff:
                continue
        except OSError:
            continue
        # Ne jamais supprimer un fichier encore référencé par un item (image
        # cassée sinon) : il sera purgé une fois qu'il ne sera plus utilisé.
        if _cache_file_in_use(p, exclude_item_id=None):
            skipped += 1
            continue
        try:
            p.unlink()
            deleted += 1
        except OSError:
            pass
    if deleted:
        logger.info(
            "purge_expired_cache: %d fichier(s) expiré(s) supprimé(s), %d conservé(s) (référencé(s))",
            deleted, skipped,
        )
    return deleted


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


def _qb_await_complete(session, info_hash, on_progress=None, timeout=DOWNLOAD_TIMEOUT):
    last_reported = -1
    deadline = time.time() + timeout
    while True:
        if time.time() >= deadline:
            logger.warning(
                "Torrent %s: délai de %ss dépassé, téléchargement abandonné",
                info_hash, timeout,
            )
            return None

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
        data={"hashes": info_hash, "deleteFiles": "false"},
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


def remove_magnet_from_qbittorrent(magnet_link):
    """Supprime tout torrent qBittorrent correspondant au magnet.

    Utilisé avant un nouvel essai afin de repartir d'un ajout propre au lieu de
    ré-attendre un torrent bloqué.
    """
    info_hashes = _extract_info_hashes(magnet_link)
    if not info_hashes:
        return
    try:
        session = _qb_login()
    except Exception as e:
        logger.error("qBittorrent login failed during retry cleanup: %s", e)
        return
    for h in info_hashes:
        try:
            torrent = _qb_get_torrent(session, h)
        except Exception:
            continue
        if torrent:
            try:
                _qb_delete_torrent(session, torrent["hash"])
            except Exception:
                pass


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


def _cache_file_in_use(cache_path, exclude_item_id):
    """Vérifie si un fichier de cache image est encore référencé par un autre item."""
    stem = cache_path.name
    prefix = "/static/cache/img/" + stem + "."
    if Item.query.filter(
        Item.id != exclude_item_id,
        Item.image_path.like(prefix + "%"),
    ).first():
        return True
    if ItemGallery.query.filter(
        ItemGallery.item_id != exclude_item_id,
        ItemGallery.src.like(prefix + "%"),
    ).first():
        return True
    return False


def _magnet_cache_in_use(magnet, cache_path, exclude_item_id):
    """Vérifie si un magnet (et son fichier de cache) est encore utilisé par un autre item."""
    if _cache_file_in_use(cache_path, exclude_item_id):
        return True
    if ItemImageJob.query.filter(
        ItemImageJob.item_id != exclude_item_id,
        ItemImageJob.magnet_link == magnet,
    ).first():
        return True
    return False


def delete_item_cached_images(item):
    """Supprime les fichiers images en cache pour un item (gallerie + image principale).

    Le cache étant partagé entre les items qui utilisent le même lien Magnet, un
    fichier n'est supprimé que si aucun autre item ne le référence encore.
    """
    deleted = 0
    skipped = 0
    magnets = set()

    for gallery in item.gallery_items:
        if gallery.data_json:
            magnet = gallery.data_json.get("magnet_link")
            if magnet:
                magnets.add(magnet)

    for job in item.image_jobs:
        if job.magnet_link:
            magnets.add(job.magnet_link)

    for magnet in magnets:
        p = _cache_path(magnet)
        if p.exists():
            if _magnet_cache_in_use(magnet, p, item.id):
                skipped += 1
                continue
            p.unlink()
            deleted += 1

    if item.image_path and item.image_path.startswith("/static/cache/img/"):
        stem = Path(item.image_path).stem
        fp = CACHE_DIR / stem
        if fp.exists():
            if _cache_file_in_use(fp, item.id):
                skipped += 1
            else:
                fp.unlink()
                deleted += 1

    if deleted:
        logger.info("delete_item_cached_images: removed %d file(s) for item %s", deleted, item.id)
    if skipped:
        logger.info("delete_item_cached_images: kept %d shared cache file(s) for item %s", skipped, item.id)
    return deleted


def normalize_image_magnets(image_magnets):
    """Normalise une liste d'aimants d'image et la déduplique par lien magnet.

    Un même lien magnet ne peut produire qu'une seule image : une entrée en
    double dans la liste ne doit jamais générer de doublon de galerie.
    """
    if not isinstance(image_magnets, list):
        return []
    magnets = []
    seen = set()
    for entry in image_magnets:
        if isinstance(entry, dict):
            magnet = (entry.get("magnet_link") or "").strip()
            if not magnet or magnet in seen:
                continue
            seen.add(magnet)
            magnets.append({
                "magnet_link": magnet,
                "label": (entry.get("label") or "").strip() or "Image",
            })
        elif isinstance(entry, str):
            magnet = entry.strip()
            if not magnet or magnet in seen:
                continue
            seen.add(magnet)
            magnets.append({"magnet_link": magnet, "label": "Image"})
    return magnets


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
        ItemGallery.query.filter_by(item_id=item_id, media_type="image").delete()
        jobs = []
        for i, img in enumerate(normalize_image_magnets(image_magnets)):
            magnet = img.get("magnet_link", "")
            jobs.append(ItemImageJob(
                item_id=item_id, idx=i, magnet_link=magnet,
                label=img.get("label") or "Image",
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
                    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
                        job.status = "downloading"
                        job.progress = 0.0
                        job.details = (
                            f"Téléchargement du torrent en cours "
                            f"(essai {attempt}/{MAX_DOWNLOAD_ATTEMPTS})..."
                        )
                        db.session.commit()

                        def _on_progress(p, _job=job):
                            _job.progress = p
                            if _job.status != "downloading":
                                _job.status = "downloading"
                            _job.details = f"Téléchargement en cours ({round(p * 100)} %)"
                            db.session.commit()

                        data, ext = download_image_from_magnet(magnet, on_progress=_on_progress)
                        if data is not None:
                            break

                        # Échec ou délai de 2 h dépassé : on marque le job en échec
                        # puis on retente un téléchargement propre.
                        if attempt < MAX_DOWNLOAD_ATTEMPTS:
                            job.status = "failed"
                            job.progress = 0.0
                            job.details = (
                                f"Échec de l'essai {attempt} (délai dépassé), "
                                f"nouvel essai en cours..."
                            )
                            db.session.commit()
                            remove_magnet_from_qbittorrent(magnet)
                    else:
                        data = None

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