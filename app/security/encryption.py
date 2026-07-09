"""Chiffrement AES-256 via Fernet — Singleton."""
import os, pickle
from cryptography.fernet import Fernet
from config import get_config


class EncryptionService:
    _instance = None

    @classmethod
    def get(cls) -> "EncryptionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        path = get_config().ENCRYPTION_KEY_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            key = Fernet.generate_key()
            with open(path, "wb") as f:
                f.write(key)
            os.chmod(path, 0o600)
        with open(path, "rb") as f:
            self._fernet = Fernet(f.read())

    def encrypt(self, data: object) -> bytes:
        return self._fernet.encrypt(pickle.dumps(data))

    def decrypt(self, token: bytes) -> object:
        return pickle.loads(self._fernet.decrypt(token))
