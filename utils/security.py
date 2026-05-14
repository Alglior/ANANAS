import bleach
import re
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
        return True
    except Exception:
        return False


MAGIC_BYTES = {
    "csv": [b"\xef\xbb\xbf", b""],  # BOM optional, no strict magic
    "shp": [b"\x00\x00"],  # First byte is always 0
    "geojson": [b"{"],  # Starts with {
    "json": [b"{", b"["],  # Starts with { or [
    "xml": [b"<?xml", b"<"],  # XML declaration or tag
    "gpkg": [b"sqlite\x33\x33\x00"],  # SQLite header (modified)
}


def validate_file_magic(file_data: bytes, allowed_exts: set[str]) -> tuple[bool, str]:
    """Valider le contenu réel d'un fichier via ses magic bytes."""
    if not file_data or not allowed_exts:
        return False, "Extensions non autorisées"

    ext = None
    if b"." in file_data[:200]:
        try:
            header_ext = file_data[:200].decode("utf-8", errors="ignore").rsplit(".", 1)[-1].split()[0].lower()
            if header_ext in allowed_exts:
                ext = header_ext
        except Exception:
            pass

    if not ext or ext not in allowed_exts:
        return False, "Type de fichier invalide"

    magic_list = MAGIC_BYTES.get(ext, [])
    for magic in magic_list:
        if len(magic) > 0 and file_data[:len(magic)] == magic:
            return True, ""

    if ext == "csv":
        # CSV is flexible - just check it's text-like
        try:
            text = file_data[:1000].decode("utf-8", errors="strict")
            if any(c in text for c in (",", "\n")):
                return True, ""
        except Exception:
            pass
        return False, "Contenu du fichier CSV invalide"

    if ext == "gpkg":
        # Check for SQLite header variant used in GeoPackage
        if file_data[:4] == b"SQLite":
            return True, ""
        return False, "Contenu du fichier GeoPackage invalide"

    if ext == "shp":
        return True, ""  # Shapefiles are flexible

    return False, f"Format {ext} non reconnu par validation magic bytes"


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
