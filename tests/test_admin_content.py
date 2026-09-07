"""Tests CRUD des contenus administrés : tags, miroirs, mis en avant,
geopackages, fichiers simples, changelog, messages de contact, catalogues,
audit, paramètres et sauvegarde."""
import gzip
import io

from models import (PredefinedTag, PredefinedTagCategory, MirrorSite, FeaturedItem,
                    GeoPackage, SimpleFileItem, ChangelogVersion, ContactMessage)


class TestTags:
    def _category(self, admin_client):
        resp = admin_client.post("/api/admin/tags", json={"name": "Thème"})
        return resp.get_json()["category"]["id"]

    def test_create_category(self, admin_client):
        resp = admin_client.post("/api/admin/tags", json={"name": "Environnement"})
        assert resp.status_code == 200
        assert resp.get_json()["category"]["name"] == "Environnement"

    def test_create_duplicate_category(self, admin_client):
        admin_client.post("/api/admin/tags", json={"name": "Doublon"})
        resp = admin_client.post("/api/admin/tags", json={"name": "Doublon"})
        assert resp.status_code == 400

    def test_list_categories(self, admin_client):
        admin_client.post("/api/admin/tags", json={"name": "ListeCat"})
        resp = admin_client.get("/api/admin/tags")
        assert any(c["name"] == "ListeCat" for c in resp.get_json()["categories"])

    def test_update_category(self, admin_client):
        cid = self._category(admin_client)
        resp = admin_client.put(f"/api/admin/tags/{cid}", json={"name": "Renommé"})
        assert resp.status_code == 200
        assert PredefinedTagCategory.query.get(cid).name == "Renommé"

    def test_create_tag(self, admin_client):
        cid = self._category(admin_client)
        resp = admin_client.post(f"/api/admin/tags/{cid}/tags", json={"name": "zone"})
        assert resp.status_code == 200
        assert PredefinedTag.query.filter_by(category_id=cid, name="zone").first()

    def test_create_duplicate_tag(self, admin_client):
        cid = self._category(admin_client)
        admin_client.post(f"/api/admin/tags/{cid}/tags", json={"name": "zone"})
        resp = admin_client.post(f"/api/admin/tags/{cid}/tags", json={"name": "zone"})
        assert resp.status_code == 400

    def test_update_tag(self, admin_client):
        cid = self._category(admin_client)
        tag_id = admin_client.post(
            f"/api/admin/tags/{cid}/tags", json={"name": "zone"}
        ).get_json()["tag"]["id"]
        resp = admin_client.put(
            f"/api/admin/tags/{cid}/tags/{tag_id}", json={"name": "zone2"}
        )
        assert resp.status_code == 200
        assert PredefinedTag.query.get(tag_id).name == "zone2"

    def test_delete_tag(self, admin_client):
        cid = self._category(admin_client)
        tag_id = admin_client.post(
            f"/api/admin/tags/{cid}/tags", json={"name": "suppr"}
        ).get_json()["tag"]["id"]
        resp = admin_client.delete(f"/api/admin/tags/{cid}/tags/{tag_id}")
        assert resp.status_code == 200
        assert PredefinedTag.query.get(tag_id) is None

    def test_delete_category(self, admin_client):
        cid = self._category(admin_client)
        resp = admin_client.delete(f"/api/admin/tags/{cid}")
        assert resp.status_code == 200
        assert PredefinedTagCategory.query.get(cid) is None


class TestMirrors:
    _payload = {"name": "Miroir A", "url": "https://mirror.example.org", "description": "Un miroir"}

    def test_create_mirror(self, admin_client):
        resp = admin_client.post("/api/admin/mirrors", json=self._payload)
        assert resp.status_code == 200
        assert MirrorSite.query.filter_by(name="Miroir A").first()

    def test_create_mirror_invalid_url(self, admin_client):
        resp = admin_client.post(
            "/api/admin/mirrors", json={**self._payload, "url": "javascript:x"}
        )
        assert resp.status_code == 400

    def test_create_mirror_missing_fields(self, admin_client):
        resp = admin_client.post("/api/admin/mirrors", json={"name": "Solo"})
        assert resp.status_code == 400

    def test_list_mirrors(self, admin_client):
        admin_client.post("/api/admin/mirrors", json=self._payload)
        resp = admin_client.get("/api/admin/mirrors")
        assert any(m["name"] == "Miroir A" for m in resp.get_json()["mirrors"])

    def test_update_mirror(self, admin_client):
        mid = admin_client.post("/api/admin/mirrors", json=self._payload).get_json()["mirror"]["id"]
        resp = admin_client.put(f"/api/admin/mirrors/{mid}", json={"is_active": False})
        assert resp.status_code == 200
        assert MirrorSite.query.get(mid).is_active is False

    def test_delete_mirror(self, admin_client):
        mid = admin_client.post("/api/admin/mirrors", json=self._payload).get_json()["mirror"]["id"]
        resp = admin_client.delete(f"/api/admin/mirrors/{mid}")
        assert resp.status_code == 200
        assert MirrorSite.query.get(mid) is None


