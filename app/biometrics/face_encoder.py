"""Encodage facial 128D."""
import cv2
import face_recognition


def encode_face(frame) -> list | None:
    rgb       = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb, model="hog")
    if not locations:
        return None
    encodings = face_recognition.face_encodings(rgb, [locations[0]])
    return encodings[0].tolist() if encodings else None
