import cv2
import threading
import time
from config import get_config


class CameraManager:
    def __init__(self):
        cfg = get_config()
        self._index  = cfg.CAMERA_INDEX
        self._width  = cfg.CAMERA_WIDTH
        self._height = cfg.CAMERA_HEIGHT
        self._fps    = cfg.CAMERA_FPS
        self._cap    = None
        self._lock   = threading.Lock()

    def open(self) -> bool:
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
                time.sleep(0.2)

            # backend principal
            self._cap = cv2.VideoCapture(self._index, cv2.CAP_V4L2)

            # fallback si échec
            if not self._cap.isOpened():
                self._cap = cv2.VideoCapture(self._index)

            if not self._cap.isOpened():
                self._cap.release()
                self._cap = None
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self._width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
            self._cap.set(cv2.CAP_PROP_FPS,          self._fps)

            try:
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except:
                pass

            # warm-up caméra
            for _ in range(10):
                self._cap.read()
                time.sleep(0.03)

            return True

    def read(self):
        with self._lock:
            if self._cap and self._cap.isOpened():
                return self._cap.read()
        return False, None

    def release(self):
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
                time.sleep(0.1)

    def is_open(self) -> bool:
        with self._lock:
            return self._cap is not None and self._cap.isOpened()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.release()
