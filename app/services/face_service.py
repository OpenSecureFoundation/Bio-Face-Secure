"""
Service enregistrement facial — WebRTC + thread daemon.
Reçoit frames depuis le navigateur, plus de VideoCapture.
"""
import cv2
import os
import time
import base64
import threading
import numpy as np

from app.biometrics.face_encoder   import encode_face
from app.biometrics.face_detector  import detect_faces
from app.repositories.user_repository import add_user, user_exists
from app.repositories.security_repository import add_security_event
from app.security.validators       import sanitize
from app.utils.logger              import get_logger

log = get_logger("face_service")


class RegisterState:
    def __init__(self):
        self.lock     = threading.Lock()
        self.running  = False
        self.done     = False
        self.ok       = False
        self.message  = ""
        self.progress = 0
        self.step_msg = "En attente..."
        self._name    = ""
        self._role    = ""
        self._encoding = None
        self._frame_count = 0
        self._start_t    = None

    def reset(self):
        with self.lock:
            self.running   = False
            self.done      = False
            self.ok        = False
            self.message   = ""
            self.progress  = 0
            self.step_msg  = "En attente..."
            self._name     = ""
            self._role     = ""
            self._encoding = None
            self._frame_count = 0
            self._start_t    = None

    def to_dict(self) -> dict:
        with self.lock:
            return {
                "running":  self.running,
                "done":     self.done,
                "ok":       self.ok,
                "message":  self.message,
                "progress": self.progress,
                "step_msg": self.step_msg,
            }


register_state = RegisterState()


def start_registration(name: str, role: str) -> tuple:
    """Initialise une session d'enregistrement WebRTC."""
    name = sanitize(name)
    if not name or len(name) < 2:
        return False, "Nom invalide (minimum 2 caractères)."
    if len(name) > 50:
        return False, "Nom trop long."
    if user_exists(name):
        return False, f'Le profil "{name}" existe déjà.'

    register_state.reset()
    with register_state.lock:
        register_state.running    = True
        register_state.done       = False
        register_state.progress   = 5
        register_state.step_msg   = "Regardez la caméra..."
        register_state._name      = name
        register_state._role      = role
        register_state._frame_count = 0
        register_state._start_t   = time.time()

    log.info(f"[REGISTER] Session démarrée pour : {name}")
    return True, ""


def process_register_frame(frame_data: str) -> dict:
    """
    Reçoit un frame base64 depuis le navigateur.
    Tente de détecter et encoder le visage.
    """
    with register_state.lock:
        if not register_state.running or register_state.done:
            return register_state.to_dict()
        name      = register_state._name
        role      = register_state._role
        start_t   = register_state._start_t
        encoding  = register_state._encoding

    elapsed = time.time() - start_t

    # Timeout 15 secondes
    if elapsed > 15:
        with register_state.lock:
            register_state.running  = False
            register_state.done     = True
            register_state.ok       = False
            register_state.message  = (
                "Aucun visage capturé en 15 secondes. "
                "Assurez-vous d'être bien éclairé et face à la caméra."
            )
            register_state.progress = 50
            register_state.step_msg = "Timeout"
        return register_state.to_dict()

    # Décoder le frame
    try:
        if ',' in frame_data:
            frame_data = frame_data.split(',')[1]
        img_bytes = base64.b64decode(frame_data)
        np_arr    = np.frombuffer(img_bytes, dtype=np.uint8)
        frame     = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return register_state.to_dict()
    except Exception as e:
        log.warning(f"[REGISTER] Décodage frame : {e}")
        return register_state.to_dict()

    with register_state.lock:
        register_state._frame_count += 1
        frame_count = register_state._frame_count

    # Progression basée sur le temps
    elapsed_pct = min(int(elapsed / 15 * 80), 80)
    prog = max(10, elapsed_pct)

    # Détecter visages
    try:
        locs = detect_faces(frame)
        n    = len(locs)
    except Exception as e:
        log.warning(f"[REGISTER] detect_faces : {e}")
        return register_state.to_dict()

    if n == 0:
        with register_state.lock:
            register_state.progress = prog
            register_state.step_msg = (
                "Aucun visage — approchez-vous de la caméra")
    elif n > 1:
        with register_state.lock:
            register_state.progress = prog
            register_state.step_msg = f"{n} visages — un seul requis"
    else:
        # Tenter encodage
        try:
            enc = encode_face(frame)
        except Exception as e:
            log.warning(f"[REGISTER] encode_face : {e}")
            enc = None

        if enc is not None:
            # Sauvegarde debug
            os.makedirs("instance", exist_ok=True)
            cv2.imwrite("instance/capture_debug.jpg", frame)

            # Sauvegarder en BDD
            ok = add_user(name, role, enc)
            if ok:
                add_security_event(
                    "USER_REGISTERED",
                    f"name={name} role={role}",
                    "INFO", name
                )
                log.info(f"[REGISTER] ✓ {name} enregistré")
                with register_state.lock:
                    register_state.running  = False
                    register_state.done     = True
                    register_state.ok       = True
                    register_state.progress = 100
                    register_state.step_msg = "Terminé ✓"
                    register_state.message  = (
                        f'Profil "{name}" ({role}) enregistré !'
                    )
            else:
                with register_state.lock:
                    register_state.running  = False
                    register_state.done     = True
                    register_state.ok       = False
                    register_state.message  = "Erreur sauvegarde BDD."
                    register_state.step_msg = "Erreur"
        else:
            with register_state.lock:
                register_state.progress = prog
                register_state.step_msg = (
                    f"Visage détecté — encodage... (#{frame_count})")

    return register_state.to_dict()
