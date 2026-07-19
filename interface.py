import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import sys

# Importation de nos modules logiques (Modèle/Contrôleur)
try:
    from database import initialiser_bdd
    from main import authentifier_utilisateur, verifier_vivacite
except ImportError:
    print("[ATTENTION] Modules logiques manquants ou en cours de compilation.")

class BioFaceSecureApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Bio-Face-Secure v1.0 — SSI Master Project")
        self.window.geometry("900x650")
        self.window.configure(bg="#2c3e50")
        
        self.video_flux = None
        self.flux_actif = False

        # Style des composants
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.creer_widgets()
        
        # Initialisation de la caméra
        self.demarrer_webcam()

    def creer_widgets(self):
        # 1. Titre Principal
        titre = tk.Label(
            self.window, 
            text="SYSTÈME D'AUTHENTIFICATION BIOMÉTRIQUE SÉCURISÉ",
            font=("Helvetica", 16, "bold"),
            fg="#ecf0f1",
            bg="#2c3e50",
            pady=15
        )
        titre.pack()

        # 2. Zone d'affichage de la Vidéo (Aperçu de la caméra)
        self.video_label = tk.Label(self.window, bg="#34495e", width=640, height=480)
        self.video_label.pack(pady=10)

        # 3. Zone des Messages / Statut (Exigence d'affichage explicite)
        self.status_frame = tk.Frame(self.window, bg="#2c3e50")
        self.status_frame.pack(fill="x",有用pady=5)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Système prêt. En attente d'une action...",
            font=("Helvetica", 12, "italic"),
            fg="#bdc3c7",
            bg="#2c3e50"
        )
        self.status_label.pack()

        # 4. Barre de boutons (Actions BF1 et BF3)
        btn_frame = tk.Frame(self.window, bg="#2c3e50")
        btn_frame.pack(pady=15)

        btn_auth = tk.Button(
            btn_frame, text="S'AUTHENTIFIER (BF1)", font=("Helvetica", 11, "bold"),
            bg="#27ae60", fg="white", padx=20, pady=10, relief="flat",
            command=self.declencher_authentification
        )
        btn_auth.grid(row=0, column=0, padx=15)

        btn_enroll = tk.Button(
            btn_frame, text="S'ENRÔLER (BF3)", font=("Helvetica", 11, "bold"),
            bg="#2980b9", fg="white", padx=20, pady=10, relief="flat",
            command=self.declencher_enrolement
        )
        btn_enroll.grid(row=0, column=1, padx=15)

        btn_quitter = tk.Button(
            btn_frame, text="Quitter", font=("Helvetica", 11),
            bg="#c0392b", fg="white", padx=15, pady=10, relief="flat",
            command=self.quitter_application
        )
        btn_quitter.grid(row=0, column=2, padx=15)

    def demarrer_webcam(self):
        self.video_flux = cv2.VideoCapture(0)
        if not self.video_flux.isOpened():
            self.mettre_a_jour_statut("Erreur : Impossible d'ouvrir la webcam.", "#e74c3c")
            return
        self.flux_actif = True
        self.mettre_a_jour_flux()

    def mettre_a_jour_flux(self):
        if self.flux_actif:
            ret, frame = self.video_flux.read()
            if ret:
                # Convertir l'image BGR d'OpenCV en RGB pour Tkinter
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            self.window.after(10, self.mettre_a_jour_flux)

    def mettre_a_jour_statut(self, message, couleur="#ecf0f1"):
        self.status_label.config(text=message, fg=couleur)
        self.window.update_idletasks()

    def declencher_authentification(self):
        self.mettre_a_jour_statut("Vérification de vivacité en cours... Répondez au défi !", "#f1c40f")
        
        # Exécution dans un thread séparé pour éviter de figer l'interface Tkinter
        def thread_auth():
            reussite = authentifier_utilisateur(self.video_flux)
            if reussite:
                self.mettre_a_jour_statut("ACCÈS ACCORDÉ. Bienvenue.", "#27ae60")
                messagebox.showinfo("Succès", "Authentification réussie !")
            else:
                self.mettre_a_jour_statut("ATTAQUE PAR PHOTO DÉTECTÉE OU ÉCHEC DU DÉFI", "#e74c3c")
                messagebox.showerror("Alerte Sécurité", "Attaque suspectée ou utilisateur inconnu.")
        
        threading.Thread(target=thread_auth).start()

    def declencher_enrolement(self):
        # Boîte de dialogue simple pour récupérer les métadonnées
        self.mettre_a_jour_statut("Préparation de l'enrôlement...", "#3498db")
        # Cette partie appellera votre fonction d'insertion chiffrée SQLite
        messagebox.showinfo("Enrôlement", "Regardez fixement la caméra pour capturer votre signature biométrique.")

    def quitter_application(self):
        self.flux_actif = False
        if self.video_flux:
            self.video_flux.release()
        self.window.destroy()
        sys.exit(0)

if __name__ == "__main__":
    # Initialisation de la BDD au lancement si nécessaire
    try:
        initialiser_bdd()
    except NameError:
        pass
        
    root = tk.Tk()
    app = BioFaceSecureApp(root)
    root.protocol("WM_DELETE_WINDOW", app.quitter_application)
    root.mainloop()
