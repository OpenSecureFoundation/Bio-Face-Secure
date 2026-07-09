"""Service logs + stats dashboard."""
from app.repositories.auth_repository     import (
    get_auth_logs, get_user_logs, get_failed_count, clear_auth_logs
)
from app.repositories.security_repository import (
    get_security_events, clear_security_events, add_security_event
)
from app.repositories.user_repository     import get_user_count


def get_dashboard_stats() -> dict:
    logs   = get_auth_logs(500)
    events = get_security_events(20)

    ok      = sum(1 for l in logs if l.verdict == "ACCORDÉ")
    ko      = sum(1 for l in logs if l.verdict == "REFUSÉ")
    attacks = sum(1 for l in logs
                  if l.verdict == "ATTAQUE" or
                  (l.attack_type and l.attack_type not in ("—", None, "")))

    # 10 logs récents sérialisés
    recent_logs = []
    for l in get_auth_logs(10):
        recent_logs.append({
            "timestamp":   l.timestamp,
            "verdict":     l.verdict,
            "user_name":   l.user_name or "—",
            "score":       l.score,
            "liveness_ok": l.liveness_ok,
            "attack_type": l.attack_type or "—",
            "note":        l.note or "—",
        })

    # 10 événements sécurité récents sérialisés
    recent_events = []
    for e in events:
        recent_events.append({
            "timestamp":  e.timestamp,
            "event_type": e.event_type,
            "severity":   e.severity,
            "user_name":  e.user_name or "—",
            "details":    e.details or "—",
        })

    return {
        "total_users":    get_user_count(),
        "total_auth":     len(logs),
        "success":        ok,
        "failed":         ko,
        "attacks":        attacks,
        "failed_recent":  get_failed_count(60),
        "recent_logs":    recent_logs,
        "recent_events":  recent_events,
    }


def get_all_auth_logs(limit=200):
    return [l.to_dict() for l in get_auth_logs(limit)]


def get_all_security_events(limit=200):
    return [e.to_dict() for e in get_security_events(limit)]


def get_my_logs(user_name: str, limit=10):
    return [l.to_dict() for l in get_user_logs(user_name, limit)]


def purge_auth(admin: str = "system"):
    clear_auth_logs()
    add_security_event("PURGE_AUTH_LOGS", f"by={admin}", "INFO", admin)


def purge_security(admin: str = "system"):
    clear_security_events()
    add_security_event("PURGE_SEC_LOGS", f"by={admin}", "INFO", admin)
