# Phase 6 — Fonctionnalités Auth & Interactions

### 6.1 Ajouter les handlers POST pour `/connexion` et `/inscription`
**Fichier :** `app.py` (routes additions). Auth par prénom + nom, pas de username.

```python
@app.route("/connexion", methods=["POST"])
def connexion_post():
    prenom = request.form["prenom"]
    nom = request.form["nom"]
    password = request.form["password"]

    user = User.query.filter_by(prenom=prenom, nom=nom).first()
    if user and check_password_hash(user.password_hash, password) and user.is_active and not user.banned:
        session["user_id"] = user.id  # créer session
        return redirect(url_for("home"))

    return render_template("connexion.html", error="Identants incorrects"), 401


@app.route("/inscription", methods=["POST"])
def inscription_post():
    prenom = request.form["prenom"]
    nom = request.form["nom"]
    email = request.form["email"]
    password = request.form["password"]

    user = User(
        prenom=prenom,
        nom=nom,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    return redirect(url_for("connexion"))
```

### Affichage du statut de vérification dans les templates

**Rappel : la vérification ne concerne QUE la confiance officielle, PAS la modération.** Tous les items `pending` restent pleinement visibles et accessibles sur le site. Le seul statut qui masque un item serait `rejected` (cas très rare pour non-conformité aux standards du site).

Les deux états normaux sont :
- `verified` → données **approuvées officiellement** par A.N.A.N.A.S. (= confiance officielle, badge 🏛️)
- `pending` → données **visibles et accessibles**, simplement pas encore vérifiées par le site (badge neutre ou absent)

#### Catalogue (catalogue.html) : seuls les données `verified` reçoivent un badge de confiance officielle

```html
<!-- templates/catalogue.html -->
{% for item in items %}
    <div class="item-card">
        {% if item.is_official_verified %}
            <!-- Données officiellement approuvées par A.N.A.N.A.S. → Badge confiance officielle -->
            <span class="badge badge-verified" title="Données vérifiées et approuvées par A.N.A.N.A.S.">🏛️ Données vérifiées</span>
        {% else %}
            <!-- Données visibles mais non encore vérifiées → aucune différence visuelle particulière -->
            <span class="badge badge-pending" title="Données accessibles sur le site, non encore vérifiées par A.N.A.N.A.S.">📋 Données non vérifiées</span>
        {% endif %}

        <h3>{{ item.title }}</h3>
        ...
    </div>
{% endfor %}
```

#### CSS pour différencier visuellement les niveaux de confiance

```css
/* static/css/features/ratings.css (ajout) */
.badge-verified {
    background: #28a745;
    color: white;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.8em;
    display: inline-block;
}

.badge-pending {
    background: #ffc107;
    color: #333;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.8em;
    display: inline-block;
}

.badge-rejected {
    background: #dc3545;
    color: white;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.8em;
    display: inline-block;
    opacity: 0.7;
}
```

#### Page détail (item_detail.html) : mentionner le niveau de confiance

```html
<!-- templates/item_detail.html -->
<div class="verification-info">
    {% if item.is_official_verified %}
        <div class="verified-seal">
            🏛️ Jeu de données vérifié et approuvé par A.N.A.N.A.S.
            <br>Par {{ item.verifier_nom }} le {{ item.verified_at|date("dd/MM/yyyy") }}
        </div>
    {% elif item.verification_status == 'rejected' %}
        <div class="warning-rejected">
            ⚠️ Ces données n'ont pas été approuvées par A.N.A.N.A.S.
            {% if item.verification_notes %}<br>Raison : {{ item.verification_notes }}{% endif %}
        </div>
    {% else %}
        <div class="pending-info">
            ℹ️ Ces données sont accessibles mais n'ont pas encore été vérifiées par A.N.A.N.A.S.
        </div>
    {% endif %}
</div>
```

#### Filtrage avancé (navbar) : lien pour ne voir QUE les données de confiance officielle

```html
<!-- templates/partials/header.html -->
<nav class="filters">
    <a href="/catalogue/donnees" class="{% if not filter_verified %}active{% endif %}">Toutes les données</a>
    <span class="separator">|</span>
    <a href="/catalogue/donnees?verified=1" class="{% if filter_verified %}active{% endif %}">🏛️ Données vérifiées uniquement</a>
</nav>
```

