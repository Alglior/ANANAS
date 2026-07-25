import os
import re

from flask import Blueprint, render_template, abort
import mistune

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_docs_site")

bp = Blueprint("doc", __name__)

markdown = mistune.create_markdown(renderer="html", plugins=["table", "strikethrough", "task_lists"])


def _slugify(name):
    return re.sub(r"[^a-z0-9-]", "", name.replace(".md", "").lower().replace("_", "-"))


def _list_docs():
    docs = []
    if not os.path.isdir(DOCS_DIR):
        return docs
    for f in sorted(os.listdir(DOCS_DIR)):
        if f.endswith(".md"):
            slug = _slugify(f)
            title = f.replace(".md", "").replace("-", " ").title()
            docs.append({"slug": slug, "title": title, "filename": f})
    return docs


@bp.route("/docs")
def doc_index():
    docs = _list_docs()
    return render_template(
        "doc_index.html",
        docs=docs,
        title="A.N.A.N.A.S. | Documentation",
        meta_description="Documentation de la plateforme A.N.A.N.A.S.",
    )


@bp.route("/docs/<slug>")
def doc_view(slug):
    docs = _list_docs()
    match = None
    for doc in docs:
        if doc["slug"] == slug:
            match = doc
            break
    if not match:
        abort(404)

    filepath = os.path.join(DOCS_DIR, match["filename"])
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, IOError):
        abort(404)

    html_content = markdown(content)
    return render_template(
        "doc.html",
        title=f"A.N.A.N.A.S. | {match['title']}",
        meta_description=f"Documentation — {match['title']}",
        doc_title=match["title"],
        doc_content=html_content,
        docs=docs,
        current_slug=slug,
    )