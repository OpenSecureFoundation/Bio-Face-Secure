"""État global authentification — mode WebRTC (sans VideoCapture)."""
import threading
import time
import os
from app.biometrics.anti_spoofing import LivenessDetector, SpoofingDetector


class AuthState:
    def __init__(self):
        self.lock      = threading.Lock()
        self.status    = "idle"
        self.step      = 0
        self.ok        = False
        self.user_name = None
        self.score     = 0.0
        self.reason    = ""
        self.frame_jpg = None
        self.running   = False
        self._session  = None
        # Objets internes du pipeline
        self._liveness = None
        self._spoofing = None
        self._encoding = None
        self._start_t  = None

    def start_pipeline(self):
        """Initialise un nouveau pipeline d'authentification."""
        from app.services.auth_service import AuthPipeline
        with self.lock:
            self.status    = "Démarrage..."
            self.step      = 1
            self.ok        = False
            self.user_name = None
            self.score     = 0.0
            self.reason    = ""
            self.frame_jpg = None
            self.running   = True
            self._liveness = LivenessDetector()
            self._spoofing = SpoofingDetector()
            self._encoding = None
            self._start_t  = time.time()
        self._session = AuthPipeline(self)

    def reset(self):
        with self.lock:
            self.status    = "idle"
            self.step      = 0
            self.ok        = False
            self.user_name = None
            self.score     = 0.0
            self.reason    = ""
            self.frame_jpg = None
            self.running   = False
            self._liveness = None
            self._spoofing = None
            self._encoding = None
            self._start_t  = None
        self._session = None

    def to_dict(self) -> dict:
        with self.lock:
            return {
                "status":    self.status,
                "step":      self.step,
                "ok":        self.ok,
                "user_name": self.user_name,
                "score":     self.score,
                "reason":    self.reason,
            }

    def get_pipeline(self):
        return self._session


# Singleton global
auth_state = AuthState()


def init_directories():
    for d in ["instance", "instance/logs",
              "app/static/uploads", "app/static/webcam"]:
        os.makedirs(d, exist_ok=True)
