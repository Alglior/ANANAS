from flask import Blueprint, request, jsonify, render_template
from app import db, limiter
from models import ContactMessage
from utils.security import sanitize_html

bp = Blueprint("contact", __name__)


@bp.route("/contact")
def contact_page():
    return render_template(
        "contact.html",
        title="A.N.A.N.A.S | Contact",
        meta_description="Contactez-nous pour toute question ou suggestion.",
    )


@bp.route("/api/contact", methods=["POST"])
@limiter.limit("5 per hour")
def submit_contact():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    subject = (data.get("subject") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not subject or not message:
        return jsonify({"error": "Tous les champs sont requis."}), 400

    if len(name) > 200 or len(email) > 200 or len(subject) > 200:
        return jsonify({"error": "Les champs nom, email et sujet sont limités à 200 caractères."}), 400

    if len(message) > 5000:
        return jsonify({"error": "Le message est limité à 5000 caractères."}), 400

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Adresse email invalide."}), 400

    contact_msg = ContactMessage(
        name=sanitize_html(name),
        email=sanitize_html(email),
        subject=sanitize_html(subject),
        message=sanitize_html(message),
    )
    db.session.add(contact_msg)
    db.session.commit()

    return jsonify({"status": "sent", "message": "Votre message a bien été envoyé."})