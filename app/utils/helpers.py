"""Fonctions utilitaires — décorateurs + helpers."""
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash


def now_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def now_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def now_full() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            flash("Veuillez vous authentifier pour accéder à cette page.",
                  "info")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            flash("Accès refusé — connexion requise.", "danger")
            return redirect(url_for("auth.login"))
        if session.get("role") not in ["Administrateur", "Superviseur"]:
            flash("Accès réservé aux administrateurs.", "danger")
            return redirect(url_for("auth.session_view"))
        return f(*args, **kwargs)
    return wrapper


def get_initials(name: str) -> str:
    parts = (name or "").split()
    return "".join(p[0].upper() for p in parts[:2]) or "?"
