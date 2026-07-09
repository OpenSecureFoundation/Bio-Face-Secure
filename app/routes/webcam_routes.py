"""Stream MJPEG webcam — non bloquant."""
import time
from flask import Blueprint, Response
from app.extensions        import auth_state
from app.utils.image_utils import blank_frame

bp = Blueprint("webcam", __name__, url_prefix="/webcam")


@bp.route("/stream")
def stream():
    """
    Stream MJPEG du flux webcam pendant l'authentification.
    Affiche un placeholder si la caméra n'est pas encore active.
    """
    def generate():
        consecutive_blank = 0
        while True:
            with auth_state.lock:
                frame    = auth_state.frame_jpg
                running  = auth_state.running
                status   = auth_state.status

            if frame:
                consecutive_blank = 0
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame
                    + b"\r\n"
                )
            else:
                consecutive_blank += 1
                text = "Initialisation..." if running else "Caméra inactive"
                blank = blank_frame(text=text)
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + blank
                    + b"\r\n"
                )
                # Si caméra inactive depuis trop longtemps → ralentir
                if consecutive_blank > 30:
                    time.sleep(0.5)
                    continue

            time.sleep(0.04)  # ~25 fps

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
