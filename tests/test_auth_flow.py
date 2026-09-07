"""Tests du flux d'authentification : inscription, connexion, 2FA, codes de
récupération, changement de mot de passe, déconnexion."""
import pyotp
import pytest

from werkzeug.security import generate_password_hash


def _register(client, prenom="Flux", nom="Auth", password="Str0ng@Pass1!"):
    resp = client.post(
        "/inscription",
        data={"prenom": prenom, "nom": nom, "password": password},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    from models import User
    return User.query.filter(User.pseudo.like(f"{prenom.lower()}-{nom.lower()}#%")).first()


def _login(client, pseudo, password, follow=True):
    return client.post("/connexion", data={"pseudo": pseudo, "password": password}, follow_redirects=follow)


class TestInscription:
    def test_inscription_redirects_to_login_with_pseudo(self, client):
        resp = client.post(
            "/inscription",
            data={"prenom": "Alice", "nom": "Martin", "password": "C0mpl3x@Pass!"},
        )
        assert resp.status_code == 302
        assert "/connexion" in resp.headers["Location"]
        assert "pseudo" in resp.headers["Location"]

    def test_inscription_rejects_weak_password(self, client):
        resp = client.post(
            "/inscription",
            data={"prenom": "Bob", "nom": "Durand", "password": "weak"},
        )
        assert resp.status_code == 400

    def test_inscription_generates_unique_pseudo(self, client):
        from models import User
        for i in range(3):
            _register(client, "Dup", f"Clo{i}")
        pseudos = [u.pseudo for u in User.query.filter(User.pseudo.like("dup-clo%")).all()]
        assert len(set(pseudos)) == 3

    def test_inscription_creates_active_non_admin_user(self, client):
        u = _register(client)
        assert u.is_active is True
        assert u.is_admin is False
        assert u.banned is False


class TestConnexion:
    def test_login_success_sets_session(self, client):
        u = _register(client)
        resp = _login(client, u.pseudo, "Str0ng@Pass1!")
        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert sess["user_id"] == u.id
            assert sess["session_version"] == u.session_version

    def test_login_wrong_password(self, client):
        u = _register(client)
        resp = _login(client, u.pseudo, "WrongPass123!")
        assert resp.status_code == 401

    def test_login_unknown_pseudo(self, client):
        resp = _login(client, "does-not-exist", "Whatever1!")
        assert resp.status_code == 401

    def test_banned_user_cannot_login(self, client, seeded):
        from app import db
        from models import User
        u = seeded["user"]
        u.password_hash = generate_password_hash("Str0ng@Pass1!", method="scrypt")
        u.banned = True
        u.is_active = False
        db.session.commit()
        resp = _login(client, u.pseudo, "Str0ng@Pass1!")
        assert resp.status_code == 401

    def test_logout_clears_session(self, user_client):
        resp = user_client.get("/logout")
        assert resp.status_code == 302
        with user_client.session_transaction() as sess:
            assert "user_id" not in sess


class TestPasswordChange:
    def test_change_password_requires_valid_current(self, user_client, seeded):
        resp = user_client.post(
            "/api/users/change-password",
            json={"current_password": "wrong", "new_password": "NewStr0ng@Pass!"},
        )
        assert resp.status_code == 400

    def test_change_password_updates_and_logs_out(self, user_client, seeded):
        from app import db
        seeded["user"].password_hash = generate_password_hash("OldStr0ng@Pass!", method="scrypt")
        db.session.commit()
        resp = user_client.post(
            "/api/users/change-password",
            json={"current_password": "OldStr0ng@Pass!", "new_password": "NewStr0ng@Pass!"},
        )
        assert resp.status_code == 200
        # session_version incrémenté => ancienne session invalidée
        assert seeded["user"].session_version >= 1

    def test_change_password_rejects_weak_new(self, user_client, seeded):
        from app import db
        seeded["user"].password_hash = generate_password_hash("OldStr0ng@Pass!", method="scrypt")
        db.session.commit()
        resp = user_client.post(
            "/api/users/change-password",
            json={"current_password": "OldStr0ng@Pass!", "new_password": "short"},
        )
        assert resp.status_code == 400


class TestRecoveryCodes:
    def test_generate_recovery_codes_returns_ten(self, user_client, seeded):
        resp = user_client.post("/api/users/generate-recovery-codes")
        assert resp.status_code == 200
        codes = resp.get_json()["codes"]
        assert len(codes) == 10
        assert seeded["user"].recovery_codes_hash is not None
        assert len(seeded["user"].recovery_codes_hash) == 10

    def test_recovery_code_login_consumes_code(self, client, seeded):
        from app import db
        u = seeded["user"]
        u.password_hash = generate_password_hash("Whatever1!", method="scrypt")
        code = "aaaa-bbbb-cccc-dddd"
        u.recovery_codes_hash = [generate_password_hash(code, method="scrypt")]
        db.session.commit()
        resp = _login(client, u.pseudo, "", recovery=code)
        assert resp.status_code == 200
        assert u.recovery_codes_hash == [] or u.recovery_codes_hash is None


def _login(client, pseudo, password="", recovery=""):
    data = {"pseudo": pseudo}
    if password:
        data["password"] = password
    if recovery:
        data["recovery_code"] = recovery
    return client.post("/connexion", data=data, follow_redirects=True)


class TestTwoFactor:
    def test_setup_2fa_returns_secret_and_qr(self, user_client, seeded):
        resp = user_client.post("/api/users/2fa/setup")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["secret"]
        assert data["uri"].startswith("otpauth://")
        assert data["qr_data_uri"].startswith("data:image/png;base64,")
        assert seeded["user"].totp_secret == data["secret"]

    def test_enable_2fa_with_valid_code(self, user_client, seeded):
        setup = user_client.post("/api/users/2fa/setup").get_json()
        secret = setup["secret"]
        code = pyotp.TOTP(secret).now()
        resp = user_client.post("/api/users/2fa/enable", json={"code": code})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "enabled"
        assert seeded["user"].totp_enabled is True

    def test_enable_2fa_with_invalid_code(self, user_client, seeded):
        user_client.post("/api/users/2fa/setup")
        resp = user_client.post("/api/users/2fa/enable", json={"code": "000000"})
        assert resp.status_code == 400
        assert seeded["user"].totp_enabled is False

    def test_2fa_login_flow(self, client):
        u = _register(client)
        # Activer la 2FA directement
        from app import db
        import pyotp
        secret = pyotp.random_base32()
        u.totp_secret = secret
        u.totp_enabled = True
        u.password_hash = generate_password_hash("Str0ng@Pass1!", method="scrypt")
        db.session.commit()

        resp = client.post(
            "/connexion", data={"pseudo": u.pseudo, "password": "Str0ng@Pass1!"}
        )
        assert resp.status_code == 302
        assert "/connexion/2fa" in resp.headers["Location"]
        with client.session_transaction() as sess:
            assert sess["pending_2fa_user_id"] == u.id

        code = pyotp.TOTP(secret).now()
        resp = client.post(
            "/connexion/2fa", data={"code": code}, follow_redirects=True
        )
        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert sess["user_id"] == u.id

    def test_2fa_login_invalid_code(self, client):
        u = _register(client)
        from app import db
        import pyotp
        secret = pyotp.random_base32()
        u.totp_secret = secret
        u.totp_enabled = True
        u.password_hash = generate_password_hash("Str0ng@Pass1!", method="scrypt")
        db.session.commit()
        client.post("/connexion", data={"pseudo": u.pseudo, "password": "Str0ng@Pass1!"})
        resp = client.post("/connexion/2fa", data={"code": "000000"})
        assert resp.status_code == 401

    def test_disable_2fa_requires_password(self, user_client, seeded):
        from app import db
        seeded["user"].password_hash = generate_password_hash("Str0ng@Pass1!", method="scrypt")
        db.session.commit()
        resp = user_client.post("/api/users/2fa/disable", json={"password": "wrong"})
        assert resp.status_code == 400