### 6.2 Ajouter le endpoint de rating
**Fichier :** `app.py`

```python
@app.route("/catalogue/item/<int:item_id>/rate", methods=["POST"])
def rate_item(item_id):
    item = Item.query.get_or_404(item_id)
    rating_value = request.form.get("rating")
    # Insérer dans ratings ou mettre à jour l'average
    ...
```

### 6.3 Ajouter le endpoint de commentaire
**Fichier :** `app.py`

```python
@app.route("/catalogue/item/<int:item_id>/comment", methods=["POST"])
def add_comment(item_id):
    item = Item.query.get_or_404(item_id)
    # Insérer dans comments
    ...
```

### 6.4 Endpoint de vérification

Un utilisateur autorisé (admin ou reviewer) peut marquer un item comme `verified`, `pending` ou `rejected`.

```python
@app.route("/api/items/<int:item_id>/verify", methods=["POST"])
@login_required
def verify_item(item_id):
    """
    Marquer un item comme vérifié, en attente ou rejeté.
    Seul les utilisateurs avec rôle 'admin' ou 'reviewer' peuvent utiliser cette route.
    """
    data = request.json
    status = data.get("status")  # "verified" | "pending" | "rejected"

    if status not in ("verified", "pending", "rejected"):
        return jsonify({"error": "Statut invalide"}), 400

    item = Item.query.get_or_404(item_id)

    item.verification_status = status
    item.verifier_user_id = current_user.id
    item.verified_at = datetime.now if status in ("verified", "pending") else None
    item.verification_notes = data.get("notes")  # notes optionnelles du vérificateur
    db.session.commit()

    return jsonify({"status": "updated", "item_id": item_id, "new_status": status})
```

**Template `connexion.html`** — remplacer le champ `username` par deux champs `prenom` et `nom` :
```html
<input name="prenom" placeholder="Prénom">
<input name="nom"  placeholder="Nom">
<input type="password" name="password">
```

**Template `inscription.html`** — idem, remplacer `username` par `prenom` + `nom`.

### 6.5 Gestion des organisations / groupes d'utilisateurs

**Rôle :** un utilisateur peut appartenir à plusieurs organisations avec différents rôles (`member`, `editor`, `admin`, `owner`). Les items publiés peuvent être associés à une organisation → l'auteur affiché devient `"Prénom Nom — Organisation"`.

#### API : Créer/rejoindre/quitter une organisation

```python
# --- POST /api/organizations (créer) ---
@app.route("/api/organizations", methods=["POST"])
@login_required
def create_organization():
    data = request.json
    org = Organization(
        name=data["name"],
        slug=data["name"].lower().replace(" ", "-"),
        description=data.get("description", ""),
        created_by=current_user.id,
        is_active=True
    )
    db.session.add(org)
    member = OrganizationMember(user_id=current_user.id, organization_id=org.id, role="owner")
    db.session.add(member)
    db.session.commit()

    return jsonify({"id": org.id, "slug": org.slug})


# --- POST /api/organizations/<slug>/join (rejoindre) ---
@app.route("/api/organizations/<slug>/join", methods=["POST"])
@login_required
def join_organization(slug):
    org = Organization.query.filter_by(slug=slug).first_or_404()
    existing = OrganizationMember.query.filter_by(user_id=current_user.id, organization_id=org.id).first()
    if existing:
        return jsonify({"error": "Déjà membre"}), 409

    member = OrganizationMember(user_id=current_user.id, organization_id=org.id, role="member")
    db.session.add(member)
    db.session.commit()

    return jsonify({"status": "joined"})


# --- POST /api/organizations/<slug>/leave (quitter) ---
@app.route("/api/organizations/<slug>/leave", methods=["POST"])
@login_required
def leave_organization(slug):
    org = Organization.query.filter_by(slug=slug).first_or_404()
    member = OrganizationMember.query.filter_by(user_id=current_user.id, organization_id=org.id).first()
    if member and member.role != "owner":
        db.session.delete(member)
        db.session.commit()
    return jsonify({"status": "left"})


# --- POST /api/organizations/<slug>/members/<user_id>/role (modifier rôle) ---
@app.route("/api/organizations/<slug>/members/<int:user_id>/role", methods=["POST"])
@login_required
def update_member_role(slug, user_id):
    data = request.json
    org = Organization.query.filter_by(slug=slug).first_or_404()
    member = OrganizationMember.query.filter_by(user_id=current_user.id, organization_id=org.id).first()
    if not member or member.role not in ("admin", "owner"):
        return jsonify({"error": "Non autorisé"}), 403

    target_member = OrganizationMember.query.filter_by(user_id=user_id, organization_id=org.id).first_or_404()
    target_member.role = data["role"]
    db.session.commit()
    return jsonify({"status": "updated", "role": data["role"]})
```

