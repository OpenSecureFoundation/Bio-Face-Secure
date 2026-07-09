"""Gestion des permissions par rôle."""

PERMISSIONS = {
    "Invité":         ["view_session"],
    "Utilisateur":    ["view_session", "view_history"],
    "Superviseur":    ["view_session", "view_history", "view_logs", "view_users"],
    "Administrateur": ["view_session", "view_history", "view_logs",
                       "view_users", "manage_users", "manage_settings",
                       "clear_logs"],
}


def has_permission(role: str, permission: str) -> bool:
    return permission in PERMISSIONS.get(role, [])


def get_permissions(role: str) -> list:
    return PERMISSIONS.get(role, [])