class TestFeatured:
    def test_create_featured(self, admin_client):
        resp = admin_client.post("/api/admin/featured", json={"item_id": 1})
        assert resp.status_code == 200
        assert FeaturedItem.query.filter_by(item_id=1).first()

    def test_create_featured_duplicate(self, admin_client):
        admin_client.post("/api/admin/featured", json={"item_id": 1})
        resp = admin_client.post("/api/admin/featured", json={"item_id": 1})
        assert resp.status_code == 409

    def test_create_featured_item_not_found(self, admin_client):
        resp = admin_client.post("/api/admin/featured", json={"item_id": 99999})
        assert resp.status_code == 404

    def test_search_items(self, admin_client):
        resp = admin_client.get("/api/admin/items/search?q=Item%201")
        assert resp.status_code == 200
        assert resp.get_json()["items"]

    def test_list_featured(self, admin_client):
        admin_client.post("/api/admin/featured", json={"item_id": 1})
        resp = admin_client.get("/api/admin/featured")
        assert resp.get_json()["featured"]

    def test_delete_featured(self, admin_client):
        fid = admin_client.post("/api/admin/featured", json={"item_id": 1}).get_json()["featured"]["id"]
        resp = admin_client.delete(f"/api/admin/featured/{fid}")
        assert resp.status_code == 200
        assert FeaturedItem.query.get(fid) is None


class TestGeoPackages:
    _payload = {"title": "Pack", "description": "Descr", "format_info": "gpkg",
                "link_url": "https://files.example.org/pack.gpkg"}

    def test_create_geopackage(self, admin_client):
        resp = admin_client.post("/api/admin/geopackages", json=self._payload)
        assert resp.status_code == 200
        assert GeoPackage.query.filter_by(title="Pack").first()

    def test_create_geopackage_invalid_url(self, admin_client):
        resp = admin_client.post(
            "/api/admin/geopackages", json={**self._payload, "link_url": "ftp://bad"}
        )
        assert resp.status_code == 400

    def test_list_geopackages(self, admin_client):
        admin_client.post("/api/admin/geopackages", json=self._payload)
        resp = admin_client.get("/api/admin/geopackages")
        assert any(p["title"] == "Pack" for p in resp.get_json()["packages"])

    def test_update_geopackage(self, admin_client):
        pid = admin_client.post("/api/admin/geopackages", json=self._payload).get_json()["package"]["id"]
        resp = admin_client.put(f"/api/admin/geopackages/{pid}", json={"title": "Pack2"})
        assert resp.status_code == 200
        assert GeoPackage.query.get(pid).title == "Pack2"

    def test_delete_geopackage(self, admin_client):
        pid = admin_client.post("/api/admin/geopackages", json=self._payload).get_json()["package"]["id"]
        resp = admin_client.delete(f"/api/admin/geopackages/{pid}")
        assert resp.status_code == 200
        assert GeoPackage.query.get(pid) is None


class TestSimpleFiles:
    def test_create_simple_file(self, admin_client):
        resp = admin_client.post("/api/admin/simple-files", json={"item_id": 1})
        assert resp.status_code == 200
        assert SimpleFileItem.query.filter_by(item_id=1).first()

    def test_create_simple_file_duplicate(self, admin_client):
        admin_client.post("/api/admin/simple-files", json={"item_id": 1})
        resp = admin_client.post("/api/admin/simple-files", json={"item_id": 1})
        assert resp.status_code == 409

    def test_list_simple_files(self, admin_client):
        admin_client.post("/api/admin/simple-files", json={"item_id": 1})
        resp = admin_client.get("/api/admin/simple-files")
        assert resp.get_json()["simple_files"]

    def test_delete_simple_file(self, admin_client):
        sfid = admin_client.post("/api/admin/simple-files", json={"item_id": 1}).get_json()["simple_file"]["id"]
        resp = admin_client.delete(f"/api/admin/simple-files/{sfid}")
        assert resp.status_code == 200
        assert SimpleFileItem.query.get(sfid) is None


