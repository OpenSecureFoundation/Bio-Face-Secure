"""Modèle utilisateur."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id:          Optional[int]
    name:        str
    role:        str
    encoding:    Optional[bytes]  # Chiffré AES-256
    created_at:  Optional[str]
    updated_at:  Optional[str]
    active:      bool
    login_count: int
    last_login:  Optional[str]

    @staticmethod
    def from_row(row: dict) -> "User":
        return User(
            id=row.get("id"),
            name=row.get("name", ""),
            role=row.get("role", "Utilisateur"),
            encoding=row.get("encoding"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            active=bool(row.get("active", 1)),
            login_count=row.get("login_count", 0) or 0,
            last_login=row.get("last_login"),
        )

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "name":        self.name,
            "role":        self.role,
            "created_at":  self.created_at,
            "updated_at":  self.updated_at,
            "active":      self.active,
            "login_count": self.login_count,
            "last_login":  self.last_login,
        }
