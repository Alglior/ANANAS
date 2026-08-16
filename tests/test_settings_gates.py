"""Tests des paramètres de porte : enable_registration et maintenance_mode."""
import pytest

from app import db
from models import SiteSetting


def _set_setting(key, value):
    row = SiteSetting.query.filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.session.add(SiteSetting(key=key, value=value))
    db.session.commit()


class TestRegistrationGate:
    def test_registration_enabled_by_default(self, client):
        resp = client.get("/inscription")
        assert resp.status_code == 200
        resp = client.post(
            "/inscription",
            data={"prenom": "Gate", "nom": "Test", "password": "C0mpl3x@Pass!"},
        )
        assert resp.status_code == 302
        assert "/connexion" in resp.headers["Location"]

    def test_registration_disabled_redirects_get(self, client):
        _set_setting("enable_registration", "false")
        resp = client.get("/inscription")
        assert resp.status_code == 302
        assert "/connexion" in resp.headers["Location"]

    def test_registration_disabled_blocks_post(self, client):
        _set_setting("enable_registration", "false")
        from models import User
        before = User.query.count()
        resp = client.post(
            "/inscription",
            data={"prenom": "Gate", "nom": "Closed", "password": "C0mpl3x@Pass!"},
        )
        assert resp.status_code == 403
        assert User.query.count() == before


class TestMaintenanceGate:
    def test_maintenance_blocks_anonymous(self, client):
        _set_setting("maintenance_mode", "true")
        resp = client.get("/")
        assert resp.status_code == 503
        assert b"Maintenance" in resp.data

    def test_maintenance_allows_admin(self, admin_client):
        _set_setting("maintenance_mode", "true")
        resp = admin_client.get("/")
        assert resp.status_code == 200

    def test_maintenance_allows_standard_user(self, user_client):
        _set_setting("maintenance_mode", "true")
        resp = user_client.get("/")
        assert resp.status_code == 503

    def test_maintenance_off_serves_site(self, client):
        _set_setting("maintenance_mode", "false")
        resp = client.get("/")
        assert resp.status_code == 200

    def test_maintenance_exempts_health_and_static(self, client):
        _set_setting("maintenance_mode", "true")
        assert client.get("/health").status_code == 200
        assert client.get("/static/js/main.js").status_code == 200
        assert client.get("/logout").status_code == 302