import os
import pytest
from app import db

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def app_config():
    """Create app with SQLite in-memory DB once per session."""
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app


@pytest.fixture(scope="function")
def client(app_config):
    with app_config.test_client() as client:
        with app_config.app_context():
            db.create_all()
            yield client


@pytest.fixture(scope="function")
def seeded(client):
    """Seed database with test data."""
    from models import User, Organization, OrganizationMember, Item, Report, Rating, Comment

    for m in [Report, Rating, Comment, Item, OrganizationMember, Organization, User]:
        db.session.query(m).delete()
    db.session.commit()

    admin = User(prenom="Admin", nom="Super", pseudo="admin-super", password_hash="pbkdf2:sha256:260000$xxx$yyy", is_active=True, banned=False, is_admin=True)
    user = User(prenom="Test", nom="User", pseudo="test-user", password_hash="pbkdf2:sha256:260000$xxx$yyy", is_active=True, banned=False, is_admin=False)
    seeder = User(prenom="Seeder", nom="Bot", pseudo="seeder-bot", password_hash="pbkdf2:sha256:260000$xxx$yyy", is_active=True, banned=False, is_admin=False)

    db.session.add_all([admin, user, seeder])
    db.session.commit()

    org = Organization(name="Org Test", slug="org-test", description="Test org", created_by=seeder.id, is_active=True)
    db.session.add(org)
    db.session.commit()

    org_member = OrganizationMember(user_id=seeder.id, organization_id=org.id, role="owner")
    db.session.add(org_member)
    db.session.commit()

    for i in range(1, 281):
        item_type = "geodonnee" if i < 211 else ("carte" if i <= 260 else "application")
        item = Item(
            type=item_type,
            title=f"Item {i}",
            description=f"Description détaillée de l'item {i} avec des informations complètes sur le jeu de données géographiques et ses caractéristiques techniques.",
            format_type=f"format-{i % 3}",
            magnet_link=f"magnet:?xt=urn:btih:{i:040x}",
            author_name=f"Author {i}",
            organization_id=org.id,
            verification_status="verified",
            license_type="Licence Ouverte / Open License",
            pdf_magnet_link=f"magnet:?xt=urn:btih:pdf{i:040x}",
            data_format_level="simple" if i % 3 == 0 else "individual",
            image_magnet_links=[f"magnet:?xt=urn:btih:img{i:040x}a"],
        )
        db.session.add(item)

    db.session.commit()
    return {"admin": admin, "user": user, "seeder": seeder}
