"""Point d'entrée BioAuth — accessible sur le réseau local."""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import json

app = create_app()

if __name__ == "__main__":
    import socket
    # Trouver l'IP locale
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "localhost"

    print(f"\n[BioAuth] ══════════════════════════════════════")
    print(f"[BioAuth] Local    : http://127.0.0.1:5000")
    print(f"[BioAuth] Réseau   : http://{local_ip}:5000")
    print(f"[BioAuth] Depuis téléphone : même WiFi requis")
    print(f"[BioAuth] ══════════════════════════════════════\n")

    app.run(
        host="0.0.0.0",    # écoute sur toutes les interfaces
        port=5000,
        debug=False,
        threaded=True,
    )