class TestChangelog:
    _payload = {"version": "1.2.3", "sections": [{"title": "Nouveautés", "items": ["Ajout X"]}]}

    def test_create_version(self, admin_client):
        resp = admin_client.post("/api/admin/changelog", json=self._payload)
        assert resp.status_code == 200
        assert ChangelogVersion.query.filter_by(version="1.2.3").first()

    def test_create_version_requires_version(self, admin_client):
        resp = admin_client.post("/api/admin/changelog", json={})
        assert resp.status_code == 400

    def test_list_versions(self, admin_client):
        admin_client.post("/api/admin/changelog", json=self._payload)
        resp = admin_client.get("/api/admin/changelog")
        assert any(v["version"] == "1.2.3" for v in resp.get_json()["versions"])

    def test_update_version(self, admin_client):
        vid = admin_client.post("/api/admin/changelog", json=self._payload).get_json()["version"]["id"]
        resp = admin_client.put(f"/api/admin/changelog/{vid}", json={"version": "1.2.4"})
        assert resp.status_code == 200
        assert ChangelogVersion.query.get(vid).version == "1.2.4"

    def test_delete_version(self, admin_client):
        vid = admin_client.post("/api/admin/changelog", json=self._payload).get_json()["version"]["id"]
        resp = admin_client.delete(f"/api/admin/changelog/{vid}")
        assert resp.status_code == 200
        assert ChangelogVersion.query.get(vid) is None


class TestContactMessages:
    def _send(self, client):
        client.post("/api/contact", data={
            "name": "Claude", "email": "claude@example.com",
            "subject": "Question", "message": "Bonjour le site",
        })

    def test_list_contact_messages(self, admin_client, client):
        self._send(client)
        resp = admin_client.get("/api/admin/contact-messages")
        assert resp.status_code == 200
        assert resp.get_json()["messages"]

    def test_mark_read(self, admin_client, client):
        self._send(client)
        msg = ContactMessage.query.first()
        resp = admin_client.post(f"/api/admin/contact-messages/{msg.id}/read", json={"is_read": True})
        assert resp.status_code == 200
        assert ContactMessage.query.get(msg.id).is_read is True

    def test_delete_contact_message(self, admin_client, client):
        self._send(client)
        msg = ContactMessage.query.first()
        resp = admin_client.delete(f"/api/admin/contact-messages/{msg.id}")
        assert resp.status_code == 200
        assert ContactMessage.query.get(msg.id) is None


class TestCataloguesToggle:
    def test_toggle_catalogue(self, admin_client):
        resp = admin_client.post("/api/admin/catalogues/cartes/toggle", json={"active": True})
        assert resp.status_code == 200
        assert resp.get_json()["catalogue"] == "cartes"

    def test_toggle_invalid_catalogue(self, admin_client):
        resp = admin_client.post("/api/admin/catalogues/bogus/toggle", json={"active": True})
        assert resp.status_code == 400


class TestAudit:
    def test_audit_log(self, admin_client):
        admin_client.post("/api/admin/tags", json={"name": "AuditTag"})
        resp = admin_client.get("/api/admin/audit")
        assert resp.status_code == 200
        assert any(e["action_type"] == "tag_category_created" for e in resp.get_json()["entries"])


class TestSettings:
    def test_settings_page(self, admin_client):
        resp = admin_client.get("/admin/settings")
        assert resp.status_code == 200

    def test_update_settings(self, admin_client):
        resp = admin_client.post(
            "/api/admin/settings/update",
            json={"items_per_page": "15", "site_name": "ANANAS v2"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["settings"]["site_name"] == "ANANAS v2"

    def test_update_settings_rejects_unknown(self, admin_client):
        resp = admin_client.post(
            "/api/admin/settings/update", json={"malicious_key": "x"}
        )
        assert resp.status_code == 200
        assert "malicious_key" in resp.get_json()["rejected"]

    def test_logo_upload_invalid_format(self, admin_client):
        resp = admin_client.post(
            "/api/admin/settings/logo-upload",
            data={"logo": (io.BytesIO(b"data"), "logo.svg")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


class TestBackup:
    def test_download_backup(self, admin_client):
        resp = admin_client.get("/api/admin/backup/download")
        assert resp.status_code == 200
        assert resp.mimetype == "application/gzip"

    def test_restore_no_file(self, admin_client):
        resp = admin_client.post("/api/admin/backup/restore")
        assert resp.status_code == 400

    def test_restore_wrong_extension(self, admin_client):
        resp = admin_client.post(
            "/api/admin/backup/restore",
            data={"file": (io.BytesIO(b"data"), "backup.txt")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_restore_undecodable_gzip(self, admin_client):
        data = gzip.compress(b"CREATE TABLE items (id int);")
        resp = admin_client.post(
            "/api/admin/backup/restore",
            data={"file": (io.BytesIO(data), "backup.sql.gz")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 500)


class TestAdminAccessControl:
    def test_admin_api_requires_admin(self, user_client):
        resp = user_client.get("/api/admin/tags")
        assert resp.status_code == 403

    def test_admin_page_requires_login(self, client):
        resp = client.get("/admin/settings")
        assert resp.status_code == 302

    def test_admin_page_denies_non_admin(self, user_client):
        resp = user_client.get("/admin/settings")
        assert resp.status_code == 403