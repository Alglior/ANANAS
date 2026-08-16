"""Tests des interactions : notation, commentaires, réponses et vérification."""
from models import Item, Rating, Comment


class TestRatings:
    def test_rate_item(self, user_client, seeded):
        resp = user_client.post("/catalogue/item/1/rate", data={"rating": "4"})
        assert resp.status_code in (302, 200)
        rating = Rating.query.filter_by(item_id=1, user_id=seeded["user"].id).first()
        assert rating is not None
        assert rating.rating == 4

    def test_rate_out_of_range(self, user_client):
        resp = user_client.post("/catalogue/item/1/rate", data={"rating": "9"})
        assert resp.status_code in (302, 200)
        assert Rating.query.filter_by(item_id=1, rating=9).first() is None

    def test_rate_non_numeric(self, user_client):
        resp = user_client.post("/catalogue/item/1/rate", data={"rating": "abc"})
        assert resp.status_code in (302, 200)
        assert Rating.query.filter_by(item_id=1, rating="abc").first() is None

    def test_rate_requires_login(self, client):
        resp = client.post("/catalogue/item/1/rate", data={"rating": "5"})
        assert resp.status_code == 302


class TestComments:
    def test_add_comment(self, user_client, seeded):
        resp = user_client.post(
            "/catalogue/item/1/comment", data={"text": "Excellent jeu de données"}
        )
        assert resp.status_code in (302, 200)
        assert Comment.query.filter_by(item_id=1, content="Excellent jeu de données").first()

    def test_add_comment_sanitized(self, user_client):
        user_client.post(
            "/catalogue/item/1/comment",
            data={"text": '<script>alert("xss")</script>super'},
        )
        c = Comment.query.filter(Comment.item_id == 1).order_by(Comment.id.desc()).first()
        assert "<script>" not in c.content

    def test_add_comment_empty_rejected(self, user_client):
        resp = user_client.post("/catalogue/item/1/comment", data={"text": "   "})
        assert resp.status_code in (302, 200)
        assert Comment.query.filter_by(item_id=1, content="").first() is None

    def test_reply_json(self, user_client, seeded):
        from app import db
        parent = Comment(item_id=1, user_id=seeded["user"].id,
                         author_name="Test User", content="parent")
        db.session.add(parent)
        db.session.commit()
        resp = user_client.post(
            f"/api/catalogue/item/1/reply",
            json={"parent_id": parent.id, "text": "réponse"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["content"] == "réponse"
        assert data["parent_id"] == parent.id

    def test_reply_invalid_parent(self, user_client):
        resp = user_client.post(
            "/api/catalogue/item/1/reply",
            json={"parent_id": 99999, "text": "réponse"},
        )
        assert resp.status_code == 404

    def test_reply_empty(self, user_client):
        resp = user_client.post(
            "/api/catalogue/item/1/reply", json={"text": ""}
        )
        assert resp.status_code == 400


class TestVerification:
    def test_admin_can_verify(self, admin_client, seeded):
        item = Item.query.get(1)
        item.verification_status = "unofficial"
        from app import db
        db.session.commit()
        resp = admin_client.post(
            "/api/items/1/verify",
            json={"status": "verified", "notes": "tout est bon"},
        )
        assert resp.status_code == 200
        item = Item.query.get(1)
        assert item.verification_status == "verified"
        assert item.verifier_user_id == seeded["admin"].id

    def test_admin_verify_invalid_status(self, admin_client):
        resp = admin_client.post("/api/items/1/verify", json={"status": "bogus"})
        assert resp.status_code == 400

    def test_non_admin_cannot_verify(self, user_client):
        resp = user_client.post("/api/items/1/verify", json={"status": "verified"})
        assert resp.status_code == 403

    def test_verify_requires_login(self, client):
        resp = client.post("/api/items/1/verify", json={"status": "verified"})
        assert resp.status_code == 302


class TestCommentsJson:
    def test_comments_json(self, client, seeded):
        resp = client.get("/catalogue/item/1/comments/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "item" in data and "comments" in data

    def test_details_json(self, client, seeded):
        resp = client.get("/catalogue/item/1/details/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["item"]["id"] == 1