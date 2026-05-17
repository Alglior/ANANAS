import bleach
import re
import ipaddress
from urllib.parse import urlparse


ALLOWED_URL_SCHEMES = {"http", "https"}


def sanitize_html(value: str, strip=True) -> str:
    """Nettoyer le texte saisi pour prévenir les attaques XSS."""
    return bleach.clean(value, tags=[], strip=strip)


def validate_external_url(url: str) -> bool:
    """Vérifier qu'une URL externe est sûre pour l'affichage."""
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    if not url:
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            return False
        if "@" in url:
            return False
        hostname = parsed.hostname.lower()
        if not hostname:
            return False
        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local or addr.is_multicast:
                return False
        except ValueError:
            pass
        if "." not in hostname and ":" not in hostname:
            return False
        parts = hostname.split(".")
        if len(parts) < 2:
            if not any(c.isdigit() for c in hostname):
                return False
        return True
    except Exception:
        return False



def validate_filename(filename: str) -> str | None:
    """Valider et sécuriser un nom de fichier pour prévenir les attaques par path traversal."""
    if not filename or not isinstance(filename, str):
        return None

    allowed_extensions = {"csv", "shp", "geojson", "gpkg", "json", "xml", "png", "jpg", "jpeg", "gif", "svg", "pdf"}

    if "." not in filename:
        return None

    parts = filename.rsplit(".", 1)
    base_name = parts[0]
    ext = parts[1].lower()

    if ext not in allowed_extensions:
        return None

    safe_name = re.sub(r"[^\w\-\_\. ]", "_", base_name).strip(".")[:200]
    return f"{safe_name}.{ext}"
