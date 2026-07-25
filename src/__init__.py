from flask import render_template as _render_template


def register_all_blueprints(app):
    """Enregistrer tous les blueprints dans l'application et configurer le convertisseur catalogue."""
    from src.catalogue_routes import bp as catalogue_bp, CatalogueTypeConverter

    app.url_map.converters["catalogue_type"] = CatalogueTypeConverter
    app.register_blueprint(catalogue_bp)

    from src.auth_routes import bp as auth_bp
    from src.item_routes import bp as items_bp
    from src.interactions import bp as interactions_bp
    from src.organization_routes import bp as org_bp
    from src.admin import bp as admin_bp
    from src.user_routes import bp as user_bp
    from src.contact_routes import bp as contact_bp
    from src.privacy_routes import bp as privacy_bp
    from src.legal_routes import bp as legal_bp
    from src.tos_routes import bp as tos_bp
    from src.doc_routes import bp as doc_bp
    from src.index_routes import bp as index_bp

    for bp in (auth_bp, items_bp, interactions_bp, org_bp, admin_bp, user_bp,
               contact_bp, privacy_bp, legal_bp, tos_bp, doc_bp, index_bp):
        app.register_blueprint(bp)


def _register_view(app, rule, template, title, meta):
    def view_func():
        return _render_template(template, title=title, meta_description=meta)
    endpoint = rule.lstrip("/") or "home"
    app.add_url_rule(rule, endpoint=endpoint, view_func=view_func)


def _legacy_catalogue(catalogue="donnees", page=1):
    from src.catalogue_routes import _do_catalogue
    return _do_catalogue(catalogue, page)