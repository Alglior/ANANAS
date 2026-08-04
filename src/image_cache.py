import hashlib
import logging
import os
import re
import time
from pathlib import Path

import requests

from app import db
from models import Item, ItemGallery

logger = logging.getLogger(__name__)

CACHE_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "instance" / "image_cache"
CACHE_TTL = 86400 * 30

QBITTORRENT_URL = os.environ.get("QBITTORRENT_URL", "http://qbittorrent:8081")
QBITTORRENT_USERNAME = os.environ.get("QBITTORRENT_USERNAME") or ""
QBITTORRENT_PASSWORD = os.environ.get("QBITTORRENT_PASSWORD") or ""
QBITTORRENT_DOWNLOADS = Path("/qbittorrent_downloads")
QBITTORRENT_SAVE_PATH = "/downloads/ananas"


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


def _qb_await_complete(session, info_hash, timeout=300):
    start = time.time()
    while True:
        if time.time() - start > timeout:
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
        if torrent.get("progress", 0) >= 1:
            return torrent
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


def download_image_from_magnet(magnet_link, timeout=300):
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
            data={"urls": magnet_link, "savepath": QBITTORRENT_SAVE_PATH},
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
                    torrent = _qb_await_complete(session, h, timeout)
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
            torrent = _qb_await_complete(session, h, timeout)
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
    relative_path = torrent.get("content_path", "")

    if not relative_path:
        name = torrent.get("name", info_hash)
        relative_path = str(Path(QBITTORRENT_SAVE_PATH) / name / image_file["name"])
    else:
        relative_path = str(Path(torrent["save_path"]) / image_file["name"])

    rel_for_mount = relative_path
    for prefix in ["/downloads/", "/qbittorrent_downloads/"]:
        if rel_for_mount.startswith(prefix):
            rel_for_mount = rel_for_mount[len(prefix):]
            break
    abs_path = QBITTORRENT_DOWNLOADS / rel_for_mount

    if not abs_path.exists():
        return None, None

    data = abs_path.read_bytes()

    try:
        _qb_delete_torrent(session, torrent["hash"])
    except Exception:
        pass

    return data, ext


def process_image_magnets(item_id, image_magnets):
    first_image = True
    try:
        for img in image_magnets:
            magnet = img.get("magnet_link", "").strip()
            label = img.get("label", "").strip()
            if not magnet:
                continue

            try:
                data = get_cached_image(magnet)
                ext = ".png"
                if data is None:
                    data, ext = download_image_from_magnet(magnet)
                    if data is None:
                        continue
                    ext = ext or ".png"

                src = cache_image(magnet, data, ext)

                gallery = ItemGallery(
                    item_id=item_id,
                    media_type="image",
                    src=src,
                    label=label or "Image",
                    data_json={
                        "magnet_link": magnet,
                        "original_filename": "image" + ext,
                    },
                )
                db.session.add(gallery)

                if first_image:
                    item = db.session.get(Item, item_id)
                    if item:
                        item.image_path = src
                    first_image = False
            except Exception as e:
                logger.error("Error downloading image magnet %s: %s", magnet, e)
                continue
    finally:
        item = db.session.get(Item, item_id)
        if item:
            item.image_magnets_pending = False
            item.image_magnets_total = 0
        db.session.commit()