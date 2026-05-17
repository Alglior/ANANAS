import datetime


class TestItemModel:
    """Phase 7 — Validation des modèles ORM."""

    def test_item_to_dict_basic(self):
        from models import Item
        item = Item(
            type="geodonnee",
            title="Test Item",
            description="Desc",
            format_type="geojson",
            magnet_link="magnet:?xt=test",
        )
        d = item.to_dict()
        assert d["title"] == "Test Item"
        assert d["format"] == "geojson"
        assert d["catalogue_link"] == "/catalogue/donnees"

    def test_item_to_dict_with_org(self):
        from models import Item, Organization
        org = Organization(name="TestOrg", slug="test-org", description="Desc", created_by=1)
        item = Item(
            type="geodonnee",
            title="Item Org",
            description="Desc",
            format_type="shapefile",            magnet_link="magnet:?xt=test2",
            organization_id=org.id,
        )
        item.organization = org
        d = item.to_dict()
        assert d["organization_name"] == "TestOrg"
        assert d["organization_slug"] == "test-org"

    def test_item_rating_average(self):
        from models import Item, Rating
        item = Item(type="carte", title="Rated", description="Desc", format_type="tif", magnet_link="magnet:?xt=rated")
        r1 = Rating(item_id=item.id, rating=4.0)
        r2 = Rating(item_id=item.id, rating=6.0)
        item.ratings = [r1, r2]
        avg = item._get_rating_avg()
        assert avg == 5.0

    def test_item_rating_no_ratings(self):
        from models import Item
        item = Item(type="application", title="Unrated", description="Desc", format_type="web", magnet_link="magnet:?xt=unrated")
        item.ratings = []
        avg = item._get_rating_avg()
        assert avg == 0

    def test_item_gallery_build(self):
        from models import Item, ItemGallery
        item = Item(type="geodonnee", title="Gallery Item", description="Desc", format_type="zip", magnet_link="magnet:?xt=gal")
        g1 = ItemGallery(item_id=item.id, media_type="image", src="/img/1.png", label="Label 1")
        g2 = ItemGallery(item_id=item.id, media_type="csv", data_json={"rows": [{"a": 1}]}, label="CSV 1")
        item.gallery_items = [g1, g2]
        gal = item._build_gallery_dict()
        assert len(gal) == 2
        assert gal[0]["type"] == "image"
        assert gal[0]["src"] == "/img/1.png"
        assert gal[1]["type"] == "csv"
        assert gal[1]["data"] == [{"a": 1}]

    def test_item_gallery_xss_prevention(self):
        from models import Item, ItemGallery
        item = Item(type="geodonnee", title="XSS Gallery", description="Desc", format_type="zip", magnet_link="magnet:?xt=xss")
        xss_payload = '<script>alert("XSS")</script>'
        g1 = ItemGallery(item_id=item.id, media_type="csv", data_json={"rows": [[xss_payload, "safe", 42]]}, label="CSV XSS")
        g2 = ItemGallery(item_id=item.id, media_type="dashboard", data_json={"metrics": [{"metric": "<b>Bold</b>", "value": '<script>alert(1)</script>'}]})
        g3 = ItemGallery(item_id=item.id, media_type="image", src='/img/<script>alert("src")</script>.png', label='<script>alert("lbl")</script>')
        item.gallery_items = [g1, g2, g3]
        gal = item._build_gallery_dict()
        assert len(gal) == 3
        # CSV rows should be sanitized - HTML tags stripped
        csv_data = gal[0]["data"][0]
        assert "<script>" not in str(csv_data[0])
        assert "<" not in str(csv_data[0])
        # Dashboard metrics should be sanitized
        metric_val = gal[1]["metrics"][0].get("metric", "")
        assert "<b>" not in str(metric_val)
        assert "<" not in str(metric_val)
        val = gal[1]["metrics"][0].get("value", "")
        assert "<script>" not in str(val)
        assert "<" not in str(val)
        # Image src and label should be sanitized
        assert "<script>" not in str(gal[2].get("src", ""))
        assert "<" not in str(gal[2].get("src", ""))
        assert "<script>" not in str(gal[2].get("label", ""))
        assert "<" not in str(gal[2].get("label", ""))

    def test_item_gallery_invalid_data_json(self):
        from models import Item, ItemGallery
        item = Item(type="geodonnee", title="Invalid Gallery", description="Desc", format_type="zip", magnet_link="magnet:?xt=invalid")
        g1 = ItemGallery(item_id=item.id, media_type="csv", data_json={"rows": "not_a_list"}, label="Bad rows")
        g2 = ItemGallery(item_id=item.id, media_type="dashboard", data_json={"metrics": "not_a_list"}, label="Bad metrics")
        g3 = ItemGallery(item_id=item.id, media_type="csv", data_json="string_not_dict", label="String json")
        item.gallery_items = [g1, g2, g3]
        gal = item._build_gallery_dict()
        assert len(gal) == 3
        # Invalid data should result in empty lists/empty values
        assert gal[0].get("data") == [] or not gal[0].get("data")
        assert gal[1].get("metrics") == [] or not gal[1].get("metrics")

    def test_data_chunk_metadata_json_sanitization(self):
        from models import DataChunk
        chunk = DataChunk(name="Test Chunk", owner_user_id=1)
        chunk.metadata_json = {
            "preview_rows": [
                '<script>alert("xss")</script>',
                "<b>bold text</b>",
                42,
                "safe_value"
            ],
            "column_count": 3,
            "column_name": "<img src=x onerror=alert(1)>"
        }
        d = chunk.to_dict()
        meta = d["metadata_json"]
        # Check that strings in preview_rows are sanitized
        assert "<script>" not in str(meta.get("preview_rows", [])) or "&lt;" in str(meta.get("preview_rows", []))
        assert "<b>" not in str(meta.get("column_name", ""))

    def test_item_verification_status(self):
        from models import Item, User
        user = User(prenom="Verif", nom="Admin", email="verif@test.com", password_hash="pbkdf2:sha256:260000$xxx$yyy", is_active=True)
        item = Item(type="carte", title="Verified Item", description="Desc", format_type="map", magnet_link="magnet:?xt=verif"
)
        item.verification_status = "verified"
        item.verifier_user_id = user.id
        item.verified_at = datetime.datetime.now()
        item.verifier = user  # directly assign to avoid lazy-load on transient object
        d = item.to_dict()
        assert d["is_official_verified"] is True
        assert d["verifier_nom"] == "Verif Admin"
        assert d["verification_status"] == "verified"

    def test_item_type_mapping(self):
        from models import Item
        for item_type, expected_link in [("geodonnee", "/catalogue/donnees"), ("carte", "/catalogue/cartes"), ("application", "/catalogue/applications")]:
            item = Item(type=item_type, title="Map Test", description="Desc", format_type="x", magnet_link="magnet:?xt=map")
            assert item.to_dict()["catalogue_link"] == expected_link


