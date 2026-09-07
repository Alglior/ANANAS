"""Tests des pages statiques et de contenu : mentions légales, confidentialité,
CGU, à propos, changelog, documentation, API docs, contact et catalogue JSON."""
import os


class TestStaticPages:
    def test_apropos(self, client):
        resp = client.get("/apropos")
        assert resp.status_code == 200

    def test_mentions_legales(self, client):
        resp = client.get("/mentions-legales")
        assert resp.status_code == 200

    def test_confidentialite(self, client):
        resp = client.get("/confidentialite")
        assert resp.status_code == 200

    def test_conditions_utilisation(self, client):
        resp = client.get("/conditions-utilisation")
        assert resp.status_code == 200

    def test_changelog_page(self, client):
        resp = client.get("/changelog")
        assert resp.status_code == 200

    def test_api_docs(self, client):
        resp = client.get("/api")
        assert resp.status_code == 200

    def test_docs_index(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_docs_view(self, client):
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_docs_site")
        files = [f for f in os.listdir(docs_dir) if f.endswith(".md")] if os.path.isdir(docs_dir) else []
        if not files:
            return  # aucune doc disponible : on skip silencieusement
        import re
        slug = re.sub(r"[^a-z0-9-]", "", files[0].replace(".md", "").lower().replace("_", "-"))
        resp = client.get(f"/docs/{slug}")
        assert resp.status_code == 200


class TestContact:
    def test_contact_submit(self, client):
        resp = client.post("/api/contact", data={
            "name": "Jean", "email": "jean@example.com",
            "subject": "Salut", "message": "Un message",
        })
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "sent"

    def test_contact_submit_missing_fields(self, client):
        resp = client.post("/api/contact", data={"name": "Jean"})
        assert resp.status_code == 400

    def test_contact_submit_invalid_email(self, client):
        resp = client.post("/api/contact", data={
            "name": "Jean", "email": "pas-un-email",
            "subject": "S", "message": "M",
        })
        assert resp.status_code == 400

    def test_contact_submit_sanitizes(self, client):
        client.post("/api/contact", data={
            "name": '<script>x</script>', "email": "a@b.com",
            "subject": "S", "message": '<b>ok</b>',
        })
        from models import ContactMessage
        m = ContactMessage.query.order_by(ContactMessage.id.desc()).first()
        assert "<script>" not in m.name
        assert "<b>" not in m.message


class TestCatalogueJSON:
    def test_json_endpoint(self, client, seeded):
        resp = client.get("/catalogue/donnees/1/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data and "total_pages" in data

    def test_catalogue_legacy_root(self, client):
        resp = client.get("/catalogue")
        assert resp.status_code == 200

    def test_catalogue_unknown_type(self, client):
        # Type invalide => redirection vers le catalogue par défaut.
        resp = client.get("/catalogue/bogus")
        assert resp.status_code == 302
        resp = client.get("/catalogue/bogus", follow_redirects=True)
        assert resp.status_code == 200

    def test_catalogue_imod_sort(self, client, seeded):
        resp = client.get("/catalogue/donnees?page=1&imod=high&format=json")
        data = resp.get_json()
        scores = [it["imod"]["score"] for it in data["items"]]
        assert scores == sorted(scores, reverse=True)

    def test_catalogue_search(self, client, seeded):
        resp = client.get("/catalogue/donnees?q=Item%201&format=json")
        data = resp.get_json()
        assert data["total_items"] >= 1

    def test_catalogue_tag_filter(self, client, seeded):
        from app import db
        from models import ItemTag
        db.session.add(ItemTag(item_id=1, tag="filtre-tag"))
        db.session.commit()
        resp = client.get("/catalogue/donnees?tag=filtre-tag&format=json")
        assert resp.get_json()["total_items"] >= 1


class TestDownloads:
    def test_magnets_download(self, client, seeded):
        resp = client.get("/catalogue/item/1/magnets/download")
        assert resp.status_code == 200
        assert "magnet" in resp.mimetype or resp.data.startswith(b"#")

    def test_favicon(self, client):
        resp = client.get("/favicon.ico")
        assert resp.status_code == 204

    def test_cached_image_404(self, client):
        resp = client.get("/static/cache/img/nonexistent")
        assert resp.status_code == 404