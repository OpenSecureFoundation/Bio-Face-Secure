"""Logs d'authentification."""
from app.repositories.user_repository import _conn
from app.models.auth_log_model import AuthLog
from app.utils.helpers import now_time, now_full
from datetime import datetime, timedelta


def add_auth_log(verdict, user_name=None, score=None,
                 liveness_ok=False, attack_type=None, note=None):
    conn = _conn()
    conn.execute(
        "INSERT INTO auth_logs "
        "(timestamp,user_name,verdict,score,liveness_ok,attack_type,note) "
        "VALUES (?,?,?,?,?,?,?)",
        (now_time(), user_name, verdict,
         round(score, 4) if score is not None else None,
         1 if liveness_ok else 0, attack_type, note)
    )
    conn.commit()
    conn.close()


def add_failed_attempt(reason: str):
    conn = _conn()
    conn.execute(
        "INSERT INTO failed_attempts (timestamp,reason) VALUES (?,?)",
        (now_full(), reason)
    )
    conn.commit()
    conn.close()


def get_auth_logs(limit=200) -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM auth_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [AuthLog.from_row(dict(r)) for r in rows]


def get_user_logs(user_name: str, limit=20) -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM auth_logs WHERE user_name=? ORDER BY id DESC LIMIT ?",
        (user_name, limit)
    ).fetchall()
    conn.close()
    return [AuthLog.from_row(dict(r)) for r in rows]


def get_failed_count(minutes=60) -> int:
    conn  = _conn()
    since = (datetime.now() - timedelta(minutes=minutes)).strftime("%d/%m/%Y %H:%M:%S")
    n = conn.execute(
        "SELECT COUNT(*) FROM failed_attempts WHERE timestamp >= ?", (since,)
    ).fetchone()[0]
    conn.close()
    return n


def clear_auth_logs():
    conn = _conn()
    conn.execute("DELETE FROM auth_logs")
    conn.commit()
    conn.close()