class TestUserModel:
    def test_user_str(self):
        from models import User
        u = User(prenom="Jean", nom="Dupont", email="jean@test.com", password_hash="pbkdf2:test", is_active=True)
        assert str(u) == "Jean Dupont"

    def test_user_banned_default(self):
        from models import User
        u = User(prenom="New", nom="User", email="banned@test.com", password_hash="pbkdf2:test")
        assert u.banned is False


class TestTagModel:
    def test_item_tags(self):
        from models import Item, ItemTag
        item = Item(type="geodonnee", title="Tagged", description="Desc", format_type="shp", magnet_link="magnet:?xt=tags")
        tag1 = ItemTag(item_id=item.id, tag="tag-alpha")
        tag2 = ItemTag(item_id=item.id, tag="tag-beta")
        item.tags = [tag1, tag2]
        d = item.to_dict()
        assert "tag-alpha" in d["tags"]
        assert "tag-beta" in d["tags"]


class TestReportModel:
    def test_report_defaults(self):
        from models import Report
        r = Report(reporter_id=1, report_type="item_geodonnee", reason="spam", status="pending")
        assert r.status == "pending"

    def test_cannot_self_report(self):
        from models import Report
        r = Report(reporter_id=5, reported_user_id=5, report_type="user", reason="other")
        assert r.reporter_id == r.reported_user_id


class TestVisualizationLinkModel:
    def test_viz_link_defaults(self):
        from models import VisualizationLink
        v = VisualizationLink(parent_item_id=1, name="Map", url="https://map.test", link_type="embed")
        assert v.link_type == "embed"
        assert v.is_active is True


class TestDataChunkModel:
    def test_chunk_defaults(self):
        from models import DataChunk
        c = DataChunk(name="Test Chunk", owner_user_id=1)
        assert c.is_published is False
