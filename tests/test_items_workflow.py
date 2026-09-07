"""Tests du workflow des items : upload, brouillons, corbeille, restauration,
purge, liens de visualisation, upload de fichier."""
import io

from models import Item, DataChunk, VisualizationLink


class TestUploadItem:
    def _create(self, client, **overrides):
        payload = {
            "title": "Mon jeu de données",
            "type": "geodonnee",
            "format_type": "csv",
            "description": "Description du jeu de données",
            "data_format_level": "simple",
            "magnet_link": "magnet:?xt=urn:btih:abc12345",
        }
        payload.update(overrides)
        return client.post("/api/upload/item", json=payload)

    def test_create_item(self, user_client):
        resp = self._create(user_client)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "created"
        item = Item.query.get(data["id"])
        assert item is not None
        assert item.owner_user_id is not None
        assert item.imod_score is not None

    def test_create_item_requires_title(self, user_client):
        resp = self._create(user_client, title="")
        assert resp.status_code == 400

    def test_create_item_invalid_type(self, user_client):
        resp = self._create(user_client, type="<script>x</script>")
        assert resp.status_code == 400

    def test_create_item_invalid_magnet(self, user_client):
        resp = self._create(user_client, data_format_level="simple", magnet_link="javascript:alert(1)")
        assert resp.status_code == 400

    def test_create_item_pack_with_zoom(self, user_client):
        resp = self._create(
            user_client,
            data_format_level="pack",
            magnet_link="magnet:?xt=urn:btih:pack1234",
            zoom_levels=["communes", "regions"],
        )
        assert resp.status_code == 200

    def test_update_item(self, user_client):
        created = self._create(user_client).get_json()
        item_id = created["id"]
        resp = user_client.put(
            f"/api/upload/item/{item_id}",
            json={"title": "Titre modifié", "description": "Nouvelle description"},
        )
        assert resp.status_code == 200
        assert Item.query.get(item_id).title == "Titre modifié"

    def test_update_foreign_item_forbidden(self, user_client, seeded):
        # item appartenant au seeder
        from models import Item as I
        foreign = I(
            type="geodonnee", title="Item seeder", description="d",
            magnet_link="magnet:?xt=urn:btih:foreign",
            owner_user_id=seeded["seeder"].id, status="draft",
        )
        from app import db
        db.session.add(foreign)
        db.session.commit()
        resp = user_client.put(
            f"/api/upload/item/{foreign.id}", json={"title": "hack"}
        )
        assert resp.status_code == 403


class TestDraftLifecycle:
    def _draft(self, client):
        resp = client.post(
            "/api/upload/item",
            json={"title": "Brouillon", "type": "geodonnee", "status": "draft"},
        )
        return resp.get_json()["id"]

    def test_delete_sets_trashed(self, user_client):
        item_id = self._draft(user_client)
        resp = user_client.delete(f"/api/upload/item/{item_id}")
        assert resp.status_code == 200
        item = Item.query.get(item_id)
        assert item.status == "trashed"
        assert item.deleted_at is not None

    def test_restore_trashed(self, user_client):
        item_id = self._draft(user_client)
        user_client.delete(f"/api/upload/item/{item_id}")
        resp = user_client.post(f"/api/upload/item/{item_id}/restore")
        assert resp.status_code == 200
        assert Item.query.get(item_id).status == "draft"

    def test_purge_trashed(self, user_client):
        item_id = self._draft(user_client)
        user_client.delete(f"/api/upload/item/{item_id}")
        resp = user_client.delete(f"/api/upload/item/{item_id}/purge")
        assert resp.status_code == 200
        assert Item.query.get(item_id) is None

    def test_purge_non_trashed_forbidden(self, user_client):
        item_id = self._draft(user_client)
        resp = user_client.delete(f"/api/upload/item/{item_id}/purge")
        assert resp.status_code == 403

    def test_list_drafts(self, user_client):
        self._draft(user_client)
        resp = user_client.get("/api/upload/drafts")
        data = resp.get_json()
        assert data["total_items"] >= 1

    def test_list_trash(self, user_client):
        item_id = self._draft(user_client)
        user_client.delete(f"/api/upload/item/{item_id}")
        resp = user_client.get("/api/upload/trash")
        assert resp.get_json()["total_items"] >= 1

    def test_list_publications(self, user_client):
        self._create_publication(user_client)
        resp = user_client.get("/api/upload/publications")
        assert resp.get_json()["total_items"] >= 1

    def _create_publication(self, client):
        return client.post(
            "/api/upload/item",
            json={"title": "Publication", "type": "geodonnee", "status": "published"},
        ).get_json()["id"]


class TestVisualizationLinks:
    def _owned_item(self, user_id):
        from app import db
        from models import Item
        item = Item(type="geodonnee", title="Viz", description="d",
                    magnet_link="magnet:?xt=urn:btih:viz123", owner_user_id=user_id)
        db.session.add(item)
        db.session.commit()
        return item.id

    def test_add_viz_link(self, user_client, seeded):
        item_id = self._owned_item(seeded["user"].id)
        resp = user_client.post(
            f"/api/items/{item_id}/viz-links",
            json={"name": "Carte", "url": "https://maps.example.com/view", "link_type": "external"},
        )
        assert resp.status_code == 200
        assert VisualizationLink.query.filter_by(parent_item_id=item_id).count() == 1

    def test_add_viz_link_invalid_url(self, user_client, seeded):
        item_id = self._owned_item(seeded["user"].id)
        resp = user_client.post(
            f"/api/items/{item_id}/viz-links",
            json={"name": "Bad", "url": "javascript:alert(1)", "link_type": "external"},
        )
        assert resp.status_code == 400

    def test_add_viz_link_foreign_item_forbidden(self, user_client, seeded):
        from app import db
        from models import Item
        item = Item(type="geodonnee", title="Foreign", description="d",
                    magnet_link="magnet:?xt=urn:btih:foreign", owner_user_id=seeded["seeder"].id)
        db.session.add(item)
        db.session.commit()
        resp = user_client.post(
            f"/api/items/{item.id}/viz-links",
            json={"name": "Carte", "url": "https://maps.example.com/view", "link_type": "external"},
        )
        assert resp.status_code == 403


class TestUploadFile:
    def test_upload_file_creates_chunk(self, user_client):
        resp = user_client.post(
            "/api/upload/file",
            data={
                "title": "Mon fichier",
                "type": "geodonnee",
                "format_type": "csv",
                "data_text": "col1,col2\n1,2\n3,4",
            },
        )
        assert resp.status_code == 200
        assert DataChunk.query.filter_by(name="Mon fichier").count() >= 1

    def test_upload_file_requires_title(self, user_client):
        resp = user_client.post("/api/upload/file", data={"title": ""})
        assert resp.status_code == 400


class TestImageStatus:
    def test_image_status(self, user_client, seeded):
        from app import db
        item = Item(type="geodonnee", title="Img", description="d",
                    magnet_link="magnet:?xt=urn:btih:imgstatus")
        db.session.add(item)
        db.session.commit()
        resp = user_client.get(f"/api/items/{item.id}/image-status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pending" in data and "total" in data and "current" in data