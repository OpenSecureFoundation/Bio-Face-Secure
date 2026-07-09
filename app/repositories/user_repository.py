"""CRUD utilisateurs — BDD SQLite."""
import sqlite3, os
from config import get_config
from app.models.user_model import User
from app.security.encryption import EncryptionService
from app.utils.helpers import now_str


def _conn():
    cfg  = get_config()
    path = cfg.DATABASE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_tables():
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            role        TEXT    DEFAULT 'Utilisateur',
            encoding    BLOB    NOT NULL,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT,
            active      INTEGER DEFAULT 1,
            login_count INTEGER DEFAULT 0,
            last_login  TEXT
        );
        CREATE TABLE IF NOT EXISTS auth_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            user_name   TEXT,
            verdict     TEXT    NOT NULL,
            score       REAL,
            liveness_ok INTEGER DEFAULT 0,
            attack_type TEXT,
            note        TEXT
        );
        CREATE TABLE IF NOT EXISTS security_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            event_type  TEXT    NOT NULL,
            severity    TEXT    DEFAULT 'INFO',
            details     TEXT,
            user_name   TEXT
        );
        CREATE TABLE IF NOT EXISTS failed_attempts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            reason      TEXT
        );
    """)
    conn.commit()
    conn.close()
    print("[DB] Tables initialisées.")


def add_user(name: str, role: str, encoding: list) -> bool:
    try:
        enc = EncryptionService.get().encrypt(encoding)
        conn = _conn()
        conn.execute(
            "INSERT INTO users (name,role,encoding,created_at) VALUES (?,?,?,?)",
            (name, role, enc, now_str())
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_all_users() -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT id,name,role,created_at,updated_at,active,"
        "login_count,last_login FROM users ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [User.from_row(dict(r)) for r in rows]


def get_active_encodings() -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT name,encoding FROM users WHERE active=1"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        try:
            enc = EncryptionService.get().decrypt(r["encoding"])
            result.append((r["name"], enc))
        except Exception:
            pass
    return result


def get_user_by_name(name: str):
    conn = _conn()
    row  = conn.execute(
        "SELECT * FROM users WHERE name=?", (name,)
    ).fetchone()
    conn.close()
    return User.from_row(dict(row)) if row else None


def user_exists(name: str) -> bool:
    return get_user_by_name(name) is not None


def delete_user(uid: int):
    conn = _conn()
    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit()
    conn.close()


def set_active(uid: int, active: bool):
    conn = _conn()
    conn.execute("UPDATE users SET active=? WHERE id=?",
                 (1 if active else 0, uid))
    conn.commit()
    conn.close()


def update_role(uid: int, role: str):
    conn = _conn()
    conn.execute("UPDATE users SET role=?,updated_at=? WHERE id=?",
                 (role, now_str(), uid))
    conn.commit()
    conn.close()


def update_last_login(name: str):
    conn = _conn()
    conn.execute(
        "UPDATE users SET last_login=?,login_count=login_count+1 WHERE name=?",
        (now_str(), name)
    )
    conn.commit()
    conn.close()


def get_user_count() -> int:
    conn = _conn()
    n = conn.execute(
        "SELECT COUNT(*) FROM users WHERE active=1"
    ).fetchone()[0]
    conn.close()
    return n
