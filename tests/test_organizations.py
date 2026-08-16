"""Tests des organisations : CRUD, rôles, membres, invitations."""
from models import Organization, OrganizationMember, OrganizationRole


class TestOrganizationCRUD:
    def test_create_organization(self, user_client):
        resp = user_client.post("/api/organizations", json={"name": "Nouvelle Org"})
        assert resp.status_code == 200
        data = resp.get_json()
        org = Organization.query.get(data["id"])
        assert org.name == "Nouvelle Org"
        # le créateur devient owner
        member = OrganizationMember.query.filter_by(organization_id=org.id, role="owner").first()
        assert member is not None

    def test_create_organization_name_too_short(self, user_client):
        resp = user_client.post("/api/organizations", json={"name": "x"})
        assert resp.status_code == 400

    def test_organization_list(self, client, seeded):
        resp = client.get("/organizations")
        assert resp.status_code == 200
        assert b"Org Test" in resp.data

    def test_organization_detail(self, client, seeded):
        resp = client.get("/organizations/org-test")
        assert resp.status_code == 200

    def test_organization_not_found(self, client):
        resp = client.get("/organizations/does-not-exist")
        assert resp.status_code == 404

    def test_organization_items_view(self, client, seeded):
        resp = client.get("/organizations/org-test/items")
        assert resp.status_code == 200

    def test_organization_delete_requires_owner(self, user_client, seeded):
        resp = user_client.delete("/api/organizations/org-test")
        assert resp.status_code == 403


class TestOrganizationMembership:
    def test_join_organization(self, user_client, seeded):
        # le user n'est pas membre ; il rejoint
        resp = user_client.post("/api/organizations/org-test/join")
        assert resp.status_code == 200
        member = OrganizationMember.query.filter_by(
            user_id=seeded["user"].id, organization_id=seeded.get("org_id") or 1
        ).first()
        assert member is not None

    def test_join_already_member(self, seeder_client, seeded):
        resp = seeder_client.post("/api/organizations/org-test/join")
        assert resp.status_code == 409

    def test_leave_organization(self, user_client, seeded):
        user_client.post("/api/organizations/org-test/join")
        resp = user_client.post("/api/organizations/org-test/leave")
        assert resp.status_code == 200

    def test_invite_member(self, seeder_client, seeded):
        resp = seeder_client.post(
            "/api/organizations/org-test/invite", json={"pseudo": "test-user"}
        )
        assert resp.status_code == 200
        assert OrganizationMember.query.filter_by(
            user_id=seeded["user"].id, organization_id=1, role="member"
        ).first() is not None

    def test_invite_unknown_user(self, seeder_client):
        resp = seeder_client.post(
            "/api/organizations/org-test/invite", json={"pseudo": "ghost"}
        )
        assert resp.status_code == 404


class TestOrganizationRoles:
    def test_create_role(self, seeder_client):
        resp = seeder_client.post(
            "/api/organizations/org-test/roles",
            json={"name": "Éditeur", "permissions": ["manage_items"]},
        )
        assert resp.status_code == 200
        role = OrganizationRole.query.filter_by(organization_id=1, name="Éditeur").first()
        assert role is not None
        assert "manage_items" in role.permissions

    def test_create_role_invalid_permissions_filtered(self, seeder_client):
        resp = seeder_client.post(
            "/api/organizations/org-test/roles",
            json={"name": "Rôle", "permissions": ["manage_items", "not_a_perm"]},
        )
        data = resp.get_json()
        assert "not_a_perm" not in data["permissions"]

    def test_create_duplicate_role(self, seeder_client):
        seeder_client.post("/api/organizations/org-test/roles", json={"name": "Doublon"})
        resp = seeder_client.post("/api/organizations/org-test/roles", json={"name": "Doublon"})
        assert resp.status_code == 409

    def test_list_roles(self, seeder_client):
        seeder_client.post("/api/organizations/org-test/roles", json={"name": "RôleX"})
        resp = seeder_client.get("/api/organizations/org-test/roles")
        assert resp.status_code == 200
        assert any(r["name"] == "RôleX" for r in resp.get_json())

    def test_update_role(self, seeder_client):
        role_id = seeder_client.post(
            "/api/organizations/org-test/roles", json={"name": "RôleA"}
        ).get_json()["id"]
        resp = seeder_client.put(
            f"/api/organizations/org-test/roles/{role_id}",
            json={"name": "RôleB", "permissions": ["edit_org"]},
        )
        assert resp.status_code == 200
        assert OrganizationRole.query.get(role_id).name == "RôleB"

    def test_delete_role(self, seeder_client):
        role_id = seeder_client.post(
            "/api/organizations/org-test/roles", json={"name": "À supprimer"}
        ).get_json()["id"]
        resp = seeder_client.delete(f"/api/organizations/org-test/roles/{role_id}")
        assert resp.status_code == 200
        assert OrganizationRole.query.get(role_id) is None

    def test_non_owner_cannot_manage_roles(self, user_client):
        resp = user_client.post(
            "/api/organizations/org-test/roles", json={"name": "Hack"}
        )
        assert resp.status_code == 403


class TestOrganizationMembersManagement:
    def test_update_member_role(self, seeder_client, seeded):
        user_client_add = seeded["user"]
        # ajouter le user en tant que membre
        OrganizationMember.query.filter_by(
            user_id=user_client_add.id, organization_id=1
        ).delete()
        from app import db
        db.session.add(OrganizationMember(
            user_id=user_client_add.id, organization_id=1, role="member"))
        db.session.commit()
        resp = seeder_client.post(
            f"/api/organizations/org-test/members/{user_client_add.id}/role",
            json={"role": "moderator"},
        )
        assert resp.status_code == 200

    def test_remove_member(self, seeder_client, seeded):
        from app import db
        OrganizationMember.query.filter_by(
            user_id=seeded["user"].id, organization_id=1
        ).delete()
        db.session.add(OrganizationMember(
            user_id=seeded["user"].id, organization_id=1, role="member"))
        db.session.commit()
        resp = seeder_client.delete(
            f"/api/organizations/org-test/members/{seeded['user'].id}"
        )
        assert resp.status_code == 200

    def test_cannot_remove_owner(self, seeder_client, seeded):
        resp = seeder_client.delete(
            f"/api/organizations/org-test/members/{seeded['seeder'].id}"
        )
        assert resp.status_code == 403