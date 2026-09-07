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
    # Désactiver le rate limiting : le plafond par défaut (1000/h) serait
    # atteint en exécutant l'ensemble de la suite de tests.
    for ext in app.extensions.get("limiter", ()):
        ext.enabled = False
    return app


@pytest.fixture(scope="function")
def client(app_config):
    with app_config.test_client() as client:
        with app_config.app_context():
            db.drop_all()
            db.create_all()
            yield client


@pytest.fixture(scope="function")
def app_ctx(app_config):
    """Fournir un contexte d'application pour les tests unitaires de modèles."""
    with app_config.app_context():
        db.drop_all()
        db.create_all()
        yield


@pytest.fixture(scope="function")
def seeded(client):
    """Seed database with test data."""
    from models import User, Organization, OrganizationMember, Item, Report, Rating, Comment, CatalogueConfig

    for m in [CatalogueConfig, Report, Rating, Comment, Item, OrganizationMember, Organization, User]:
        db.session.query(m).delete()
    db.session.commit()

    for ctype, enabled in (("donnees", True), ("cartes", True), ("applications", True)):
        db.session.add(CatalogueConfig(catalogue_type=ctype, enabled=enabled))
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
        item.imod_score = item._compute_imod_score()["score"]
        db.session.add(item)

    db.session.commit()
    return {"admin": admin, "user": user, "seeder": seeder}


def _login_as(client, user):
    """Connecte la session Flask en tant que user sans passer par le formulaire."""
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["session_version"] = user.session_version
    return client


@pytest.fixture
def user_client(client, seeded):
    """Client connecté en tant qu'utilisateur standard."""
    return _login_as(client, seeded["user"])


@pytest.fixture
def admin_client(client, seeded):
    """Client connecté en tant qu'administrateur."""
    return _login_as(client, seeded["admin"])


@pytest.fixture
def seeder_client(client, seeded):
    """Client connecté en tant que seeder (propriétaire d'org)."""
    return _login_as(client, seeded["seeder"])