#### Template : Afficher l'organisation de l'auteur dans le catalogue

```html
<!-- templates/catalogue.html -->
{% for item in items %}
    <div class="item-card">
        {% if item.is_official_verified %}
            <span class="badge badge-verified" title="Données vérifiées et approuvées par A.N.A.N.A.S.">🏛️ Données vérifiées</span>
        {% else %}
            <span class="badge badge-pending" title="Données visibles, en attente de vérification par A.N.A.N.A.S.">📋 En attente</span>
        {% endif %}

        <h3>{{ item.title }}</h3>
        <div class="author-info">
            {% if item.organization_name %}
                <a href="/organizations/{{ item.organization_slug }}">
                    🏢 {{ item.organization_name }}
                </a> —
            {% endif %}
            <span>{{ item.author }}</span>
        </div>

        ...
    </div>
{% endfor %}
```

#### Template : Page de profil organisation (`/organizations/<slug>`)

```html
<!-- templates/organization_detail.html -->
<div class="org-header">
    {% if org.logo_url %}
        <img src="{{ org.logo_url }}" alt="{{ org.name }} logo">
    {% endif %}
    <h2>{{ org.name }}</h2>
    {% if org.website_url %}
        <a href="{{ org.website_url }}">{{ org.website_url }}</a>
    {% endif %}
    <p>{{ org.description }}</p>

    <div class="org-members">
        <h3>Membres ({{ org.members | length }})</h3>
        {% for m in org.members %}
            <div class="member-card">
                <span>{{ m.user.prenom }} {{ m.user.nom }}</span>
                <span class="badge badge-{{ m.role }}">{{ m.role }}</span>
            </div>
        {% endfor %}
    </div>

    <div class="org-items">
        <h3>Données ({{ items.total_items }})</h3>
        <a href="/catalogue/donnees?org={{ org.slug }}">Voir toutes les données</a>
    </div>
</div>
```

#### Route : Lister les items d'une organisation (`/catalogue/<type>?org=<slug>`)

```python
def get_catalogue_page(total_page=1, per_page=ITEMS_PER_PAGE, catalogue="donnees", filter_verified=False, org_slug=None):
    ...
    query = Item.query.filter_by(type=item_type)
    if org_slug:
        org = Organization.query.filter_by(slug=org_slug).first()
        if org:
            query = query.filter_by(organization_id=org.id)
    if filter_verified:
        query = query.filter_by(verification_status="verified")
    else:
        query = query.all()

    total_items = len(query.all())
    ...
```

#### Template : Sélectionner son organisation lors de la publication

```html
<!-- Formulaire d'upload / item creation -->
<select name="organization_id">
    <option value="">Aucune organisation</option>
    {% for org in current_user.organizations %}
        <option value="{{ org.organization_id }}">{{ org.organization.name }} ({{ org.role }})</option>
    {% endfor %}
</select>
```

### 6.6 Gestion des bans (banning/unbanning utilisateurs)

**Rôle :** seuls les administrateurs peuvent bannir ou débannir un utilisateur. Un utilisateur banni ne peut plus se connecter ni accéder à l'application.

#### Endpoint API : Bannir/Débannir un utilisateur

```python
@app.route("/api/users/<int:user_id>/ban", methods=["POST"])
@login_required
def ban_user(user_id):
    """Bannir ou débannir un utilisateur (admin uniquement)."""
    if not current_user.is_admin:  # vérifier que current_user est admin
        return jsonify({"error": "Non autorisé"}), 403

    target_user = User.query.get_or_404(user_id)

    data = request.json
    action = data.get("action")  # "ban" ou "unban"

    if action not in ("ban", "unban"):
        return jsonify({"error": "Action invalide"}), 400

    target_user.banned = (action == "ban")

    db.session.commit()

    status = "banni" if action == "ban" else "débanni"
    return jsonify({"status": "updated", "user_id": user_id, "action": action})
```

