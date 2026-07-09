"""API JSON — WebRTC auth + dashboard."""
from flask import Blueprint, jsonify, session, request
from app.extensions            import auth_state
from app.services.log_service  import get_dashboard_stats
from app.security.rate_limiter import RateLimiter
from config import get_config

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/auth/start", methods=["POST"])
def auth_start():
    cfg = get_config()
    rl  = RateLimiter.get()
    key = "auth_global"

    if rl.is_blocked(key, cfg.MAX_LOGIN_ATTEMPTS, 5):
        return jsonify({
            "locked":  True,
            "message": "Trop de tentatives. Attendez 5 minutes."
        })
    rl.record(key)

    auth_state.reset()
    auth_state.start_pipeline()
    return jsonify({"locked": False, "started": True})


@bp.route("/auth/frame", methods=["POST"])
def auth_frame():
    """
    Reçoit un frame base64 depuis le navigateur (WebRTC).
    Traite et retourne le statut.
    """
    if not auth_state.running:
        return jsonify(auth_state.to_dict())

    data = request.get_json(silent=True) or {}
    frame_data = data.get("frame", "")

    if not frame_data:
        return jsonify({"error": "Pas de frame"})

    pipeline = auth_state.get_pipeline()
    if pipeline is None:
        return jsonify(auth_state.to_dict())

    result = pipeline.process_frame(frame_data)

    # Créer session Flask si auth réussie
    d = auth_state.to_dict()
    if d["status"] == "done" and d["ok"] and d["user_name"]:
        if not session.get("user"):
            from datetime import datetime
            from app.repositories.user_repository import get_all_users
            from app.repositories.security_repository import add_security_event
            session["user"]       = d["user_name"]
            session["login_time"] = datetime.now().strftime(
                "%d/%m/%Y à %H:%M:%S")
            users = [u for u in get_all_users()
                     if u.name == d["user_name"]]
            session["role"] = users[0].role if users else "Utilisateur"
            add_security_event(
                "SESSION_STARTED",
                f"user={d['user_name']}",
                "INFO", d["user_name"]
            )
    return jsonify(d)


@bp.route("/auth/status")
def auth_status():
    return jsonify(auth_state.to_dict())


@bp.route("/auth/stop", methods=["POST"])
def auth_stop():
    auth_state.reset()
    return jsonify({"stopped": True})


@bp.route("/dashboard/stats")
def dashboard_stats():
    return jsonify(get_dashboard_stats())


@bp.route("/health")
def health():
    from app.repositories.user_repository import get_user_count
    return jsonify({
        "status":  "ok",
        "version": "1.0.0",
        "users":   get_user_count(),
        "mode":    "WebRTC",
    })
