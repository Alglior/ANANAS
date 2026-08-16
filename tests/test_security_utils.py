"""Tests unitaires des utilitaires de sécurité et de validation."""
from utils.security import (sanitize_html, validate_external_url,
                            validate_magnet_link, sanitize_value,
                            sanitize_gallery_data, validate_filename)
from src.shared import validate_password_strength, _build_page_numbers


class TestSanitizeHtml:
    def test_strips_tags(self):
        # bleach.clean(tags=[]) retire les balises mais conserve le texte brut.
        assert sanitize_html('<script>alert(1)</script>') == 'alert(1)'
        assert sanitize_html('<b>texte</b>') == 'texte'

    def test_keeps_plain_text(self):
        assert sanitize_html('Bonjour le monde') == 'Bonjour le monde'


class TestValidateExternalUrl:
    def test_valid_https(self):
        assert validate_external_url('https://example.com/path') is True

    def test_valid_http(self):
        assert validate_external_url('http://example.com') is True

    def test_rejects_non_http(self):
        assert validate_external_url('ftp://example.com') is False
        assert validate_external_url('javascript:alert(1)') is False
        assert validate_external_url('file:///etc/passwd') is False

    def test_rejects_credentials(self):
        assert validate_external_url('https://user@host.com') is False

    def test_rejects_private_ip(self):
        assert validate_external_url('https://192.168.1.1') is False
        assert validate_external_url('https://127.0.0.1') is False

    def test_rejects_no_hostname(self):
        assert validate_external_url('https://') is False
        assert validate_external_url('') is False
        assert validate_external_url(None) is False


class TestValidateMagnetLink:
    def test_valid_btih(self):
        assert validate_magnet_link('magnet:?xt=urn:btih:abcd1234') is True

    def test_valid_btmh(self):
        assert validate_magnet_link('magnet:?xt=urn:btmh:abcd1234') is True

    def test_rejects_non_magnet(self):
        assert validate_magnet_link('https://example.com') is False
        assert validate_magnet_link('javascript:x') is False

    def test_rejects_no_hash(self):
        assert validate_magnet_link('magnet:?dn=file') is False

    def test_rejects_whitespace(self):
        assert validate_magnet_link('magnet:?xt=urn:btih:a b') is False


class TestSanitizeValue:
    def test_scalars_passthrough(self):
        assert sanitize_value(None) is None
        assert sanitize_value(42) == 42
        assert sanitize_value(1.5) == 1.5
        assert sanitize_value(True) is True

    def test_strings_cleaned(self):
        assert sanitize_value('<b>x</b>') == 'x'


class TestSanitizeGalleryData:
    def test_dicts_sanitized(self):
        result = sanitize_gallery_data([{"k": '<script>x</script>'}])
        assert result == [{"k": 'x'}]

    def test_non_list_returns_empty(self):
        assert sanitize_gallery_data("foo") == []
        assert sanitize_gallery_data(None) == []
        assert sanitize_gallery_data({"a": 1}) == []

    def test_list_truncated(self):
        result = sanitize_gallery_data([list(range(100))])
        assert len(result[0]) == 50


class TestValidateFilename:
    def test_valid_extensions(self):
        assert validate_filename('fichier.csv') == 'fichier.csv'
        assert validate_filename('data.geojson') == 'data.geojson'

    def test_invalid_extension(self):
        assert validate_filename('fichier.exe') is None
        assert validate_filename('fichier.php') is None

    def test_no_extension(self):
        assert validate_filename('fichier') is None

    def test_path_traversal_sanitized(self):
        result = validate_filename('../../etc/passwd.png')
        assert result is not None
        # Les séparateurs de chemin sont remplacés : plus de '/' ni '\\'.
        assert '/' not in result
        assert '\\' not in result

    def test_non_string(self):
        assert validate_filename(None) is None
        assert validate_filename(123) is None


class TestPasswordStrength:
    def test_strong_password(self):
        ok, errors = validate_password_strength('Str0ng@Pass1!')
        assert ok is True
        assert errors == []

    def test_weak_password(self):
        ok, errors = validate_password_strength('short')
        assert ok is False
        assert len(errors) >= 1

    def test_missing_uppercase(self):
        ok, _ = validate_password_strength('alllower1!')
        assert ok is False

    def test_missing_special(self):
        ok, _ = validate_password_strength('NoSpecial1')
        assert ok is False


class TestPageNumbers:
    def test_small_total(self):
        assert _build_page_numbers(1, 5) == [1, 2, 3, 4, 5]

    def test_large_total_first_page(self):
        pages = _build_page_numbers(1, 20)
        assert pages[0] == 1
        assert pages[-1] == 20

    def test_large_total_last_page(self):
        pages = _build_page_numbers(20, 20)
        assert pages[0] == 1
        assert pages[-1] == 20

    def test_middle_page(self):
        pages = _build_page_numbers(10, 20)
        assert 1 in pages and 20 in pages
        assert 10 in pages