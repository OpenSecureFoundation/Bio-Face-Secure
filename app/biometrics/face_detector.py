"""Détection de visages — headless."""
import cv2
import face_recognition


def detect_faces(frame) -> list:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return face_recognition.face_locations(rgb, model="hog")


def get_landmarks(frame) -> dict | None:
    rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locs = face_recognition.face_locations(rgb)
    if not locs:
        return None
    marks = face_recognition.face_landmarks(rgb, locs)
    return marks[0] if marks else None


def face_count(frame) -> int:
    return len(detect_faces(frame))
