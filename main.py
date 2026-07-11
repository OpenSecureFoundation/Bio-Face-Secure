import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import random

# Importations de notre architecture MVC
from database import (
    initialiser_bdd, enrôler_utilisateur, recuperer_utilisateurs, 
    supprimer_utilisateur, récupérer_seuil, modifier_seuil, log_evenement
)
from biometrics import executer_defi_vivacite, authentifier_capture

class BioSecureInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Bio-Face-Secure Pro — Panneau de Contrôle Directeur")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1e272e")
        
        # Initialisation de la caméra (Gestion du flux webcam en temps réel)
        self.cap = cv2.VideoCapture(0)
        
        # Variables d'état pour les modules de sécurité
        self.mode_defi = False
        self.defi_demande = ""
        self.temps_debut_defi = 0
        self.nom_enrolement = ""
        self.role_enrolement = ""
        
        # Construction et affichage
        self.creer_architecture_graphique()
        self.rafraichir_tableau_admin()
        self.mettre_a_jour_flux_video()

    def creer_architecture_graphique(self):
        # Configuration des styles pour les composants graphiques
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview", bg="#2f3640", fg="white", fieldbg="#2f3640", rowheight=25)
        s.configure("Treeview.Heading", bg="#718093", fg="white", font=("Helvetica", 10, "bold"))

        # ================= PANNEAU GAUCHE : CŒUR BIOMÉTRIQUE =================
        left_frame = tk.Frame(self.root, bg="#1e272e")
        left_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)

        titre_video = tk.Label(left_frame, text="⚙️ CAPTURE BIOMÉTRIQUE EN DIRECT", font=("Helvetica", 12, "bold"), fg="#dcdde1", bg="#1e272e")
        titre_video.pack(anchor="w", pady=5)

        # Zone d'affichage du flux caméra
        self.video_label = tk.Label(left_frame, bg="#2f3640", borderwidth=2, relief="groove")
        self.video_label.pack(fill="both", expand=True)

        # Bandeau de notification explicite (Exigence clé pour le signalement des alertes)
        self.alert_panel = tk.Label(left_frame, text="SYSTÈME EN LIGNE - EN ATTENTE", font=("Helvetica", 11, "bold"), bg="#2f3640", fg="#4cd137", height=2)
        self.alert_panel.pack(fill="x", pady=10)

        # Layout des boutons d'action métier
        btn_layout = tk.Frame(left_frame, bg="#1e272e")
        btn_layout.pack(fill="x")
        
        ttk.Button(btn_layout, text="🔒 AUTHENTIFIER (BF1)", command=self.lancer_workflow_auth).pack(side="left", fill="x", expand=True, padx=5, ipady=5)
        ttk.Button(btn_layout, text="📝 ENRÔLER (BF3)", command=self.ouvrir_fenetre_enrolement).pack(side="left", fill="x", expand=True, padx=5, ipady=5)

        # ================= PANNEAU DROIT : CONSOLE DE GESTION (BF2) =================
        right_frame = tk.Frame(self.root, bg="#2f3640", width=450, padx=15, pady=15)
        right_frame.pack(side="right", fill="y", padx=10, pady=20)

        tk.Label(right_frame, text="🛡️ CONSOLE DE GESTION ADMINISTRATIVE", font=("Helvetica", 12, "bold"), fg="#f5f6fa", bg="#2f3640").pack(anchor="w", pady=5)
        
        # Configuration dynamique du seuil de similarité (Exigence BF2)
        seuil_frame = tk.Frame(right_frame, bg="#2f3640")
        seuil_frame.pack(fill="x", pady=10)
        tk.Label(seuil_frame, text="Seuil de distance euclidienne :", fg="white", bg="#2f3640").pack(side="left")
        
        self.seuil_var = tk.StringVar(value=str(récupérer_seuil()))
        self.entry_seuil = ttk.Entry(seuil_frame, textvariable=self.seuil_var, width=6)
        self.entry_seuil.pack(side="left", padx=5)
        ttk.Button(seuil_frame, text="Ajuster", command=self.appliquer_nouveau_seuil).pack(side="left")

        # Composant Treeview pour l'administration des profils
        tk.Label(right_frame, text="Profils Utilisateurs Enregistrés :", fg="#dcdde1", bg="#2f3640").pack(anchor="w", pady=5)
        self.tree = ttk.Treeview(right_frame, columns=("ID", "Nom", "Rôle"), show="headings", height=15)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nom", text="Nom")
        self.tree.heading("Rôle", text="Rôle")
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Nom", width=200)
        self.tree.column("Rôle", width=120)
        self.tree.pack(fill="both", expand=True, pady=5)

        ttk.Button(right_frame, text="❌ SUPPRIMER LE PROFIL SÉLECTIONNÉ", command=self.action_supprimer).pack(fill="x", pady=10, ipady=4)

    def mettre_a_jour_flux_video(self):
        ret, frame = self.cap.read()
        if ret:
            # Gestion active de la défense Anti-Spoofing (Défi-Réponse de vivacité)
            if self.mode_defi:
                cv2.putText(frame, f"SVP TOURNEZ LA TETE A : {self.defi_demande}", (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
                # Évaluation de la réponse de l'utilisateur
                if executer_defi_vivacite(frame, self.defi_demande):
                    self.mode_defi = False
                    # Si c'est un enrôlement après défi réussi
                    if self.nom_enrolement:
                        self.alert_panel.config(text="VIVACITÉ CONFIRMÉE - ENREGISTREMENT...", bg="#192a56", fg="#00a8ff")
                        self.root.after(500, lambda: self.finaliser_enrolement(frame))
                    else:
                        # Si c'est une authentification classique
                        self.alert_panel.config(text="VIVACITÉ CONFIRMÉE - ANALYSE BIOMÉTRIQUE...", bg="#192a56", fg="#00a8ff")
                        self.root.after(500, lambda: self.finaliser_traitement_biometrique(frame))
                        
                elif time.time() - self.temps_debut_defi > 5.0: # Temps limite dépassé
                    self.mode_defi = False
                    self.alert_panel.config(text="🚫 ATTAQUE PAR PHOTO DÉTECTÉE (ÉCHEC VIVACITÉ)", bg="#c23616", fg="white")
                    log_evenement("WARNING", f"Alerte Sécurité : Tentative d'usurpation avortée pour l'action {'Enrôlement' if self.nom_enrolement else 'Authentification'}.")
                    messagebox.showerror("Alerte Sécurité", "Attaque suspectée ou absence de réponse au défi. Opération annulée.")
            
            # Conversion de l'image OpenCV (BGR) vers Tkinter (RGBA)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
        self.root.after(10, self.mettre_a_jour_flux_video)

    def lancer_workflow_auth(self):
        self.nom_enrolement = "" # Assure qu'on est en mode authentification
        self.defi_demande = random.choice(["GAUCHE", "DROITE"])
        self.temps_debut_defi = time.time()
        self.mode_defi = True
        self.alert_panel.config(text=f"DÉFI SÉCURITÉ : Tournez la tête à {self.defi_demande}", bg="#e1b12c", fg="black")

    def finaliser_traitement_biometrique(self, frame):
        statut, utilisateur = authentifier_capture(frame)
        if statut == "SUCCES":
            self.alert_panel.config(text=f"✅ ACCÈS ACCORDÉ : {utilisateur['nom']} ({utilisateur['role']})", bg="#4cd137", fg="black")
            messagebox.showinfo("Succès", f"Authentification réussie. Bienvenue {utilisateur['nom']}.")
        elif statut == "INCONNU":
            self.alert_panel.config(text="❌ ACCÈS REFUSÉ : PROFIL INCONNU", bg="#c23616", fg="white")
            messagebox.showwarning("Refus d'accès", "Signature biométrique non reconnue.")
        else:
            self.alert_panel.config(text="⚠️ ERREUR : AUCUN VISAGE DÉTECTÉ", bg="#7f8c8d", fg="white")

    def ouvrir_fenetre_enrolement(self):
        win = tk.Toplevel(self.root)
        win.title("Nouvel Enrôlement (BF3)")
        win.geometry("340x200")
        win.configure(bg="#2f3640")
        win.transient(self.root)
        win.grab_set()
        
        tk.Label(win, text="Nom de l'utilisateur :", fg="white", bg="#2f3640", font=("Helvetica", 10)).pack(pady=5)
        enm = ttk.Entry(win, width=30)
        enm.pack()
        
        tk.Label(win, text="Rôle attribué :", fg="white", bg="#2f3640", font=("Helvetica", 10)).pack(pady=5)
        erl = ttk.Combobox(win, values=["Utilisateur", "Administrateur"], width=28)
        erl.pack()
        
        def valider_champs():
            if enm.get().strip() and erl.get():
                self.nom_enrolement = enm.get().strip()
                self.role_enrolement = erl.get()
                win.destroy()
                
                # Déclenchement automatique du défi de vivacité dès l'inscription
                self.defi_demande = random.choice(["GAUCHE", "DROITE"])
                self.temps_debut_defi = time.time()
                self.mode_defi = True
                self.alert_panel.config(text=f"INSCRIPTION - TOURNEZ LA TÊTE À : {self.defi_demande}", bg="#e1b12c", fg="black")
            else:
                messagebox.showwarning("Champs requis", "Veuillez remplir le nom et sélectionner un rôle.")
        
        ttk.Button(win, text="Lancer la capture de sécurité", command=valider_champs).pack(pady=20)

    def finaliser_enrolement(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if encodings:
            # Enrôlement avec génération et chiffrement AES-256 du vecteur 128D
            enrôler_utilisateur(self.nom_enrolement, self.role_enrolement, encodings[0].tolist())
            self.alert_panel.config(text=f"PROFIL DE {self.nom_enrolement} INSCRIT ET CHIFFRÉ !", bg="#4cd137", fg="black")
            messagebox.showinfo("Enrôlement Terminé", f"Le profil de {self.nom_enrolement} a été stocké de manière sécurisée.")
            self.rafraichir_tableau_admin()
        else:
            self.alert_panel.config(text="⚠️ ÉCHEC : ENCODAGE IMPOSSIBLE", bg="#7f8c8d", fg="white")
            messagebox.showerror("Erreur Capture", "Le visage n'a pas pu être encodé correctement. Réessayez.")

    def appliquer_nouveau_seuil(self):
        try:
            val = float(self.seuil_var.get())
            if 0.0 < val < 1.0:
                modifier_seuil(val)
                messagebox.showinfo("Paramètres", f"Le seuil de tolérance a été ajusté à {val}.")
            else:
                messagebox.showwarning("Valeur incorrecte", "Le seuil doit être compris entre 0.1 et 0.9.")
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez saisir un coefficient numérique valide.")

    def rafraichir_tableau_admin(self):
        # Nettoyage
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Remplissage par déchiffrement des données à la volée (BF2)
        for u in recuperer_utilisateurs():
            self.tree.insert("", "end", values=(u["id"], u["nom"], u["role"]))

    def action_supprimer(self):
        selected = self.tree.selection()
        if selected:
            id_u = self.tree.item(selected[0])["values"][0]
            nom_u = self.tree.item(selected[0])["values"][1]
            if messagebox.askyesno("Confirmation", f"Supprimer définitivement le profil de {nom_u} ?"):
                supprimer_utilisateur(id_u)
                self.rafraichir_tableau_admin()
                self.alert_panel.config(text="PROFIL UTILISATEUR EFFACÉ", bg="#7f8c8d", fg="white")
        else:
            messagebox.showwarning("Sélection requise", "Veuillez désigner un profil dans la liste.")

if __name__ == "__main__":
    initialiser_bdd()
    root = tk.Tk()
    app = BioSecureInterface(root)
    root.mainloop()
