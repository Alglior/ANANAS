import os
from flask import Blueprint, render_template, current_app, send_file, abort

bp = Blueprint("rapport", __name__)


@bp.route("/rapport")
def rapport_page():
    static_folder = current_app.static_folder
    if not static_folder:
        static_folder = os.path.join(current_app.root_path, "static")
    rapports_dir = os.path.join(static_folder, "rapports")

    pdfs = []
    if os.path.isdir(rapports_dir):
        for fname in sorted(os.listdir(rapports_dir)):
            if fname.lower().endswith(".pdf"):
                filepath = os.path.join(rapports_dir, fname)
                stat = os.stat(filepath)
                pdfs.append({
                    "name": fname,
                    "path": f"/rapport/pdf/{fname}",
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                })

    return render_template(
        "rapport.html",
        title="A.N.A.N.A.S | Rapports",
        meta_description="Rapports et documents PDF de la plateforme A.N.A.N.A.S.",
        pdfs=pdfs,
    )


@bp.route("/rapport/pdf/<path:filename>")
def serve_pdf(filename):
    static_folder = current_app.static_folder
    if not static_folder:
        static_folder = os.path.join(current_app.root_path, "static")
    rapports_dir = os.path.join(static_folder, "rapports")
    filepath = os.path.normpath(os.path.join(rapports_dir, filename))

    if not filepath.startswith(os.path.normpath(rapports_dir)):
        abort(403)

    if not os.path.isfile(filepath):
        abort(404)

    response = send_file(filepath, mimetype="application/pdf")
    response.headers["X-PDF-Viewer"] = "1"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Content-Disposition"] = "inline"
    return response