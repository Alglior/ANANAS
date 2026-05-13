import os
from alembic import context

db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
if not db_uri:
    pg_user = os.environ.get("POSTGRES_USER", "ananas_user")
    pg_pass = os.environ.get("POSTGRES_PASSWORD", "password")
    pg_host = os.environ.get("POSTGRES_HOST", "postgres")
    pg_db = os.environ.get("POSTGRES_DB", "ananas")
    db_uri = f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_db}"

config = context.config
config.set_main_option("sqlalchemy.url", db_uri)

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    from flask_app import create_app, db
    app = create_app()
    with app.app_context():
        context.configure(
            connection=db.get_engine(),
            target_metadata=db.metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
