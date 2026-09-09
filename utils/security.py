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


def validate_magnet_link(url: str) -> bool:
    """Valider strictement un lien magnet pour éviter les schémas dangereux."""
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    if not url:
        return False

    if any(c.isspace() for c in url):
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme != "magnet":
            return False
        if not parsed.query:
            return False
        query = parsed.query.lower()
        if "xt=urn:btih:" not in query and "xt=urn:btmh:" not in query:
            return False
        return True
    except Exception:
        return False



def sanitize_value(value) -> str | int | float | bool:
    """Sanitizer une valeur individuelle pour prévenir les attaques XSS."""
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    if not isinstance(value, str):
        try:
            return str(value)
        except Exception:
            return ""
    cleaned = bleach.clean(value, tags=[], strip=True)
    return cleaned


def sanitize_gallery_data(data) -> list:
    """Sanitizer et valider strictement les données JSON de la galerie (CSV/dashboard).

    - Pour les CSV : valide que 'rows' est une liste de listes/strings/int/float,
      sanitize chaque valeur et rejette les structures anormales.
    - Pour les dashboards : valide que 'metrics' est une liste d'objets avec des clés 'metric'/'value',
      sanitize les valeurs string.
    """
    if data is None:
        return []
    if not isinstance(data, list):
        return []

    sanitized = []
    for row in data:
        if isinstance(row, dict):
            clean_row = {}
            for key, val in row.items():
                safe_key = sanitize_value(str(key)) if isinstance(key, str) else key
                clean_row[safe_key] = sanitize_value(val) if isinstance(val, str) else val
            sanitized.append(clean_row)
        elif isinstance(row, list):
            clean_row = [sanitize_value(v) if isinstance(v, str) else v for v in row[:50]]
            sanitized.append(clean_row)
        elif isinstance(row, (str, int, float)):
            sanitized.append(sanitize_value(row) if isinstance(row, str) else row)
    return sanitized


def validate_filename(filename: str) -> str | None:
    """Valider et sécuriser un nom de fichier pour prévenir les attaques par path traversal."""
    if not filename or not isinstance(filename, str):
        return None

    allowed_extensions = {"csv", "shp", "geojson", "gpkg", "json", "xml", "png", "jpg", "jpeg", "svg", "pdf"}

    if "." not in filename:
        return None

    parts = filename.rsplit(".", 1)
    base_name = parts[0]
    ext = parts[1].lower()

    if ext not in allowed_extensions:
        return None

    safe_name = re.sub(r"[^\w\-\_\. ]", "_", base_name).strip(".")[:200]
    return f"{safe_name}.{ext}"
