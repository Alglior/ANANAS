"""Tests de modération : gestion des utilisateurs (ban/mute/warn) et des
signalements (reports)."""
from models import User, Report


def _do(admin_client, action, target_id, **extra):
    payload = {"action": action}
    payload.update(extra)
    return admin_client.post(f"/api/users/{target_id}/ban", json=payload)


class TestUserModeration:
    def test_ban_user(self, admin_client, seeded):
        resp = _do(admin_client, "ban", seeded["user"].id)
        assert resp.status_code == 200
        u = User.query.get(seeded["user"].id)
        assert u.banned is True and u.is_active is False

    def test_unban_user(self, admin_client, seeded):
        _do(admin_client, "ban", seeded["user"].id)
        resp = _do(admin_client, "unban", seeded["user"].id)
        assert resp.status_code == 200
        u = User.query.get(seeded["user"].id)
        assert u.banned is False and u.is_active is True

    def test_tempban_user(self, admin_client, seeded):
        resp = _do(admin_client, "tempban", seeded["user"].id, duration=24)
        assert resp.status_code == 200
        assert User.query.get(seeded["user"].id).banned is True

    def test_tempban_invalid_duration(self, admin_client, seeded):
        resp = _do(admin_client, "tempban", seeded["user"].id, duration="abc")
        assert resp.status_code == 400

    def test_mute_user(self, admin_client, seeded):
        resp = _do(admin_client, "mute", seeded["user"].id, duration=12)
        assert resp.status_code == 200
        assert User.query.get(seeded["user"].id).muted_until is not None

    def test_unmute_user(self, admin_client, seeded):
        _do(admin_client, "mute", seeded["user"].id, duration=12)
        resp = _do(admin_client, "unmute", seeded["user"].id)
        assert resp.status_code == 200
        assert User.query.get(seeded["user"].id).muted_until is None

    def test_warn_user(self, admin_client, seeded):
        resp = _do(admin_client, "warn", seeded["user"].id, reason="spam")
        assert resp.status_code == 200
        u = User.query.get(seeded["user"].id)
        assert u.warned is True
        assert "spam" in (u.warnings or "")

    def test_unwarn_user(self, admin_client, seeded):
        _do(admin_client, "warn", seeded["user"].id, reason="spam")
        resp = _do(admin_client, "unwarn", seeded["user"].id)
        assert resp.status_code == 200
        u = User.query.get(seeded["user"].id)
        assert u.warned is False and u.warnings is None

    def test_kick_increments_session_version(self, admin_client, seeded):
        resp = _do(admin_client, "kick", seeded["user"].id)
        assert resp.status_code == 200
        assert User.query.get(seeded["user"].id).session_version >= 1

    def test_invalid_action(self, admin_client, seeded):
        resp = _do(admin_client, "explode", seeded["user"].id)
        assert resp.status_code == 400

    def test_cannot_ban_self(self, admin_client, seeded):
        resp = _do(admin_client, "ban", seeded["admin"].id)
        assert resp.status_code == 403

    def test_list_banned_users(self, admin_client, seeded):
        _do(admin_client, "ban", seeded["user"].id)
        resp = admin_client.get("/api/users/banned")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1

    def test_non_admin_cannot_ban(self, user_client, seeded):
        resp = user_client.post(
            f"/api/users/{seeded['seeder'].id}/ban", json={"action": "ban"}
        )
        assert resp.status_code == 403

    def test_admin_users_page(self, admin_client):
        resp = admin_client.get("/admin/users")
        assert resp.status_code == 200


class TestReports:
    def test_create_report_item(self, user_client):
        resp = user_client.post(
            "/api/reports",
            json={"target_type": "geodonnee", "target_id": 1, "reason": "spam",
                  "description": "Du contenu spam"},
        )
        assert resp.status_code == 200
        assert Report.query.filter_by(target_item_id=1, reason="spam").first()

    def test_create_report_user(self, user_client, seeded):
        resp = user_client.post(
            "/api/reports",
            json={"target_type": "user", "target_id": seeded["seeder"].id, "reason": "fake_data"},
        )
        assert resp.status_code == 200
        assert Report.query.filter_by(reported_user_id=seeded["seeder"].id).first()

    def test_cannot_self_report(self, user_client, seeded):
        resp = user_client.post(
            "/api/reports",
            json={"target_type": "user", "target_id": seeded["user"].id, "reason": "other"},
        )
        assert resp.status_code == 400

    def test_report_requires_reason(self, user_client):
        resp = user_client.post(
            "/api/reports",
            json={"target_type": "geodonnee", "target_id": 1},
        )
        assert resp.status_code == 400

    def test_report_invalid_reason(self, user_client):
        resp = user_client.post(
            "/api/reports",
            json={"target_type": "geodonnee", "target_id": 1, "reason": "evil"},
        )
        assert resp.status_code == 400

    def test_report_invalid_item_type(self, user_client):
        resp = user_client.post(
            "/api/reports",
            json={"target_type": "meme", "target_id": 1, "reason": "spam"},
        )
        assert resp.status_code == 400

    def test_list_reports(self, admin_client, seeded):
        from app import db
        db.session.add(Report(
            reporter_id=seeded["user"].id, report_type="item_geodonnee",
            reason="spam", status="pending", target_item_id=1,
        ))
        db.session.commit()
        resp = admin_client.get("/api/admin/reports")
        assert resp.status_code == 200
        assert resp.get_json()["reports"]

    def test_resolve_report(self, admin_client, seeded):
        from app import db
        db.session.add(Report(
            reporter_id=seeded["user"].id, report_type="item_geodonnee",
            reason="spam", status="pending", target_item_id=1,
        ))
        db.session.commit()
        report = Report.query.first()
        resp = admin_client.post(f"/api/admin/reports/{report.id}/resolve", json={"status": "resolved"})
        assert resp.status_code == 200
        assert Report.query.get(report.id).status == "resolved"

    def test_resolve_invalid_status(self, admin_client, seeded):
        from app import db
        db.session.add(Report(
            reporter_id=seeded["user"].id, report_type="item_geodonnee",
            reason="spam", status="pending", target_item_id=1,
        ))
        db.session.commit()
        report = Report.query.first()
        resp = admin_client.post(f"/api/admin/reports/{report.id}/resolve", json={"status": "bogus"})
        assert resp.status_code == 400