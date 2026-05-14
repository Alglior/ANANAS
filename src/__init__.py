from flask import render_template as _render_template


def register_all_blueprints(app):
    """Enregistrer tous les blueprints dans l'application et configurer le convertisseur catalogue."""
    from src.catalogue_routes import bp as catalogue_bp, CatalogueTypeConverter

    app.url_map.converters["catalogue_type"] = CatalogueTypeConverter
    app.register_blueprint(catalogue_bp)


def _register_view(app, rule, template, title, meta):
    """Enregistrer une fonction de vue avec un nom d'extrémité (endpoint) unique."""
    def view_func():
        return _render_template(
            template,
            title=title,
            meta_description=meta,
        )
    endpoint = rule.lstrip("/") or "home"
    app.add_url_rule(rule, endpoint=endpoint, view_func=view_func)


def _legacy_catalogue(catalogue="donnees", page=1):
    from src.catalogue_routes import _do_catalogue
    return _do_catalogue(catalogue, page)
