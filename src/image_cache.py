import hashlib
import os
import re
import time
from pathlib import Path

import requests

from app import db
from models import Item, ItemGallery

CACHE_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "instance" / "image_cache"
CACHE_TTL = 86400 * 30

QBITTORRENT_URL = os.environ.get("QBITTORRENT_URL", "http://qbittorrent:8081")
QBITTORRENT_USERNAME = os.environ.get("QBITTORRENT_USERNAME", "admin")
QBITTORRENT_PASSWORD = os.environ.get("QBITTORRENT_PASSWORD", "adminadmin")
QBITTORRENT_DOWNLOADS = Path("/qbittorrent_downloads")
QBITTORENT_SAVE_PATH = "/downloads/ananas"


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


def _extract_info_hash(magnet_link):
    m = re.search(r"btih:([a-fA-F0-9]{40})", magnet_link)
    return m.group(1).lower() if m else None


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


def download_image_from_magnet(magnet_link, timeout=300):
    info_hash = _extract_info_hash(magnet_link)
    if not info_hash:
        return None, None

    try:
        session = _qb_login()
    except Exception as e:
        print(f"qBittorrent login failed: {e}")
        return None, None

    try:
        resp = session.post(
            f"{QBITTORRENT_URL}/api/v2/torrents/add",
            data={"urls": magnet_link, "savepath": QBITTORENT_SAVE_PATH},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"qBittorrent add magnet failed: {e}")
        return None, None

    torrent = _qb_await_complete(session, info_hash, timeout)
    if torrent is None:
        return None, None

    files = _qb_get_file_paths(session, info_hash)
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
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
        relative_path = str(Path(QBITTORENT_SAVE_PATH) / name / image_file["name"])
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
                print(f"Error downloading image magnet {magnet}: {e}")
                continue
    finally:
        item = db.session.get(Item, item_id)
        if item:
            item.image_magnets_pending = False
            item.image_magnets_total = 0
        db.session.commit()