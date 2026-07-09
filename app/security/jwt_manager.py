"""Gestion JWT pour l'API."""
import jwt
from datetime import datetime, timedelta
from config import get_config


class JWTManager:
    @staticmethod
    def generate(user_name: str, role: str) -> str:
        cfg = get_config()
        payload = {
            "sub":  user_name,
            "role": role,
            "iat":  datetime.utcnow(),
            "exp":  datetime.utcnow() + timedelta(minutes=cfg.JWT_EXPIRY_MIN),
        }
        return jwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm="HS256")

    @staticmethod
    def verify(token: str) -> dict | None:
        try:
            cfg = get_config()
            return jwt.decode(token, cfg.JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
