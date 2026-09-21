import os
import time

import pytest

from app import db


class TestRoutes:
    """Phase 7.1 — Vérifier chaque route."""

    def test_home_page_loads(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"A.N.A.N.A.S" in resp.data

    def test_contact_page_loads(self, client):
        resp = client.get("/contact")
        assert resp.status_code == 200
        assert b"Contact" in resp.data

    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"

    def test_catalogue_donnees_loads(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=1")
        assert resp.status_code == 200
        assert b"Item 1" in resp.data

    def test_catalogue_cartes_loads(self, client, seeded):
        resp = client.get("/catalogue/cartes?page=1")
        assert resp.status_code == 200
        assert b"Item 211" in resp.data

    def test_catalogue_applications_loads(self, client, seeded):
        resp = client.get("/catalogue/applications?page=1")
        assert resp.status_code == 200
        assert b"Item 261" in resp.data

    def test_item_detail_exists(self, client, seeded):
        resp = client.get("/catalogue/item/1")
        assert resp.status_code == 200
        assert b"Item 1" in resp.data

    def test_item_detail_not_found_redirects(self, client, seeded):
        resp = client.get("/catalogue/item/99999")
        assert resp.status_code in (302, 404)

    def test_gallery_page_loads(self, client, seeded):
        resp = client.get("/catalogue/item/1/gallery")
        assert resp.status_code == 200

    def test_favicon_returns_204(self, client):
        resp = client.get("/favicon.ico")
        assert resp.status_code == 204

    def test_connexion_page_loads(self, client):
        resp = client.get("/connexion")
        assert resp.status_code == 200

    def test_inscription_page_loads(self, client):
        resp = client.get("/inscription")
        assert resp.status_code == 200


class TestPagination:
    """Phase 7.2 — Vérifier la pagination."""

    def test_page_1_items_range(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=1&format=json")
        data = resp.get_json()
        assert data is not None
        items = data["items"]
        assert len(items) == 30
        ids = [item["id"] for item in items]
        # Le catalogue est trié par score iMod (pas par id) : vérifier la taille
        # de page et que les ids sont valides et distincts.
        assert all(1 <= i <= 210 for i in ids)
        assert len(set(ids)) == 30

    def test_page_7_donnees(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=7&format=json")
        data = resp.get_json()
        assert data is not None
        assert data["page"] == 7
        assert data["total_pages"] == 7
        items = data["items"]
        ids = [item["id"] for item in items]
        assert all(1 <= i <= 210 for i in ids)

    def test_page_overflow_redirects(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=999")
        assert resp.status_code == 302

    def test_total_items_count(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=1&format=json")
        data = resp.get_json()
        assert data["total_items"] == 210

    def test_page_numbers_logic(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=4&format=json")
        data = resp.get_json()
        assert len(data["page_numbers"]) == 7

    def test_cartes_pagination_total(self, client, seeded):
        resp = client.get("/catalogue/cartes?page=1&format=json")
        data = resp.get_json()
        assert data["total_items"] == 50

    def test_apps_pagination_total(self, client, seeded):
        resp = client.get("/catalogue/applications?page=1&format=json")
        data = resp.get_json()
        assert data["total_items"] == 20


class TestFilters:
    """Phase 7.3 — Vérifier les filtres."""

    def test_filter_verified(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=1&verified=1&format=json")
        data = resp.get_json()
        for item in data["items"]:
            assert item["verification_status"] == "verified"

    def test_org_filter(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=1&org=org-test&format=json")
        data = resp.get_json()
        for item in data["items"]:
            assert item["organization_name"] == "Org Test"

    def test_pagination_preserves_filters(self, client, seeded):
        resp = client.get("/catalogue/donnees?verified=1&format_level=simple")
        html = resp.get_data(as_text=True)
        expected = 'href="/catalogue/donnees/2?verified=1&amp;format_level=simple"'
        assert expected in html
        assert 'href="/catalogue/donnees/3?verified=1&amp;format_level=simple"' in html

    def test_page_overflow_redirect_preserves_filters(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=999&verified=1&format_level=simple")
        assert resp.status_code == 302
        assert "/catalogue/donnees?page=3&verified=1&format_level=simple" in resp.headers["Location"]


class TestResumeImageDownloads:
    """Vérifie la reprise des téléchargements d'images interrompus."""

    def test_list_unfinished_items(self, client, seeded):
        from models import Item, ItemImageJob
        from src.user_routes import list_unfinished_image_items

        item = Item.query.filter_by(title="Item 1").first()
        for i, st in enumerate(("done", "downloading", "saving", "pending", "failed")):
            db.session.add(ItemImageJob(
                item_id=item.id, idx=i,
                magnet_link=f"magnet:?xt=urn:btih:{i:040x}",
                label="Image", status=st,
            ))
        db.session.commit()

        result = dict(list_unfinished_image_items())
        assert item.id in result
        magnets = result[item.id]
        assert len(magnets) == 4  # downloading + saving + pending + failed
        assert "magnet:?xt=urn:btih:0" not in magnets

    def test_list_skips_items_without_magnets(self, client, seeded):
        from models import Item, ItemImageJob
        from src.user_routes import list_unfinished_image_items

        item = Item.query.filter_by(title="Item 1").first()
        db.session.add(ItemImageJob(item_id=item.id, idx=0, magnet_link="", label="Image", status="downloading"))
        other = Item.query.filter_by(title="Item 2").first()
        db.session.add(ItemImageJob(item_id=other.id, idx=0, magnet_link="magnet:?xt=urn:btih:aabbccddeeff00112233445566778899aabbccdd", label="Image", status="failed"))
        db.session.commit()

        result = dict(list_unfinished_image_items())
        assert item.id not in result
        assert other.id in result

    def test_list_recovers_from_item_when_flag_stuck(self, client, seeded):
        from models import Item, ItemGallery
        from src.user_routes import list_unfinished_image_items

        item = Item.query.filter_by(title="Item 1").first()
        # Item affiché "en cours" (flag) mais sans jobs non terminés
        # (crash avant création des jobs) : magnets récupérés depuis l'item.
        item.image_magnets_pending = True
        item.image_magnets_total = 2
        item.image_magnet_links = [
            {"magnet_link": "magnet:?xt=urn:btih:aabbccddeeff00112233445566778899aabbccdd", "label": "Image"},
            {"magnet_link": "magnet:?xt=urn:btih:aabbccddeeff00112233445566778899aabbccee", "label": "Image"},
        ]
        db.session.commit()

        result = dict(list_unfinished_image_items())
        assert item.id in result
        assert len(result[item.id]) == 2

    def test_relaunch_cleans_stuck_flag(self, client, seeded):
        from models import Item, ItemImageJob
        from src.user_routes import relaunch_unfinished_image_jobs

        stuck = Item.query.filter_by(title="Item 1").first()
        # Aucun magnet récupérable (ni jobs ni image_magnet_links) : le flag
        # "en cours" ne peut plus aboutir, il doit être levé.
        stuck.image_magnets_pending = True
        stuck.image_magnets_total = 0
        stuck.image_magnet_links = []
        ItemImageJob.query.filter_by(item_id=stuck.id).delete()
        ok = Item.query.filter_by(title="Item 2").first()
        db.session.add(ItemImageJob(
            item_id=ok.id, idx=0,
            magnet_link="magnet:?xt=urn:btih:aabbccddeeff00112233445566778899aabbccdd",
            label="Image", status="downloading",
        ))
        db.session.commit()

        relaunched, cleaned = relaunch_unfinished_image_jobs()
        assert relaunched >= 1
        assert cleaned == 1
        db.session.refresh(stuck)
        assert stuck.image_magnets_pending is False


class TestImageCachePurge:
    """Vérifie la purge du cache d'images expiré (TTL 30 jours)."""

    def _touch(self, path, age_seconds):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        os.utime(path, (time.time() - age_seconds, time.time() - age_seconds))

    def test_purges_expired_unreferenced(self, client, seeded, tmp_path, monkeypatch):
        from src import image_cache

        monkeypatch.setattr(image_cache, "CACHE_DIR", tmp_path)

        old = tmp_path / "deadbeef"
        self._touch(old, 40 * 86400)
        recent = tmp_path / "cafebabe"
        self._touch(recent, 5 * 86400)

        assert image_cache.purge_expired_cache() == 1
        assert not old.exists()
        assert recent.exists()

    def test_keeps_expired_referenced(self, client, seeded, tmp_path, monkeypatch):
        from src import image_cache
        from models import Item

        monkeypatch.setattr(image_cache, "CACHE_DIR", tmp_path)

        entry = tmp_path / "baadf00d"
        self._touch(entry, 40 * 86400)
        item = Item.query.filter_by(title="Item 1").first()
        item.image_path = "/static/cache/img/baadf00d.png"
        db.session.commit()

        assert image_cache.purge_expired_cache() == 0
        assert entry.exists()


class TestAuthRoutes:
    """Phase 7.4 — Vérifier les routes d'authentification."""

    def test_inscription_creates_user(self, client):
        resp = client.post(
            "/inscription",
            data={"prenom": "New", "nom": "User", "password": "Str0ng@Pass1!"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        from models import User
        created = User.query.filter(User.pseudo.like("new-user#%")).first()
        assert created is not None
        assert created.prenom == "New"
        assert created.nom == "User"

    def test_inscription_without_email(self, client):
        resp = client.post(
            "/inscription",
            data={"prenom": "Dup", "nom": "User", "password": "Test@Secure1"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        from models import User
        created = User.query.filter(User.pseudo.like("dup-user#%")).first()
        assert created is not None

    def test_logout(self, client):
        resp = client.get("/logout")
        assert resp.status_code == 302


class TestAPIEndpoints:
    """Phase 7.5 — Vérifier les endpoints API."""

    def test_health_json_format(self, client):
        resp = client.get("/health")
        data = resp.get_json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_rating_endpoint_post(self, client, seeded):
        resp = client.post("/catalogue/item/1/rate", data={"rating": "5"})
        assert resp.status_code in (302, 200)

    def test_upload_item_rejects_invalid_type(self, client, seeded):
        with client.session_transaction() as sess:
            sess["user_id"] = seeded["user"].id
            sess["session_version"] = seeded["user"].session_version

        resp = client.post(
            "/api/upload/item",
            json={
                "title": "Test item",
                "type": "<img src=x onerror=alert(1)>",
                "format_type": "csv",
                "description": "desc",
                "data_format_level": "pack",
            },
        )
        assert resp.status_code == 400

    def test_upload_item_accepts_valid_type(self, client, seeded):
        with client.session_transaction() as sess:
            sess["user_id"] = seeded["user"].id
            sess["session_version"] = seeded["user"].session_version

        resp = client.post(
            "/api/upload/item",
            json={
                "title": "Test item ok",
                "type": "geodonnee",
                "format_type": "csv",
                "description": "desc",
                "data_format_level": "pack",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data and data.get("status") == "created"

    def test_upload_item_accepts_simple_level(self, client, seeded):
        with client.session_transaction() as sess:
            sess["user_id"] = seeded["user"].id
            sess["session_version"] = seeded["user"].session_version

        resp = client.post(
            "/api/upload/item",
            json={
                "title": "Test item simple",
                "type": "geodonnee",
                "format_type": "csv",
                "description": "desc",
                "data_format_level": "simple",
                "magnet_link": "magnet:?xt=urn:btih:test123",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "created"


class TestOrganizationRoutes:
    """Phase 7.6 — Vérifier les routes organisation."""

    def test_org_not_found(self, client):
        resp = client.get("/organizations/nonexistent")
        assert resp.status_code == 404
