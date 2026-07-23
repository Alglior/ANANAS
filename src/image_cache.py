import hashlib
import os
import time
from pathlib import Path

import libtorrent as lt

from app import db
from models import ItemGallery

CACHE_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "instance" / "image_cache"
CACHE_TTL = 86400 * 30


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


def download_image_from_magnet(magnet_link, timeout=60):
    session = lt.session({"listen_interfaces": "0.0.0.0:6881"})
    session.start_dht()

    try:
        handle = session.add_magnet_torrent({"url": magnet_link, "paused": False})
        start = time.time()

        while not handle.has_metadata():
            if time.time() - start > timeout:
                return None, None
            time.sleep(0.5)

        fi = handle.get_file_info()
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
        image_files = [
            (idx, f) for idx, f in enumerate(fi)
            if any(f.name.lower().endswith(ext) for ext in image_extensions)
        ]

        if not image_files:
            return None, None

        idx, target = image_files[0]
        ext = Path(target.name).suffix.lower()

        priorities = [0] * len(fi)
        priorities[idx] = 4
        handle.set_file_priority(priorities)

        start = time.time()
        while True:
            if time.time() - start > timeout:
                return None, None
            if handle.file_status(idx).completed:
                break
            time.sleep(0.5)

        save_path = handle.status().save_path
        file_path = Path(save_path) / target.name
        if file_path.exists():
            return file_path.read_bytes(), ext

        return None, None
    finally:
        session.pause()


def process_image_magnets(item_id, image_magnets):
    for img in image_magnets:
        magnet = img.get("magnet_link", "").strip()
        label = img.get("label", "").strip()
        if not magnet:
            continue

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
    db.session.commit()
