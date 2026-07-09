"""Notifications en temps réel via Server-Sent Events."""
import json
import queue
import threading


class NotificationBus:
    """Bus d'événements pour les SSE (Server-Sent Events)."""
    _instance = None

    @classmethod
    def get(cls) -> "NotificationBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._listeners = []
        self._lock      = threading.Lock()

    def subscribe(self) -> queue.Queue:
        q = queue.Queue(maxsize=20)
        with self._lock:
            self._listeners.append(q)
        return q

    def unsubscribe(self, q: queue.Queue):
        with self._lock:
            try:
                self._listeners.remove(q)
            except ValueError:
                pass

    def publish(self, event_type: str, data: dict):
        msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        with self._lock:
            dead = []
            for q in self._listeners:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    dead.append(q)
            for q in dead:
                self._listeners.remove(q)
