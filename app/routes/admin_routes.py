"""Routes administration."""
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, request, jsonify
)
from app.utils.helpers         import login_required
from app.repositories.user_repository import (
    get_all_users, delete_user, set_active, update_role
)
from app.services.face_service import start_registration, register_state
from app.services.log_service  import (
    get_all_auth_logs, get_all_security_events,
    purge_auth, purge_security
)
from app.repositories.security_repository import add_security_event

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard")
@login_required
def dashboard():
    system_status = [
        {"label": "Chiffrement AES-256",  "value": "✓ Actif"},
        {"label": "Base de données",      "value": "✓ Connectée"},
        {"label": "Liveness detection",   "value": "✓ Activée"},
        {"label": "Journalisation",       "value": "✓ Active"},
        {"label": "Webcam V4L2",          "value": "✓ Configurée"},
        {"label": "Rate limiter",         "value": "✓ Actif"},
    ]
    return render_template("dashboard.html",
                           active_page="dashboard",
                           system_status=system_status)


@bp.route("/users")
@login_required
def users():
    return render_template(
        "users.html",
        active_page="users",
        users=get_all_users(),
        roles=["Utilisateur", "Administrateur", "Invité", "Superviseur"],
    )


# ── Enregistrement depuis le panel admin (même pipeline non bloquant) ──
@bp.route("/users/register/start", methods=["POST"])
@login_required
def users_register_start():
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "Utilisateur")
    ok, err = start_registration(name, role)
    if not ok:
        return jsonify({"started": False, "error": err})
    return jsonify({"started": True, "name": name})


@bp.route("/users/register/status")
@login_required
def users_register_status():
    return jsonify(register_state.to_dict())


@bp.route("/users/<int:uid>/delete", methods=["POST"])
@login_required
def users_delete(uid):
    delete_user(uid)
    add_security_event(
        "DELETE_USER",
        f"uid={uid} by={session['user']}",
        "INFO", session["user"]
    )
    flash("Utilisateur supprimé.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:uid>/toggle", methods=["POST"])
@login_required
def users_toggle(uid):
    all_users = get_all_users()
    target    = next((u for u in all_users if u.id == uid), None)
    if target:
        new_state = not target.active
        set_active(uid, new_state)
        add_security_event(
            "TOGGLE_USER",
            f"uid={uid} active={new_state} by={session['user']}",
            "INFO", session["user"]
        )
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:uid>/role", methods=["POST"])
@login_required
def users_role(uid):
    role = request.form.get("role", "Utilisateur")
    update_role(uid, role)
    add_security_event(
        "EDIT_ROLE",
        f"uid={uid} role={role} by={session['user']}",
        "INFO", session["user"]
    )
    return redirect(url_for("admin.users"))


@bp.route("/logs")
@login_required
def logs():
    return render_template(
        "logs.html",
        active_page="logs",
        auth_logs=get_all_auth_logs(200),
        sec_events=get_all_security_events(200),
    )


@bp.route("/logs/clear-auth", methods=["POST"])
@login_required
def logs_clear_auth():
    purge_auth(session["user"])
    flash("Journal d'authentification vidé.", "success")
    return redirect(url_for("admin.logs"))


@bp.route("/logs/clear-security", methods=["POST"])
@login_required
def logs_clear_security():
    purge_security(session["user"])
    flash("Journal de sécurité vidé.", "success")
    return redirect(url_for("admin.logs"))


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        updates = {
            "SIMILARITY_THRESHOLD":   request.form.get("SIMILARITY_THRESHOLD", "0.50"),
            "LIVENESS_EAR_THRESHOLD": request.form.get("LIVENESS_EAR_THRESHOLD", "0.25"),
            "LIVENESS_TIMEOUT_SEC":   request.form.get("LIVENESS_TIMEOUT_SEC", "10"),
            "MAX_LOGIN_ATTEMPTS":     request.form.get("MAX_LOGIN_ATTEMPTS", "3"),
            "ANTI_SPOOFING_ENABLED":  "True" if "anti_spoofing" in request.form else "False",
            "AUDIT_ENABLED":          "True" if "audit_enabled" in request.form else "False",
        }
        try:
            lines = []
            with open(".env") as f:
                for line in f:
                    key = line.split("=")[0].strip()
                    if key in updates:
                        lines.append(f"{key}={updates.pop(key)}\n")
                    else:
                        lines.append(line)
            for k, v in updates.items():
                lines.append(f"{k}={v}\n")
            with open(".env", "w") as f:
                f.writelines(lines)
            add_security_event(
                "CONFIG_UPDATE",
                f"by={session['user']}",
                "INFO", session["user"]
            )
            flash("Configuration sauvegardée.", "success")
        except Exception as e:
            flash(f"Erreur : {e}", "danger")
        return redirect(url_for("admin.settings"))

    from dotenv import dotenv_values
    env = dotenv_values(".env")
    return render_template("settings.html", active_page="settings", env=env)
