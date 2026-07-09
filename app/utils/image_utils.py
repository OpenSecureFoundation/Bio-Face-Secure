"""Utilitaires image — encode JPEG pour stream MJPEG."""
import cv2
import numpy as np


def frame_to_jpeg(frame, quality: int = 75) -> bytes:
    _, buf = cv2.imencode('.jpg', frame,
                          [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


def blank_frame(width=640, height=480, text="Initialisation...") -> bytes:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (11, 32, 57)  # couleur fond dark
    cv2.putText(img, text,
                (width//2 - 120, height//2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 194, 255), 2)
    return frame_to_jpeg(img)


def draw_face_boxes(frame, locations: list) -> None:
    """Dessine les cadres de détection (in-place)."""
    for (top, right, bottom, left) in locations:
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 194, 255), 2)
        s, t, c = 16, 3, (0, 229, 195)
        for x, y, dx, dy in [
            (left, top, 1, 1), (right, top, -1, 1),
            (left, bottom, 1, -1), (right, bottom, -1, -1)
        ]:
            cv2.line(frame, (x, y), (x+dx*s, y), c, t)
            cv2.line(frame, (x, y), (x, y+dy*s), c, t)


def draw_status(frame, text: str, color=(0, 194, 255)) -> None:
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 36), (11, 32, 57), -1)
    cv2.putText(frame, text, (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