#### Endpoint API : Lister les utilisateurs bannis

```python
@app.route("/api/users/banned", methods=["GET"])
@login_required
def list_banned_users():
    """Lister tous les utilisateurs bannis (admin uniquement)."""
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    banned = User.query.filter_by(banned=True).all()
    return jsonify([{
        "id": u.id,
        "prenom": u.prenom,
        "nom": u.nom,
        "email": u.email,
        "created_at": u.created_at.isoformat(),
        "banned": u.banned
    } for u in banned])
```

#### Template : Liste admin des utilisateurs bannis (`/admin/users`)

```html
<!-- templates/admin/users.html -->
<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>Nom</th>
            <th>Email</th>
            <th>Statut</th>
            <th>Action</th>
        </tr>
    </thead>
    <tbody>
        {% for user in users %}
        <tr>
            <td>{{ user.id }}</td>
            <td>{{ user.prenom }} {{ user.nom }}</td>
            <td>{{ user.email }}</td>
            <td>
                {% if user.banned %}
                    <span class="badge badge-banned">Banni</span>
                {% else %}
                    <span class="badge badge-active">Actif</span>
                {% endif %}
            </td>
            <td>
                <form action="/api/users/{{ user.id }}/ban" method="POST">
                    <input type="hidden" name="action" value="{% if user.banned %}unban{% else %}ban{% endif %}">
                    <button type="submit">
                        {% if user.banned %}Débannir{% else %}Bannir{% endif %}
                    </button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

#### Template : Message affiché à un utilisateur banni lors de la connexion

```html
<!-- templates/connexion.html -->
{% if error == "banned" %}
    <div class="alert alert-danger">
        Votre compte a été désactivé. Contactez l'administration pour plus d'informations.
    </div>
{% endif %}
```

**Mise à jour du handler de connexion :**
```python
@app.route("/connexion", methods=["POST"])
def connexion_post():
    prenom = request.form["prenom"]
    nom = request.form["nom"]
    password = request.form["password"]

    user = User.query.filter_by(prenom=prenom, nom=nom).first()
    if user and check_password_hash(user.password_hash, password) and user.is_active and not user.banned:
        session["user_id"] = user.id
        return redirect(url_for("home"))

    if user and (not user.is_active or user.banned):
        return render_template("connexion.html", error="banned"), 401

    return render_template("connexion.html", error="Identifiants incorrects"), 401
```

#### Template : Message affiché à un utilisateur banni lorsqu'il tente d'accéder aux pages protégées

Si l'utilisateur est déjà connecté mais que son compte a été banni entre-temps, il doit être déconnecté et redirigé :

```python
# Dans le decorator login_required existant
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('connexion'))

        # Vérifier si l'utilisateur a été banni entre-temps
        current_user = User.query.get(session['user_id'])
        if current_user and (current_user.banned or not current_user.is_active):
            session.clear()  # déconnecter
            return redirect(url_for('connexion'))

        return f(*args, **kwargs)
    return decorated_function
