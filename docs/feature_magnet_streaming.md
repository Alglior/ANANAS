# Feature: Magnet Link Image Streaming

## Overview

Serve images from torrent magnets as direct HTTP responses without saving full files to disk. When a user views an item's image gallery, the image is fetched on-demand from BitTorrent peers and streamed back in the response.

## Dependencies

Add to `requirements.txt`:
```
libtorrent>=2.0.9
```

libtorrent provides fast, C++-backed BitTorrent client bindings for Python (used by qBittorrent, Transmission).

## Architecture Changes

### New Blueprint: `src/stream_routes.py`

```
src/
├── stream_routes.py    # NEW — streaming endpoint
└── ...
```

### New Model Field (optional)

In `models.py`, add to `Item`:
```python
last_streamed_at: Mapped[datetime.datetime | None]
```
Track when an image was last streamed for caching decisions.

## Endpoints

```
GET /stream/image/<int:item_id>/<filename>
    → Streams the image from the item's magnet link
    → Returns 404 if no gallery image matches filename
    → Returns 504 if peers can't be reached in time
```

## Implementation Details

### 1. Torrent Client Session Manager

Single global `lt.session` instance (libtorrent session). One session per app avoids port conflicts and deduplicates downloads.

```python
# src/stream_routes.py

import libtorrent as lt
import threading
from flask import Blueprint, Response, abort, request
from app import db

bp = Blueprint("stream", __name__)

# Global session — initialized once on first request
_session = None
_lock = threading.Lock()


def _get_session():
    global _session
    if _session is None:
        with _lock:
            if _session is None:
                params = {
                    "listen_interfaces": "0.0.0.0:6881",
                    "max_halfopen": 50,
                    "denied_listen_times_ipv4": {"tcp": [592]},
                    "denied_listen_times_ipv6": {"tcp": [592]},
                }
                _session = lt.session(params=params)
                _session.start_dht()
    return _session
```

### 2. Piece Request Logic

For each magnet URL, create a `torrent_handle`. Download only files matching the requested filename. Use a callback to collect bytes into memory (or a temp file if >5MB).

```python
def _fetch_image_from_magnet(magnet_link: str, target_filename: str, timeout=15):
    """Fetch a single file from a torrent magnet link.

    Returns bytes of the matching file or None on timeout/error.
    """
    import time
    params = {"url": magnet_link, "paused": False}
    handle = _get_session().add_magnet_torrent(params)

    # Wait for metadata
    start = time.time()
    while not handle.has_metadata():
        if time.time() - start > timeout:
            return None
        time.sleep(0.3)

    # Set download priority to 0 for all files except the target
    fi = handle.get_file_info()
    priorities = [1] * len(fi)  # default priority = 1 (download)
    for idx, file in enumerate(fi):
        if not file.name.endswith(target_filename):
            priorities[idx] = 0  # skip non-target files
        else:
            priorities[idx] = 4  # highest priority for target

    handle.set_file_priority(priorities)

    # Wait until the target file is downloaded
    start = time.time()
    while True:
        if time.time() - start > timeout:
            return None

        status = handle.status()
        downloaded = sum(
            fi[idx].length for idx in range(len(fi))
            if handle.file_status(idx).completed
        )
        target_size = fi[next(i for i, f in enumerate(fi) if f.name.endswith(target_filename))].length

        if downloaded >= target_size and downloaded > 0:
            # Read the file from the session's disk cache
            try:
                with open(fi[0].path.replace(f"[{handle.torrent_file().name()}]", ""), "rb") as f:
                    return f.read()
            except Exception:
                return None

        time.sleep(0.5)
```

### 3. Cache Layer

Downloaded images should be cached to avoid re-downloading for repeated views.

```python
import hashlib
import os
from pathlib import Path

CACHE_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "instance" / "stream_cache"
CACHE_TTL = 3600  # 1 hour

def _cache_key(magnet_link: str, filename: str) -> str:
    raw = f"{magnet_link}:{filename}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _read_cached(key: str, filename: str):
    cache_path = CACHE_DIR / f"{key}.dat"
    if cache_path.exists():
        mtime = os.path.getmtime(cache_path)
        if time.time() - mtime < CACHE_TTL:
            return cache_path.read_bytes()
    return None


def _write_cached(data: bytes, key: str):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{key}.dat").write_bytes(data)
```

### 4. Route Handler

```python
@bp.route("/stream/image/<int:item_id>/<filename>")
def stream_image(item_id, filename):
    from models import Item, ItemGallery

    item = db.session.get(Item, item_id)
    if not item or not item.magnet_link:
        abort(404)

    # Find matching gallery image
    gallery = next((g for g in item.gallery_items if g.src and filename in g.src), None)
    if not gallery:
        abort(404)

    cache_key = _cache_key(item.magnet_link, filename)

    # Check cache first
    cached_data = _read_cached(cache_key, filename)
    if cached_data:
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
        ext = os.path.splitext(filename)[1]
        return Response(cached_data, content_type=mime_map.get(ext, "application/octet-stream"))

    # Fetch from torrent
    data = _fetch_image_from_magnet(item.magnet_link, filename, timeout=15)
    if not data:
        abort(504)  # Gateway timeout — peers not available

    _write_cached(data, cache_key)
    item.last_streamed_at = db.datetime.now()

    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
    ext = os.path.splitext(filename)[1]
    return Response(data, content_type=mime_map.get(ext, "application/octet-stream"))
```

