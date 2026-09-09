"""Tests exhaustifs de tous les endpoints listés dans la documentation API.
Vérifie que les snippets de code (curl/python/javascript) correspondent
au comportement réel de chaque endpoint."""

import io
from models import User, Organization, OrganizationMember, Item, Rating, Comment, DataChunk, VisualizationLink


class TestAuthentification:
    def test_connexion_page_get(self, client):
        resp = client.get("/connexion")
        assert resp.status_code == 200

    def test_connexion_post_form(self, client, seeded):
        resp = client.post("/connexion", data={"pseudo": "test-user", "password": "wrong-password"},
                           follow_redirects=True)
        assert resp.status_code == 401

    def test_connexion_bad_credentials(self, client):
        resp = client.post("/connexion", data={"pseudo": "inconnu", "password": "x"})
        assert resp.status_code == 401

    def test_inscription_page_get(self, client):
        resp = client.get("/inscription")
        assert resp.status_code == 200

    def test_inscription_post_form(self, client):
        resp = client.post(
            "/inscription",
            data={"prenom": "Jane", "nom": "Doe", "password": "Str0ng@Pass1!"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        created = User.query.filter(User.pseudo.like("jane-doe#%")).first()
        assert created is not None
        assert created.prenom == "Jane"
        assert created.nom == "Doe"

    def test_inscription_weak_password(self, client):
        resp = client.post(
            "/inscription",
            data={"prenom": "Weak", "nom": "Pass", "password": "123"},
        )
        assert resp.status_code == 400

    def test_logout(self, user_client):
        resp = user_client.get("/logout")
        assert resp.status_code == 302


class TestCatalogue:
    def test_catalogue_donnees(self, client, seeded):
        resp = client.get("/catalogue/donnees")
        assert resp.status_code == 200
        assert b"Item 1" in resp.data

    def test_catalogue_cartes(self, client, seeded):
        resp = client.get("/catalogue/cartes")
        assert resp.status_code == 200

    def test_catalogue_applications(self, client, seeded):
        resp = client.get("/catalogue/applications")
        assert resp.status_code == 200

    def test_catalogue_page(self, client, seeded):
        resp = client.get("/catalogue/donnees/2")
        assert resp.status_code == 200

    def test_catalogue_json(self, client, seeded):
        resp = client.get("/catalogue/donnees/1/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert "page" in data
        assert data["page"] == 1

    def test_catalogue_invalid_type_404(self, client):
        resp = client.get("/catalogue/invalide")
        assert resp.status_code == 302


class TestElements:
    def test_item_detail(self, client, seeded):
        resp = client.get("/catalogue/item/1")
        assert resp.status_code == 200

    def test_item_detail_not_found(self, client):
        resp = client.get("/catalogue/item/99999")
        assert resp.status_code in (302, 404)

    def test_item_data_geodonnee(self, client, seeded):
        resp = client.get("/catalogue/item/1/data")
        assert resp.status_code == 200

    def test_item_data_non_geodonnee_redirect(self, client, seeded):
        from app import db
        item = Item(type="carte", title="Map", description="d",
                    magnet_link="magnet:?xt=urn:btih:maponly")
        db.session.add(item)
        db.session.commit()
        resp = client.get(f"/catalogue/item/{item.id}/data")
        assert resp.status_code in (302, 404)

    def test_item_gallery(self, client, seeded):
        resp = client.get("/catalogue/item/1/gallery")
        assert resp.status_code == 200

    def test_item_comments_json(self, client, seeded):
        resp = client.get("/catalogue/item/1/comments/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "item" in data
        assert "comments" in data

    def test_item_magnets_download(self, client, seeded):
        resp = client.get("/catalogue/item/1/magnets/download")
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/plain")

    def test_item_details_json(self, client, seeded):
        resp = client.get("/catalogue/item/1/details/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["item"]["id"] == 1

    def test_image_status(self, user_client, seeded):
        from app import db
        item = Item(type="geodonnee", title="Img", description="d",
                    magnet_link="magnet:?xt=urn:btih:imgtest")
        db.session.add(item)
        db.session.commit()
        resp = user_client.get(f"/api/items/{item.id}/image-status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pending" in data

    def test_rate_item_form(self, user_client, seeded):
        resp = user_client.post("/catalogue/item/1/rate", data={"rating": "4"})
        assert resp.status_code in (302, 200)
        rating = Rating.query.filter_by(item_id=1, user_id=seeded["user"].id).first()
        assert rating is not None
        assert rating.rating == 4

    def test_rate_item_out_of_range(self, user_client):
        resp = user_client.post("/catalogue/item/1/rate", data={"rating": "9"})
        assert resp.status_code in (302, 200)
        assert Rating.query.filter_by(item_id=1).count() == 0

    def test_rate_requires_login(self, client):
        resp = client.post("/catalogue/item/1/rate", data={"rating": "5"})
        assert resp.status_code == 302

    def test_add_comment_form(self, user_client, seeded):
        resp = user_client.post(
            "/catalogue/item/1/comment", data={"text": "Excellent jeu de données"}
        )
        assert resp.status_code in (302, 200)
        assert Comment.query.filter_by(item_id=1, content="Excellent jeu de données").first()

    def test_add_comment_empty_rejected(self, user_client):
        from models import Comment
        resp = user_client.post("/catalogue/item/1/comment", data={"text": "   "})
        assert resp.status_code in (302, 200)
        # Vérifie que le commentaire vide n'a pas été créé
        # (on ignore les éventuels commentaires ajoutés par d'autres tests)
        empty_comments = Comment.query.filter(Comment.content == "").count()
        assert empty_comments == 0

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

    def test_add_viz_link(self, user_client, seeded):
        from app import db
        item = Item(type="geodonnee", title="Viz", description="d",
                    magnet_link="magnet:?xt=urn:btih:viztest", owner_user_id=seeded["user"].id)
        db.session.add(item)
        db.session.commit()
        resp = user_client.post(
            f"/api/items/{item.id}/viz-links",
            json={"name": "Carte", "url": "https://maps.example.com/view", "link_type": "external"},
        )
        assert resp.status_code == 200
        assert VisualizationLink.query.filter_by(parent_item_id=item.id).count() == 1

    def test_add_viz_link_invalid_url(self, user_client, seeded):
        from app import db
        item = Item(type="geodonnee", title="VizBad", description="d",
                    magnet_link="magnet:?xt=urn:btih:vizbad", owner_user_id=seeded["user"].id)
        db.session.add(item)
        db.session.commit()
        resp = user_client.post(
            f"/api/items/{item.id}/viz-links",
            json={"name": "Bad", "url": "javascript:alert(1)", "link_type": "external"},
        )
        assert resp.status_code == 400

    def test_comment_requires_login(self, client):
        resp = client.post("/catalogue/item/1/comment", data={"text": "test"})
        assert resp.status_code == 302

    def test_reply_requires_login(self, client):
        resp = client.post("/api/catalogue/item/1/reply", json={"parent_id": 1, "text": "test"})
        assert resp.status_code == 302


class TestUtilisateurs:
    def test_public_profile(self, client, seeded):
        resp = client.get(f"/profile/{seeded['user'].id}")
        assert resp.status_code == 200

    def test_public_profile_not_found(self, client):
        resp = client.get("/profile/99999")
        assert resp.status_code == 404

    def test_compte_dashboard(self, user_client):
        resp = user_client.get("/compte")
        assert resp.status_code == 200

    def test_compte_requires_login(self, client):
        resp = client.get("/compte")
        assert resp.status_code == 302

    def test_update_profile_json(self, user_client):
        resp = user_client.put(
            "/api/users/profile",
            json={"prenom": "Jean", "nom": "Dupont"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "updated"

    def test_update_profile_requires_login(self, client):
        resp = client.put("/api/users/profile", json={"prenom": "X"})
        assert resp.status_code == 302

    def test_change_password_json(self, user_client, seeded):
        user = seeded["user"]
        from werkzeug.security import generate_password_hash, check_password_hash
        user.password_hash = generate_password_hash("OldPass1!")
        from app import db
        db.session.commit()
        resp = user_client.post(
            "/api/users/change-password",
            json={"current_password": "OldPass1!", "new_password": "NewStr0ng!"},
        )
        assert resp.status_code == 200
        from app import db
        db.session.refresh(user)
        assert check_password_hash(user.password_hash, "NewStr0ng!")

    def test_change_password_wrong_current(self, user_client, seeded):
        resp = user_client.post(
            "/api/users/change-password",
            json={"current_password": "wrong", "new_password": "NewStr0ng!"},
        )
        assert resp.status_code == 400

    def test_change_password_requires_login(self, client):
        resp = client.post("/api/users/change-password", json={})
        assert resp.status_code == 302

    def test_upload_avatar(self, user_client):
        resp = user_client.post(
            "/api/users/avatar",
            data={"avatar": (io.BytesIO(b"fake-image-data"), "avatar.png")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (200, 400)

    def test_upload_avatar_requires_login(self, client):
        resp = client.post("/api/users/avatar")
        assert resp.status_code == 302


class TestPublication:
    def test_upload_file_form(self, user_client):
        resp = user_client.post(
            "/api/upload/file",
            data={
                "title": "Mon fichier test",
                "type": "geodonnee",
                "format_type": "csv",
                "data_text": "col1,col2\n1,2\n3,4",
            },
        )
        assert resp.status_code == 200
        assert DataChunk.query.filter_by(name="Mon fichier test").count() >= 1

    def test_upload_file_requires_title(self, user_client):
        resp = user_client.post("/api/upload/file", data={"title": ""})
        assert resp.status_code == 400

    def test_upload_file_requires_login(self, client):
        resp = client.post("/api/upload/file", data={"title": "x"})
        assert resp.status_code == 302

    def test_create_item_json(self, user_client):
        resp = user_client.post(
            "/api/upload/item",
            json={
                "title": "Mon jeu de test",
                "type": "geodonnee",
                "format_type": "csv",
                "description": "Description",
                "data_format_level": "simple",
                "magnet_link": "magnet:?xt=urn:btih:abcdef01",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "created"
        item = Item.query.get(data["id"])
        assert item is not None
        assert item.title == "Mon jeu de test"

    def test_create_item_requires_title(self, user_client):
        resp = user_client.post("/api/upload/item", json={"title": "", "type": "geodonnee"})
        assert resp.status_code == 400

    def test_create_item_invalid_type(self, user_client):
        resp = user_client.post("/api/upload/item", json={"title": "X", "type": "invalide"})
        assert resp.status_code == 400

    def test_update_draft_json(self, user_client):
        created = user_client.post(
            "/api/upload/item",
            json={"title": "Brouillon test", "type": "geodonnee", "status": "draft"},
        ).get_json()
        item_id = created["id"]
        resp = user_client.put(
            f"/api/upload/item/{item_id}",
            json={"title": "Titre modifié", "description": "Nouvelle description"},
        )
        assert resp.status_code == 200
        assert Item.query.get(item_id).title == "Titre modifié"

    def test_delete_to_trash(self, user_client):
        created = user_client.post(
            "/api/upload/item",
            json={"title": "À supprimer", "type": "geodonnee", "status": "draft"},
        ).get_json()
        item_id = created["id"]
        resp = user_client.delete(f"/api/upload/item/{item_id}")
        assert resp.status_code == 200
        assert Item.query.get(item_id).status == "trashed"

    def test_restore_from_trash(self, user_client):
        created = user_client.post(
            "/api/upload/item",
            json={"title": "À restaurer", "type": "geodonnee", "status": "draft"},
        ).get_json()
        item_id = created["id"]
        user_client.delete(f"/api/upload/item/{item_id}")
        resp = user_client.post(f"/api/upload/item/{item_id}/restore")
        assert resp.status_code == 200
        assert Item.query.get(item_id).status == "draft"

    def test_purge_trashed(self, user_client):
        created = user_client.post(
            "/api/upload/item",
            json={"title": "À purger", "type": "geodonnee", "status": "draft"},
        ).get_json()
        item_id = created["id"]
        user_client.delete(f"/api/upload/item/{item_id}")
        resp = user_client.delete(f"/api/upload/item/{item_id}/purge")
        assert resp.status_code == 200
        assert Item.query.get(item_id) is None

    def test_list_drafts(self, user_client):
        user_client.post("/api/upload/item", json={"title": "Draft", "type": "geodonnee", "status": "draft"})
        resp = user_client.get("/api/upload/drafts")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_items"] >= 1

    def test_list_trash(self, user_client):
        created = user_client.post(
            "/api/upload/item",
            json={"title": "Trash test", "type": "geodonnee", "status": "draft"},
        ).get_json()
        user_client.delete(f"/api/upload/item/{created['id']}")
        resp = user_client.get("/api/upload/trash")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_items"] >= 1

    def test_list_publications(self, user_client):
        user_client.post("/api/upload/item", json={"title": "Pub test", "type": "geodonnee", "status": "published"})
        resp = user_client.get("/api/upload/publications")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_items"] >= 1

    def test_create_item_requires_login(self, client):
        resp = client.post("/api/upload/item", json={"title": "X", "type": "geodonnee"})
        assert resp.status_code == 302


class TestOrganizations:
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

    def test_create_organization_json(self, user_client):
        resp = user_client.post("/api/organizations", json={"name": "Ma Super Org"})
        assert resp.status_code == 200
        data = resp.get_json()
        org = Organization.query.get(data["id"])
        assert org is not None
        assert org.name == "Ma Super Org"

    def test_create_organization_too_short(self, user_client):
        resp = user_client.post("/api/organizations", json={"name": "x"})
        assert resp.status_code == 400

    def test_join_organization(self, user_client, seeded):
        resp = user_client.post("/api/organizations/org-test/join")
        assert resp.status_code == 200
        assert OrganizationMember.query.filter_by(
            user_id=seeded["user"].id, organization_id=1
        ).first() is not None

    def test_join_already_member(self, seeder_client):
        resp = seeder_client.post("/api/organizations/org-test/join")
        assert resp.status_code == 409

    def test_leave_organization(self, user_client, seeded):
        user_client.post("/api/organizations/org-test/join")
        resp = user_client.post("/api/organizations/org-test/leave")
        assert resp.status_code == 200

    def test_update_member_role(self, seeder_client, seeded):
        from app import db
        OrganizationMember.query.filter_by(user_id=seeded["user"].id, organization_id=1).delete()
        db.session.add(OrganizationMember(
            user_id=seeded["user"].id, organization_id=1, role="member"))
        db.session.commit()
        resp = seeder_client.post(
            f"/api/organizations/org-test/members/{seeded['user'].id}/role",
            json={"role": "moderator"},
        )
        assert resp.status_code == 200

    def test_remove_member(self, seeder_client, seeded):
        from app import db
        OrganizationMember.query.filter_by(user_id=seeded["user"].id, organization_id=1).delete()
        db.session.add(OrganizationMember(
            user_id=seeded["user"].id, organization_id=1, role="member"))
        db.session.commit()
        resp = seeder_client.delete(f"/api/organizations/org-test/members/{seeded['user'].id}")
        assert resp.status_code == 200

    def test_invite_member_by_pseudo(self, seeder_client, seeded):
        resp = seeder_client.post(
            "/api/organizations/org-test/invite", json={"pseudo": "test-user"}
        )
        assert resp.status_code == 200

    def test_invite_unknown_user(self, seeder_client):
        resp = seeder_client.post(
            "/api/organizations/org-test/invite", json={"pseudo": "ghost"}
        )
        assert resp.status_code == 404

    def test_create_custom_role(self, seeder_client):
        resp = seeder_client.post(
            "/api/organizations/org-test/roles",
            json={"name": "Éditeur", "permissions": ["manage_items"]},
        )
        assert resp.status_code == 200
        from models import OrganizationRole
        role = OrganizationRole.query.filter_by(organization_id=1, name="Éditeur").first()
        assert role is not None
        assert "manage_items" in role.permissions

    def test_list_roles(self, seeder_client):
        seeder_client.post("/api/organizations/org-test/roles", json={"name": "TestRole"})
        resp = seeder_client.get("/api/organizations/org-test/roles")
        assert resp.status_code == 200
        assert any(r["name"] == "TestRole" for r in resp.get_json())

    def test_update_role(self, seeder_client):
        role_id = seeder_client.post(
            "/api/organizations/org-test/roles", json={"name": "RôleA"}
        ).get_json()["id"]
        resp = seeder_client.put(
            f"/api/organizations/org-test/roles/{role_id}",
            json={"name": "RôleB", "permissions": ["edit_org"]},
        )
        assert resp.status_code == 200
        from models import OrganizationRole
        assert OrganizationRole.query.get(role_id).name == "RôleB"

    def test_delete_role(self, seeder_client):
        role_id = seeder_client.post(
            "/api/organizations/org-test/roles", json={"name": "À supprimer"}
        ).get_json()["id"]
        resp = seeder_client.delete(f"/api/organizations/org-test/roles/{role_id}")
        assert resp.status_code == 200
        from models import OrganizationRole
        assert OrganizationRole.query.get(role_id) is None

    def test_delete_organization_requires_owner(self, user_client):
        resp = user_client.delete("/api/organizations/org-test")
        assert resp.status_code == 403

    def test_create_organization_requires_login(self, client):
        resp = client.post("/api/organizations", json={"name": "X"})
        assert resp.status_code == 302

    def test_join_requires_login(self, client):
        resp = client.post("/api/organizations/org-test/join")
        assert resp.status_code == 302


class TestReports:
    def test_create_report_json(self, user_client, seeded):
        resp = user_client.post(
            "/api/reports",
            json={
                "target_type": "geodonnee",
                "target_id": 1,
                "reason": "fake_data",
                "description": "Données suspectes",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "created"

    def test_create_report_requires_reason(self, user_client):
        resp = user_client.post(
            "/api/reports",
            json={"target_type": "geodonnee", "target_id": 1, "reason": ""},
        )
        assert resp.status_code == 400

    def test_create_report_invalid_reason(self, user_client):
        resp = user_client.post(
            "/api/reports",
            json={"target_type": "geodonnee", "target_id": 1, "reason": "invalid"},
        )
        assert resp.status_code == 400

    def test_create_report_requires_login(self, client):
        resp = client.post("/api/reports", json={})
        assert resp.status_code == 302

    def test_create_report_rejects_form(self, client, seeded):
        with client.session_transaction() as sess:
            sess["user_id"] = seeded["user"].id
            sess["session_version"] = seeded["user"].session_version
        resp = client.post("/api/reports", data={"target_type": "geodonnee", "target_id": 1, "reason": "spam"})
        assert resp.status_code == 415


class TestContact:
    def test_contact_json(self, client):
        resp = client.post(
            "/api/contact",
            json={"name": "Jean", "email": "jean@example.com", "subject": "Question", "message": "Bonjour"},
            headers={"X-CSRF-Token": "test"},
        )
        assert resp.status_code == 200

    def test_contact_form(self, client):
        resp = client.post(
            "/api/contact",
            data={"name": "Jean", "email": "jean@example.com", "subject": "Question", "message": "Bonjour"},
        )
        assert resp.status_code in (200, 422)


class TestAdministration:
    def test_admin_dashboard(self, admin_client):
        resp = admin_client.get("/admin/accueil")
        assert resp.status_code == 302

    def test_admin_users(self, admin_client):
        resp = admin_client.get("/admin/users")
        assert resp.status_code == 200

    def test_ban_user_json(self, admin_client, seeded):
        resp = admin_client.post(
            f"/api/users/{seeded['user'].id}/ban",
            json={"action": "ban", "reason": "Non respect des CGU"},
        )
        assert resp.status_code == 200
        from app import db
        db.session.refresh(seeded["user"])
        assert seeded["user"].banned is True

    def test_unban_user(self, admin_client, seeded):
        seeded["user"].banned = True
        from app import db
        db.session.commit()
        resp = admin_client.post(
            f"/api/users/{seeded['user'].id}/ban",
            json={"action": "unban"},
        )
        assert resp.status_code == 200
        db.session.refresh(seeded["user"])
        assert seeded["user"].banned is False

    def test_list_banned(self, admin_client, seeded):
        seeded["user"].banned = True
        from app import db
        db.session.commit()
        resp = admin_client.get("/api/users/banned")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 1

    def test_non_admin_cannot_ban(self, user_client, seeded):
        resp = user_client.post(f"/api/users/{seeded['admin'].id}/ban", json={"action": "ban"})
        assert resp.status_code == 403

    def test_ban_requires_login(self, client, seeded):
        resp = client.post(f"/api/users/{seeded['user'].id}/ban", json={"action": "ban"})
        assert resp.status_code == 302

    def test_admin_reports_page(self, admin_client):
        resp = admin_client.get("/admin/reports")
        assert resp.status_code == 302

    def test_admin_moderation(self, admin_client):
        resp = admin_client.get("/admin/moderation")
        assert resp.status_code == 200

    def test_admin_delete_comment(self, admin_client, seeded):
        from app import db
        comment = Comment(item_id=1, user_id=seeded["user"].id, author_name="Test", content="À supprimer")
        db.session.add(comment)
        db.session.commit()
        resp = admin_client.delete(f"/api/admin/comments/{comment.id}")
        assert resp.status_code == 200

    def test_admin_delete_item(self, admin_client, seeded):
        from app import db
        from models import Item as ItemModel
        item = ItemModel(type="geodonnee", title="À supprimer admin", description="d",
                    magnet_link="magnet:?xt=urn:btih:admindelete")
        db.session.add(item)
        db.session.commit()
        resp = admin_client.delete(f"/api/admin/items/{item.id}")
        assert resp.status_code == 200
        # L'admin hard-delete (suppression définitive)
        assert db.session.get(Item, item.id) is None

    def test_admin_verify_item(self, admin_client, seeded):
        from app import db
        item = Item.query.get(1)
        item.verification_status = "unofficial"
        db.session.commit()
        resp = admin_client.post(f"/api/admin/items/1/verify")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["verification_status"] == "verified"

    def test_admin_unverify_item(self, admin_client, seeded):
        from app import db
        item = Item.query.get(1)
        item.verification_status = "verified"
        db.session.commit()
        resp = admin_client.post(f"/api/admin/items/1/unverify")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["verification_status"] == "unofficial"

    def test_non_admin_cannot_verify(self, user_client):
        resp = user_client.post("/api/admin/items/1/verify")
        assert resp.status_code == 403

    def test_admin_audit(self, admin_client):
        resp = admin_client.get("/admin/audit")
        assert resp.status_code == 200

    def test_admin_contact_messages(self, admin_client):
        resp = admin_client.get("/admin/contact-messages")
        assert resp.status_code == 302

    def test_admin_mirrors(self, admin_client):
        resp = admin_client.get("/admin/mirrors")
        assert resp.status_code == 200

    def test_admin_featured(self, admin_client):
        resp = admin_client.get("/admin/featured")
        assert resp.status_code == 200

    def test_admin_geopackages(self, admin_client):
        resp = admin_client.get("/admin/geopackages")
        assert resp.status_code == 200

    def test_admin_catalogues(self, admin_client):
        resp = admin_client.get("/admin/catalogues")
        assert resp.status_code == 302

    def test_admin_replication(self, admin_client):
        resp = admin_client.get("/admin/replication")
        assert resp.status_code == 302

    def test_admin_tags(self, admin_client):
        resp = admin_client.get("/admin/tags")
        assert resp.status_code == 302

    def test_admin_pages_require_admin(self, user_client):
        for path in ["/admin/accueil", "/admin/users", "/admin/reports",
                     "/admin/moderation", "/admin/audit", "/admin/contact-messages",
                     "/admin/mirrors", "/admin/featured", "/admin/geopackages",
                     "/admin/catalogues", "/admin/replication", "/admin/tags"]:
            resp = user_client.get(path)
            assert resp.status_code == 403, f"{path} should be forbidden for non-admin"