"""Événements de sécurité."""
from app.repositories.user_repository import _conn
from app.models.security_model import SecurityEvent
from app.utils.helpers import now_full


def add_security_event(event_type, details=None,
                       severity="INFO", user_name=None):
    conn = _conn()
    conn.execute(
        "INSERT INTO security_events "
        "(timestamp,event_type,severity,details,user_name) VALUES (?,?,?,?,?)",
        (now_full(), event_type, severity, details, user_name)
    )
    conn.commit()
    conn.close()


def get_security_events(limit=200) -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM security_events ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [SecurityEvent.from_row(dict(r)) for r in rows]


def clear_security_events():
    conn = _conn()
    conn.execute("DELETE FROM security_events")
    conn.commit()
    conn.close()