```

### 6.7 Système de signalements (reports)

**Rôle :** un utilisateur connecté peut signaler un autre utilisateur ou un contenu (donnée, carte, application). Un utilisateur ne peut pas se signer lui-même. Les administrateurs consultent les signalements et décident de les clôturer ou les marquer comme non fondés.

#### Endpoint API : Signaler un utilisateur ou un contenu

```python
@app.route("/api/reports", methods=["POST"])
@login_required
def create_report():
    """
    Signaler un utilisateur ou un contenu (donnée, carte, application).
    Un utilisateur ne peut pas se signer lui-même.
    """
    data = request.json
    target_type = data.get("target_type")  # 'user', 'geodonnee', 'carte', 'application'
    target_id = data.get("target_id")
    reason = data.get("reason")  # spam, contenu_inapproprié, fake_data, other
    description = data.get("description", "")

    if not target_type or not target_id or not reason:
        return jsonify({"error": "target_type, target_id et reason sont requis"}), 400

    if reason not in ("spam", "contenu_inapproprié", "fake_data", "other"):
        return jsonify({"error": "Raison invalide"}), 400

    report = Report(
        reporter_id=current_user.id,
        report_type=f"item_{target_type}" if target_type != "user" else "user",
        reason=reason,
        description=description,
        status="pending"
    )

    # Signalement d'un utilisateur
    if target_type == "user":
        reported_user = User.query.get(target_id)
        if not reported_user:
            return jsonify({"error": "Utilisateur introuvable"}), 404
        if reported_user.id == current_user.id:
            return jsonify({"error": "Impossible de se signer soi-même"}), 400
        report.reported_user_id = reported_user.id
    # Signalement d'un contenu
    else:
        item_type_map = {"geodonnee": "geodonnee", "carte": "carte", "application": "application"}
        if target_type not in item_type_map:
            return jsonify({"error": "Type de contenu invalide"}), 400
        item = Item.query.filter_by(id=target_id, type=item_type_map[target_type]).first()
        if not item:
            return jsonify({"error": "Contenu introuvable"}), 404
        report.target_item_id = target_id

    db.session.add(report)
    db.session.commit()

    return jsonify({"status": "created", "report_id": report.id})
```

#### Endpoint API : Lister les signalements (admin)

```python
@app.route("/api/admin/reports", methods=["GET"])
@login_required
def list_reports():
    """Lister tous les signalements (admin uniquement, avec filtres)."""
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    status = request.args.get("status", "all")
    report_type = request.args.get("type", "all")

    query = Report.query
    if status != "all":
        query = query.filter_by(status=status)
    if report_type != "all":
        query = query.filter_by(report_type=report_type)

    reports = query.order_by(Report.created_at.desc()).all()
    return jsonify([{
        "id": r.id,
        "reporter": {"id": r.reporter.id, "name": str(r.reporter)} if r.reporter else None,
        "reported_user": {"id": r.reported_user.id, "name": str(r.reported_user)} if r.reported_user else None,
        "target_item_id": r.target_item_id,
        "report_type": r.report_type,
        "reason": r.reason,
        "description": r.description,
        "status": r.status,
        "reviewed_by": {"id": r.reviewed_by.id, "name": str(r.reviewed_by)} if r.reviewed_by else None,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        "created_at": r.created_at.isoformat()
    } for r in reports])
```

#### Endpoint API : Traiter un signalement (admin)

```python
@app.route("/api/admin/reports/<int:report_id>/resolve", methods=["POST"])
@login_required
def resolve_report(report_id):
    """Clôturer un signalement (reviewed/resolved ou dismissed). Admin uniquement."""
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    report = Report.query.get_or_404(report_id)
    data = request.json
    new_status = data.get("status")  # 'resolved' ou 'dismissed'

    if new_status not in ("resolved", "dismissed"):
        return jsonify({"error": "Statut invalide"}), 400

    report.status = new_status
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.now()

    db.session.commit()
    return jsonify({"status": "updated", "report_id": report.id})
```

#### Template : Formulaire de signalement (`item_detail.html`)

Ajouté en bas du détail d'un item ou à côté du nom d'auteur :

```html
<!-- templates/item_detail.html -->
<div class="report-section">
    <button id="open-report-modal" onclick="document.getElementById('reportModal').style.display='block'">
        🚩 Signaler ce contenu
    </button>

    <div id="reportModal" class="modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999;">
        <div style="max-width:400px; margin:100px auto; padding:20px; background:white; border-radius:8px;">
            <h3>Signaler ce contenu</h3>
            <form id="reportForm" onsubmit="submitReport(event)">
                <select name="reason" required>
                    <option value="">-- Raison --</option>
                    <option value="spam">Spam</option>
                    <option value="contenu_inapproprié">Contenu inapproprié</option>
                    <option value="fake_data">Fake data / Données frauduleuses</option>
                    <option value="other">Autre</option>
                </select>
                <textarea name="description" placeholder="Détails (optionnel)"></textarea>
                <div style="display:flex; gap:10px; margin-top:10px;">
                    <button type="submit">Envoyer le signalement</button>
                    <button type="button" onclick="document.getElementById('reportModal').style.display='none'">Annuler</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
