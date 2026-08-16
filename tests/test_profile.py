"""Tests du profil utilisateur, du compte et de l'avatar."""
import io


class TestProfileUpdate:
    def test_update_profile(self, user_client, seeded):
        resp = user_client.put(
            "/api/users/profile",
            json={"prenom": "Nouveau", "nom": "Prenom"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "updated"
        assert seeded["user"].prenom == "Nouveau"
        assert seeded["user"].nom == "Prenom"

    def test_update_profile_requires_fields(self, user_client):
        resp = user_client.put("/api/users/profile", json={"prenom": ""})
        assert resp.status_code == 400


class TestAvatarUpload:
    def test_avatar_requires_file(self, user_client):
        resp = user_client.post("/api/users/avatar")
        assert resp.status_code == 400

    def test_avatar_rejects_invalid_format(self, user_client):
        resp = user_client.post(
            "/api/users/avatar",
            data={"avatar": (io.BytesIO(b"data"), "avatar.gif")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_avatar_rejects_invalid_signature(self, user_client):
        resp = user_client.post(
            "/api/users/avatar",
            data={"avatar": (io.BytesIO(b"not-an-image"), "avatar.png")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


class TestAccountPages:
    def test_compte_page_requires_login(self, client):
        resp = client.get("/compte")
        assert resp.status_code == 302

    def test_compte_page_loads(self, user_client, seeded):
        resp = user_client.get("/compte")
        assert resp.status_code == 200

    def test_compte_tabs(self, user_client):
        for tab in ("infos", "securite", "activite", "organisations"):
            resp = user_client.get(f"/compte?tab={tab}")
            assert resp.status_code == 200

    def test_upload_page_loads(self, user_client):
        resp = user_client.get("/upload")
        assert resp.status_code == 200

    def test_public_profile(self, client, seeded):
        resp = client.get(f"/profile/{seeded['user'].id}")
        assert resp.status_code == 200

    def test_public_profile_not_found(self, client):
        resp = client.get("/profile/99999")
        assert resp.status_code == 404