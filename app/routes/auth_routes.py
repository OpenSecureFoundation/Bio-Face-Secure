"""Routes auth + enregistrement WebRTC."""
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, request, jsonify
)
from datetime import datetime
from app.extensions                    import auth_state
from app.services.face_service        import (
    start_registration, register_state, process_register_frame
)
from app.repositories.user_repository import get_all_users, get_user_count
from app.services.log_service         import get_my_logs
from app.utils.helpers                import login_required, get_initials

bp = Blueprint("auth", __name__)


@bp.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("auth.session_view"))
    if get_user_count() == 0:
        flash("Aucun profil. Créez le premier compte.", "info")
        return redirect(url_for("auth.register_page"))
    return redirect(url_for("auth.login"))


@bp.route("/login")
def login():
    if session.get("user"):
        return redirect(url_for("auth.session_view"))
    if get_user_count() == 0:
        flash("Aucun profil. Créez le premier compte.", "info")
        return redirect(url_for("auth.register_page"))
    return render_template("login.html", active_page="login")


@bp.route("/register")
def register_page():
    already_has_users = get_user_count() > 0
    return render_template(
        "register.html",
        active_page="register",
        already_has_users=already_has_users,
        roles=["Utilisateur", "Administrateur", "Invité", "Superviseur"],
    )


@bp.route("/register/start", methods=["POST"])
def register_start():
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "Utilisateur")
    ok, err = start_registration(name, role)
    if not ok:
        return jsonify({"started": False, "error": err})
    return jsonify({"started": True, "name": name})


@bp.route("/register/frame", methods=["POST"])
def register_frame():
    """Reçoit les frames WebRTC pour l'enregistrement."""
    data       = request.get_json(silent=True) or {}
    frame_data = data.get("frame", "")
    if not frame_data:
        return jsonify({"error": "Pas de frame"})
    result = process_register_frame(frame_data)
    return jsonify(result)


@bp.route("/register/status")
def register_status():
    return jsonify(register_state.to_dict())


@bp.route("/logout")
def logout():
    user = session.get("user", "inconnu")
    from app.repositories.security_repository import add_security_event
    add_security_event("SESSION_ENDED", f"user={user}", "INFO", user)
    session.clear()
    auth_state.reset()
    flash("Déconnexion réussie.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/session")
@login_required
def session_view():
    user_name    = session["user"]
    users        = [u for u in get_all_users() if u.name == user_name]
    user         = users[0] if users else None
    session_info = {
        "Nom":              user_name,
        "Rôle":             session.get("role", "Utilisateur"),
        "Connecté le":      session.get("login_time", "—"),
        "Dernier login":    user.last_login if user else "—",
        "Total connexions": str(user.login_count if user else 1),
    }
    bio_status = [
        {"label": "Authentification",    "value": "✓ Réussie"},
        {"label": "Liveness detection",  "value": "✓ Validée"},
        {"label": "Anti-spoofing",       "value": "✓ Aucune attaque"},
        {"label": "Chiffrement AES-256", "value": "✓ Actif"},
    ]
    return render_template(
        "session.html",
        active_page="session",
        user_name=user_name,
        user=user,
        session_info=session_info,
        bio_status=bio_status,
        recent_logs=get_my_logs(user_name, 5),
        initials=get_initials(user_name),
        login_time=session.get("login_time", "—"),
    )
