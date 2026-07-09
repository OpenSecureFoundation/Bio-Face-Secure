"""
Pipeline d'authentification — mode WebRTC.
Les frames arrivent du navigateur (JS), plus d'OpenCV VideoCapture.
Compatible : téléphone, laptop, tablette — chacun utilise SA caméra.
"""
import threading
import time
import cv2
import numpy as np
import base64

from app.biometrics.face_encoder      import encode_face
from app.biometrics.anti_spoofing     import LivenessDetector, SpoofingDetector
from app.biometrics.recognition_engine import compare
from app.repositories.user_repository import get_active_encodings, update_last_login
from app.repositories.auth_repository import add_auth_log, add_failed_attempt
from app.repositories.security_repository import add_security_event
from app.utils.image_utils            import frame_to_jpeg, draw_face_boxes, draw_status
from app.biometrics.face_detector     import detect_faces
from app.utils.logger                 import get_logger
from config                           import get_config

log = get_logger("auth_service")

LIVENESS_TIMEOUT = 30


class AuthPipeline:
    """
    Pipeline d'authentification — reçoit les frames depuis le navigateur.
    Pas de VideoCapture : la caméra est gérée par JavaScript (WebRTC).
    """

    def __init__(self, state):
        self._state    = state
        self._lock     = threading.Lock()

    def stop(self):
        with self._state.lock:
            self._state.running = False

    def _set(self, **kw):
        with self._state.lock:
            for k, v in kw.items():
                setattr(self._state, k, v)

    def _push_frame(self, frame):
        jpg = frame_to_jpeg(frame, quality=72)
        with self._state.lock:
            self._state.frame_jpg = jpg

    def _done(self, name, score, ok, reason):
        with self._state.lock:
            self._state.user_name = name
            self._state.score     = score
            self._state.ok        = ok
            self._state.reason    = reason
            self._state.status    = "done"
            self._state.step      = 5
            self._state.running   = False

    def process_frame(self, frame_data: str) -> dict:
        """
        Reçoit un frame en base64 depuis le navigateur.
        Traite et retourne le statut courant.
        Appelé depuis l'API /api/auth/frame (POST).
        """
        with self._state.lock:
            if not self._state.running or self._state.status == "done":
                return self._state.to_dict() if hasattr(self._state, 'to_dict') else {}

        # ── Décoder le frame base64 ──────────────────────
        try:
            if ',' in frame_data:
                frame_data = frame_data.split(',')[1]
            img_bytes = base64.b64decode(frame_data)
            np_arr    = np.frombuffer(img_bytes, dtype=np.uint8)
            frame     = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None:
                return {"error": "frame invalide"}
        except Exception as e:
            log.warning(f"Décodage frame : {e}")
            return {"error": str(e)}

        with self._state.lock:
            liveness = self._state._liveness
            spoofing = self._state._spoofing
            encoding = self._state._encoding
            start_t  = self._state._start_t

        elapsed = time.time() - start_t
        cfg     = get_config()

        # ── Overlay visuel ───────────────────────────────
        display = frame.copy()
        locs    = detect_faces(frame)
        draw_face_boxes(display, locs)
        with self._state.lock:
            cur_status = self._state.status
        draw_status(display, cur_status)
        self._push_frame(display)

        # ── Étape 1 : Encoder ────────────────────────────
        if encoding is None and len(locs) > 0:
            enc = encode_face(frame)
            if enc is not None:
                with self._state.lock:
                    self._state._encoding = enc
                encoding = enc
                self._set(
                    status="Visage encodé ✓ — Clignez des yeux !",
                    step=2
                )
                log.info(f"Visage encodé ({elapsed:.1f}s)")

        # ── Étape 2 : Liveness + Anti-spoofing ───────────
        if encoding is not None:
            if cfg.ANTI_SPOOFING_ENABLED:
                atk = spoofing.analyze(frame)
                if atk["is_attack"]:
                    reason = atk["reason"]
                    add_auth_log("ATTAQUE", None, 0.0, False, reason)
                    add_failed_attempt("Spoofing : " + reason)
                    add_security_event("ATTACK", reason, "CRITICAL")
                    self._done(None, 0.0, False,
                               "Attaque détectée : " + reason)
                    log.warning(f"Spoofing : {reason}")
                    return self._state.to_dict()

            msg = liveness.process(frame)
            self._set(status=msg, step=3)

            if liveness.validated:
                # ── Étape 3 : Comparaison BDD ────────────
                self._set(status="Comparaison BDD...", step=4)
                stored      = get_active_encodings()
                name, score = compare(encoding, stored)

                log.info(
                    f"Comparaison : name={name} score={score:.1f}% "
                    f"profils={len(stored)}"
                )

                if name:
                    update_last_login(name)
                    add_auth_log("ACCORDÉ", name, score/100, True)
                    add_security_event(
                        "AUTH_SUCCESS",
                        f"user={name} score={score:.1f}%",
                        "INFO", name
                    )
                    log.info(f"✓ AUTH_SUCCESS {name} {score:.1f}%")
                    self._done(name, score, True, "")
                else:
                    msg_fail = (
                        f"Profil non reconnu (score={score:.1f}%). "
                        f"{len(stored)} profil(s) en base."
                    )
                    add_auth_log("REFUSÉ", None, score/100, True,
                                 note="Profil inconnu")
                    add_failed_attempt("Profil inconnu")
                    add_security_event("AUTH_FAILURE",
                                       f"score={score:.1f}%", "WARNING")
                    log.warning(f"✗ AUTH_FAILURE score={score:.1f}%")
                    self._done(None, score, False, msg_fail)

                return self._state.to_dict()

        # ── Timeout liveness ─────────────────────────────
        if elapsed > LIVENESS_TIMEOUT and encoding is not None:
            add_auth_log("REFUSÉ", None, 0.0, False, note="Timeout")
            add_failed_attempt("Timeout liveness")
            self._done(
                None, 0.0, False,
                f"Timeout ({LIVENESS_TIMEOUT}s) — Clignez des yeux."
            )
            log.warning(f"Timeout liveness {elapsed:.1f}s")
            return self._state.to_dict()

        # Message d'aide
        if elapsed > 4 and encoding is None:
            self._set(status="Approchez et centrez votre visage")

        return self._state.to_dict()
