"""Validation et nettoyage des entrées."""
import re
from config import get_config


ALLOWED_ROLES = ["Utilisateur", "Administrateur", "Invité", "Superviseur"]


def validate_name(name: str) -> tuple:
    cfg = get_config()
    if not name or not name.strip():
        return False, "Le nom est obligatoire."
    name = name.strip()
    if len(name) < cfg.MIN_NAME_LENGTH if hasattr(cfg, 'MIN_NAME_LENGTH') else 2:
        return False, "Nom trop court (minimum 2 caractères)."
    if len(name) > 50:
        return False, "Nom trop long (maximum 50 caractères)."
    if not re.match(r"^[a-zA-ZÀ-ÿ\s'\-]+$", name):
        return False, "Caractères non autorisés."
    return True, ""


def validate_role(role: str) -> tuple:
    if role not in ALLOWED_ROLES:
        return False, f"Rôle invalide. Choisir : {', '.join(ALLOWED_ROLES)}"
    return True, ""


def sanitize(text: str) -> str:
    return (text or "").strip().replace("\x00", "")
