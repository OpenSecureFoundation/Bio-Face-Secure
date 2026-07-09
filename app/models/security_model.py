"""Modèle événement de sécurité."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityEvent:
    id:         Optional[int]
    timestamp:  str
    event_type: str
    severity:   str
    details:    Optional[str]
    user_name:  Optional[str]

    @staticmethod
    def from_row(row: dict) -> "SecurityEvent":
        return SecurityEvent(
            id=row.get("id"),
            timestamp=row.get("timestamp", ""),
            event_type=row.get("event_type", ""),
            severity=row.get("severity", "INFO"),
            details=row.get("details"),
            user_name=row.get("user_name"),
        )

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "timestamp":  self.timestamp,
            "event_type": self.event_type,
            "severity":   self.severity,
            "details":    self.details or "—",
            "user_name":  self.user_name or "—",
        }