function submitReport(e) {
    e.preventDefault();
    const form = document.getElementById('reportForm');
    const data = {};
    for (let [key, val] of new FormData(form).entries()) {
        data[key] = val;
    }
    data.target_type = "{{ item_type }}";
    data.target_id = {{ item.id }};

    fetch("/api/reports", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    }).then(r => r.json()).then(res => {
        alert("Signalement envoyé avec succès. Merci pour votre vigilance.");
        document.getElementById('reportModal').style.display = 'none';
    });
}
</script>
```

#### Template : Admin — Liste des signalements (`/admin/reports`)

```html
<!-- templates/admin/reports.html -->
<h2>Signalements ({{ reports | length }})</h2>

<nav style="margin-bottom:20px;">
    <a href="/admin/reports?status=all&" {% if status == 'all' %}class="active"{% endif %}>Tous</a>
    <a href="/admin/reports?status=pending" {% if status == 'pending' %}class="active"{% endif %}>En attente ({{ pending_count }})</a>
    <a href="/admin/reports?type=all">Tous les types</a>
    <a href="/admin/reports?type=user">Utilisateurs</a>
    <a href="/admin/reports?type=item_geodonnee">Données</a>
    <a href="/admin/reports?type=item_carte">Cartes</a>
    <a href="/admin/reports?type=item_application">Applications</a>
</nav>

<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>Signaleur</th>
            <th>Cible</th>
            <th>Type</th>
            <th>Raison</th>
            <th>Statut</th>
            <th>Date</th>
            <th>Action</th>
        </tr>
    </thead>
    <tbody>
        {% for report in reports %}
        <tr>
            <td>{{ report.id }}</td>
            <td>{{ report.reporter.prenom }} {{ report.reporter.nom if report.reporter else '(anonyme)' }}</td>
            {% if report.report_type != 'user' %}
                <td><a href="/catalogue/item/{{ report.target_item_id }}">{{ report.target_item.title[:40] if report.target_item and report.target_item.title else '#' }}</a></td>
            {% elif report.reported_user %}
                <td>{{ report.reported_user.prenom }} {{ report.reported_user.nom }}</td>
            {% else %}
                <td>Inconnu</td>
            {% endif %}
            <td>{{ report.report_type }}</td>
            <td>{{ report.reason }}</td>
            <td>
                {% if report.status == 'pending' %}
                    <span class="badge badge-warning">En attente</span>
                {% elif report.status == 'resolved' %}
                    <span class="badge badge-verified">Résolu</span>
                {% elif report.status == 'dismissed' %}
                    <span class="badge badge-pending">Non fondé</span>
                {% else %}
                    {{ report.status }}
                {% endif %}
            </td>
            <td>{{ report.created_at.strftime('%d/%m/%Y') }}</td>
            <td>
                {% if report.status == 'pending' %}
                    <form action="/api/admin/reports/{{ report.id }}/resolve" method="POST">
                        <input type="hidden" name="status" value="resolved">
                        <button type="submit" style="background:#28a745;">Résoudre</button>
                    </form>
                    <form action="/api/admin/reports/{{ report.id }}/resolve" method="POST" style="display:inline;">
                        <input type="hidden" name="status" value="dismissed">
                        <button type="submit" style="background:#6c757d;">Non fondé</button>
                    </form>
                {% else %}
                    —
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

#### Template : Badge de signalement sur un profil utilisateur (`organization_detail.html` ou profil)

Affiché à côté du nom d'un utilisateur signalé (visible par tous, le compte n'est pas banni automatiquement pour montrer la transparence) :

```html
<!-- templates/user_profile.html -->
<div class="user-header">
    <h3>{{ user.prenom }} {{ user.nom }}</h3>
    {% if report_count > 0 %}
        <span class="badge badge-pending" title="{{ report_count }} signalement(s) en attente de traitement.">⚠️ {{ report_count }} signalement{{ 's' if report_count > 1 else '' }}</span>
    {% endif %}
</div>
```

#### Template : Message après envoi de signalement

Un utilisateur ne peut pas se signer lui-même et est notifié par une alerte :

```html
<!-- templates/user_profile.html — affiché si l'utilisateur tente de se signer soi-même -->
{% if self_report_attempt %}
    <div class="alert alert-warning">
        Vous ne pouvez pas signaler votre propre profil. Si vous souhaitez que vos données soient modifiées ou supprimées, contactez l'administration.
    </div>
{% endif %}
```
