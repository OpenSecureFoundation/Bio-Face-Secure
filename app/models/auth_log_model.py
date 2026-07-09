"""Modèle log d'authentification."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthLog:
    id:          Optional[int]
    timestamp:   str
    user_name:   Optional[str]
    verdict:     str
    score:       Optional[float]
    liveness_ok: bool
    attack_type: Optional[str]
    note:        Optional[str]

    @staticmethod
    def from_row(row: dict) -> "AuthLog":
        return AuthLog(
            id=row.get("id"),
            timestamp=row.get("timestamp", ""),
            user_name=row.get("user_name"),
            verdict=row.get("verdict", ""),
            score=row.get("score"),
            liveness_ok=bool(row.get("liveness_ok", 0)),
            attack_type=row.get("attack_type"),
            note=row.get("note"),
        )

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "timestamp":   self.timestamp,
            "user_name":   self.user_name or "—",
            "verdict":     self.verdict,
            "score":       round(self.score * 100, 1) if self.score else None,
            "liveness_ok": self.liveness_ok,
            "attack_type": self.attack_type or "—",
            "note":        self.note or "—",
        }
