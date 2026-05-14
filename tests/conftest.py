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

    admin = User(prenom="Admin", nom="Super", email="admin@test.com", password_hash="pbkdf2:sha256:260000$xxx$yyy", is_active=True, banned=False, is_admin=True)
    user = User(prenom="Test", nom="User", email="user@test.com", password_hash="pbkdf2:sha256:260000$xxx$yyy", is_active=True, banned=False, is_admin=False)
    seeder = User(prenom="Seeder", nom="Bot", email="seeder@test.com", password_hash="pbkdf2:sha256:260000$xxx$yyy", is_active=True, banned=False, is_admin=False)

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
            description=f"Description de l'item {i}",
            format_type=f"format-{i % 3}",
            size_mb=50 + i,
            magnet_link=f"magnet:?xt=urn:btih:{i:040x}",
            author_name=f"Author {i}",
            organization_id=org.id if i % 2 == 0 else None,
            is_published=True,
            verification_status="verified" if i % 5 == 0 else "unofficial",
        )
        db.session.add(item)

    db.session.commit()
    return {"admin": admin, "user": user, "seeder": seeder}
