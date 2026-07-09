"""
Anti-spoofing + Liveness detection — calibré pour usage réel.
EAR=0.22, seuils photo/vidéo stricts pour éviter faux positifs.
"""
import cv2
import numpy as np
from scipy.spatial import distance as dist
from app.biometrics.face_detector import get_landmarks
from app.utils.logger import get_logger

log = get_logger("anti_spoofing")


def _ear(eye) -> float:
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C) if C > 0.001 else 0.3


class LivenessDetector:
    def __init__(self):
        self.ear_threshold = 0.22
        self.blink_frames  = 1
        self.head_px       = 12
        self.score         = 0
        self.validated     = False
        self.frames_low    = 0
        self.blink_count   = 0
        self.nose_hist     = []
        self.ear_history   = []
        self.frame_count   = 0
        self.msg           = "Clignez des yeux ou bougez légèrement la tête"
        log.info("[LIVENESS] Initialisé — EAR seuil=0.22")

    def reset(self):
        self.__init__()

    def process(self, frame) -> str:
        if self.validated:
            return self.msg

        self.frame_count += 1
        lm = get_landmarks(frame)

        if lm is None:
            self.msg = "Centrez votre visage..."
            return self.msg

        # ── EAR clignement ───────────────────────────────
        left  = [(p[0], p[1]) for p in lm.get("left_eye",  [])]
        right = [(p[0], p[1]) for p in lm.get("right_eye", [])]

        if len(left) == 6 and len(right) == 6:
            ear = (_ear(left) + _ear(right)) / 2.0
            self.ear_history.append(ear)

            if self.frame_count % 15 == 0:
                log.info(
                    f"[LIVENESS] frame={self.frame_count} "
                    f"EAR={ear:.3f} score={self.score} "
                    f"blinks={self.blink_count}"
                )

            if ear < self.ear_threshold:
                self.frames_low += 1
            else:
                if self.frames_low >= self.blink_frames:
                    self.blink_count += 1
                    self.score = max(self.score, 1)
                    log.info(
                        f"[LIVENESS] ✓ Clignement #{self.blink_count} "
                        f"EAR={ear:.3f}"
                    )
                    self.msg = f"Clignement ✓ ({self.blink_count})"
                self.frames_low = 0

        # ── Mouvement de tête ────────────────────────────
        nose = lm.get("nose_tip", [])
        if nose:
            nx = nose[len(nose)//2][0]
            self.nose_hist.append(nx)
            if len(self.nose_hist) > 30:
                self.nose_hist.pop(0)
            if len(self.nose_hist) >= 10:
                variation = max(self.nose_hist) - min(self.nose_hist)
                if variation >= self.head_px:
                    self.score = max(self.score, 1)
                    if self.blink_count == 0:
                        log.info(
                            f"[LIVENESS] ✓ Mouvement tête {variation:.1f}px"
                        )
                        self.msg = "Mouvement tête ✓"

        # ── Validation ───────────────────────────────────
        if self.score >= 1:
            self.validated = True
            self.msg = "Vivacité confirmée ✓"
            log.info(
                f"[LIVENESS] ✓ VALIDÉE score={self.score} "
                f"blinks={self.blink_count} frames={self.frame_count}"
            )
        return self.msg


class SpoofingDetector:
    """
    Détecte photo statique et vidéo rejouée.
    Seuils calibrés pour éviter les faux positifs sur visage réel.
    Confidence >= 0.75 requise (strict) pour déclarer attaque.
    """

    def __init__(self):
        self._frames       = []
        self._variance_log = []
        self._frame_count  = 0
        self._warmup       = 15   # frames d'échauffement avant analyse

    def reset(self):
        self.__init__()

    def analyze(self, frame) -> dict:
        self._frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self._frames.append(gray.copy())
        if len(self._frames) > 25:
            self._frames.pop(0)

        # Période de chauffe — pas d'analyse
        if self._frame_count < self._warmup:
            return {"is_attack": False, "reason": "Chauffe...",
                    "confidence": 0.0}

        # Luminosité insuffisante
        mean_lum = float(np.mean(gray))
        if mean_lum < 20:
            return {"is_attack": False,
                    "reason": "Éclairage insuffisant",
                    "confidence": 0.0}

        signals     = []
        confidence  = 0.0

        # ── Netteté (Laplacien) ──────────────────────────
        lap = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if lap < 25:
            signals.append(f"Image trop plate (lap={lap:.1f})")
            confidence += 0.35

        # ── Variance temporelle ──────────────────────────
        if len(self._frames) >= 8:
            stack = np.stack(
                [f.astype(np.float32) for f in self._frames[-8:]], axis=0
            )
            t_var = float(np.var(stack, axis=0).mean())
            self._variance_log.append(t_var)

            # Photo statique : variance quasi nulle
            if t_var < 3.0:
                signals.append(f"Variance nulle (t_var={t_var:.2f})")
                confidence += 0.40

            # Vidéo rejouée : variance très régulière
            if len(self._variance_log) >= 15:
                v_of_v = float(np.var(self._variance_log[-15:]))
                if v_of_v < 0.15 and t_var < 8.0:
                    signals.append(
                        f"Mouvement périodique (v={v_of_v:.3f})"
                    )
                    confidence += 0.30

        confidence = min(confidence, 1.0)

        # Seuil strict : 0.75 pour déclarer attaque
        is_attack = confidence >= 0.75

        if is_attack:
            log.warning(
                f"[SPOOFING] Attaque détectée conf={confidence:.2f} : "
                f"{' | '.join(signals)}"
            )

        return {
            "is_attack":  is_attack,
            "reason":     " | ".join(signals) if signals else "OK",
            "confidence": round(confidence, 2),
        }