### 5. Register Blueprint in `app.py`

In the blueprint registration section (around line 208):

```python
from src.stream_routes import bp as stream_bp
# ... later ...
app.register_blueprint(stream_bp)
```

### 6. Template Changes

In `templates/item_detail.html`, change image gallery `<img>` tags from static paths to the streaming endpoint:

```html
<!-- Before -->
<img src="{{ gallery.src }}" alt="...">

<!-- After -->
{% set filename = gallery.src.split('/')[-1] %}
<img src="{{ url_for('stream.stream_image', item_id=item.id, filename=filename) }}" alt="...">
```

## Caching Strategy

| Condition | Action |
|-----------|--------|
| Cache hit (within TTL) | Return cached bytes immediately |
| Cache miss | Fetch from torrent (15s timeout) |
| Fetch success | Write to cache, return + update `last_streamed_at` |
| Fetch failure | 504 — tell browser to retry later |

Cache lives in `instance/stream_cache/`. A cleanup cron job or periodic task can evict files older than TTL.

## Error Handling

| Scenario | HTTP Status | Response |
|----------|-------------|----------|
| No item found | 404 | JSON error |
| No matching gallery image | 404 | JSON error |
| Magnet link empty/invalid | 404 | JSON error |
| Timeout (no peers in 15s) | 504 | Retry after X seconds |
| Session creation fails | 500 | Log error, abort |

## Docker Considerations

Update `Dockerfile` to install libtorrent C++ dependencies:

```dockerfile
# Before installing Python packages
RUN apt-get update && apt-get install -y \
    libtorrent-rasterbar-dev \
    cmake \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
```

Or use a pre-built image like `python:3.12-slim-bookworm` where libtorrent wheels are available:
```
pip install Cython
pip install libtorrent --no-cache-dir
```

## Performance Notes

- **First view:** ~5-20s depending on peer availability and image size (typically 50-500KB for thumbnails)
- **Cached views:** <10ms (just a file read)
- **Concurrent requests** for the same magnet: libtorrent session deduplicates — only one fetch happens regardless of how many users request simultaneously
- Memory usage: ~20MB for session + upload/download buffers

## Security Notes

- The `filename` parameter is validated against actual torrent filenames to prevent path traversal
- Rate limit the streaming endpoint: 20 requests/minute per IP (add `@limiter.limit("20 per minute")`)
- Validate MIME types of returned data with `python-magic` or magic byte checks
- The cached files are served only through Flask — not exposed directly on disk

## Testing Plan

1. **Unit test:** `_fetch_image_from_magnet()` with a known public torrent containing a PNG image
2. **Integration test:** Mock libtorrent, verify the route returns 200 + correct content-type for valid item
3. **Integration test:** Verify 404 for nonexistent item_id or missing filename
4. **Integration test:** Verify 504 when session can't connect (offline torrent)
5. **Cache test:** First request triggers fetch, second request returns cached data

Add to `tests/test_stream.py`:
```python
def test_stream_image_not_found(client):
    res = client.get("/stream/image/99999/test.png")
    assert res.status_code == 404


def test_stream_image_no_magnet(client, db_session):
    # Item with no magnet_link
    item = Item(..., magnet_link="")
    db_session.add(item)
    db_session.commit()
    res = client.get(f"/stream/image/{item.id}/test.png")
    assert res.status_code == 404


def test_stream_image_success(client, db_session, mock_libtorrent):
    # Mock torrent returns sample PNG data
    item = Item(..., magnet_link="magnet:?xt=urn:btih:...")
    gallery = ItemGallery(item=item, media_type="image", src="/images/test.png", label="Test")
    db_session.add_all([item, gallery])
    db_session.commit()
    res = client.get(f"/stream/image/{item.id}/test.png")
    assert res.status_code == 200
    assert res.content_type.startswith("image/")
```

## Rollout Plan

1. **Phase 1:** Install libtorrent, create `stream_routes.py`, register blueprint — verify locally
2. **Phase 2:** Update templates to use streaming URLs, add cache layer
3. **Phase 3:** Add rate limiting, error handling, logging
4. **Phase 4:** Update Dockerfile, test in containerized environment
5. **Phase 5:** Deploy with feature flag — only enable for items with verified magnet links

## Rollback

If streaming causes issues (high memory, slow responses):
1. Revert template changes to use static gallery images
2. Remove `stream_bp` registration
3. Drop cache directory and clear `last_streamed_at` references
