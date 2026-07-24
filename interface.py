import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading

import database
import biometrics
import main


class BioFaceSecureApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bio-Face-Secure | Authentification Biométrique & SIEM")
        
        # Dimensions fixes style "Boîte de dialogue"
        self.largeur = 950
        self.hauteur = 680
        self.centrer_fenetre(self.largeur, self.hauteur)
        
        self.resizable(False, False)
        
        # Couleur BLEU CIEL pour tout l'arrière-plan entourant la boîte
        self.couleur_fond_bleu_ciel = "#38bdf8"
        self.configure(bg=self.couleur_fond_bleu_ciel)

        # Initialisation BDD & Styles
        database.initialiser_bdd()
        self.setup_styles()

        # Conteneur principal sur fond bleu ciel
        self.container = tk.Frame(self, bg=self.couleur_fond_bleu_ciel)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for PageClass in (InitialSetupFrame, MainAuthFrame, AdminDashboardFrame):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Vue initiale
        if not database.existe_administrateur():
            self.show_frame("InitialSetupFrame")
        else:
            self.show_frame("MainAuthFrame")

    def centrer_fenetre(self, largeur, hauteur):
        """Centre la fenêtre au milieu de l'écran du PC"""
        ecran_largeur = self.winfo_screenwidth()
        ecran_hauteur = self.winfo_screenheight()
        
        x = (ecran_largeur // 2) - (largeur // 2)
        y = (ecran_hauteur // 2) - (hauteur // 2)
        
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1e293b", borderwidth=0)
        style.configure("TNotebook.Tab", background="#0f172a", foreground="#94a3b8",
                        font=("Helvetica", 9, "bold"), padding=[10, 6])
        style.map("TNotebook.Tab", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

        style.configure("Treeview", background="#0f172a", foreground="#f8fafc",
                        fieldbackground="#0f172a", rowheight=26, font=("Helvetica", 9))
        style.configure("Treeview.Heading", background="#334155", foreground="#f8fafc", font=("Helvetica", 9, "bold"))
        style.map("Treeview", background=[("selected", "#0284c7")])

    def show_frame(self, page_name):
        # Désactiver les caméras sur toutes les frames avant de basculer
        for frame in self.frames.values():
            if hasattr(frame, "stop_cam"):
                frame.stop_cam()

        frame = self.frames[page_name]
        frame.tkraise()
        self.update_idletasks() # Forcer le rafraîchissement graphique
        if hasattr(frame, "on_show"):
            frame.on_show()


def creer_pied_de_page(parent_frame):
    """Pied de page discret en bas du conteneur"""
    footer = tk.Frame(parent_frame, bg="#020617", height=26)
    footer.pack(side="bottom", fill="x")
    lbl_footer = tk.Label(footer, text="Réalisé par les étudiants de Master 1 SSI de l'IUSJ",
                          font=("Helvetica", 8, "italic"), fg="#94a3b8", bg="#020617")
    lbl_footer.pack(pady=4)


# ----------------------------------------------------------------------
# Écran de configuration initiale (Boîte centrée sur fond Bleu Ciel)
# ----------------------------------------------------------------------
class InitialSetupFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#38bdf8")
        self.controller = controller
        self.cap_setup = None
        self.is_running = False
        self.current_frame = None

        creer_pied_de_page(self)

        # Boîte de dialogue centrée
        dialog_box = tk.Frame(self, bg="#1e293b", bd=2, relief="solid")
        dialog_box.place(relx=0.5, rely=0.48, anchor="center", width=820, height=540)

        top_bar = tk.Frame(dialog_box, bg="#0f172a", height=50)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🛡️ BIO-FACE-SECURE | Initialisation Administrateur",
                 font=("Helvetica", 12, "bold"), fg="#38bdf8", bg="#0f172a").pack(side="left", padx=15, pady=10)

        lbl_welcome = tk.Label(dialog_box, text="Création du Compte Administrateur Principal",
                               font=("Helvetica", 12, "bold"), fg="#f8fafc", bg="#1e293b")
        lbl_welcome.pack(pady=(15, 2))

        lbl_desc = tk.Label(dialog_box, text="Ce profil gère la console de contrôle et la réception des alertes.",
                            font=("Helvetica", 9), fg="#94a3b8", bg="#1e293b")
        lbl_desc.pack(pady=(0, 15))

        content_frame = tk.Frame(dialog_box, bg="#1e293b")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        form_frame = tk.Frame(content_frame, bg="#1e293b")
        form_frame.pack(side="left", fill="both", expand=True, padx=10)

        tk.Label(form_frame, text="Identifiant Admin (Username) :", fg="#94a3b8", bg="#1e293b", font=("Helvetica", 9)).pack(anchor="w", pady=2)
        self.entry_username = tk.Entry(form_frame, bg="#0f172a", fg="white", insertbackground="white", font=("Helvetica", 10))
        self.entry_username.pack(fill="x", pady=5)

        tk.Label(form_frame, text="Nom Complet :", fg="#94a3b8", bg="#1e293b", font=("Helvetica", 9)).pack(anchor="w", pady=2)
        self.entry_fullname = tk.Entry(form_frame, bg="#0f172a", fg="white", insertbackground="white", font=("Helvetica", 10))
        self.entry_fullname.pack(fill="x", pady=5)

        btn_init = tk.Button(form_frame, text="🚀 Finaliser l'Installation", font=("Helvetica", 10, "bold"),
                             bg="#10b981", fg="white", bd=0, pady=8, cursor="hand2", command=self.action_finaliser_setup)
        btn_init.pack(fill="x", pady=20)

        self.lbl_cam_setup = tk.Label(content_frame, bg="#020617", bd=1, relief="solid")
        self.lbl_cam_setup.pack(side="right", padx=10, pady=5)

    def on_show(self):
        if not self.is_running:
            self.cap_setup = cv2.VideoCapture(0)
            self.is_running = True
            threading.Thread(target=self.update_cam, daemon=True).start()

    def stop_cam(self):
        self.is_running = False
        if self.cap_setup and self.cap_setup.isOpened():
            self.cap_setup.release()
            self.cap_setup = None

    def update_cam(self):
        while self.is_running and self.cap_setup and self.cap_setup.isOpened():
            ret, frame = self.cap_setup.read()
            if ret:
                self.current_frame = frame.copy()
                cv2_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2_rgb).resize((340, 230))
                imgtk = ImageTk.PhotoImage(image=img)
                if self.is_running:
                    self.lbl_cam_setup.imgtk = imgtk
                    self.lbl_cam_setup.configure(image=imgtk)

    def action_finaliser_setup(self):
        username = self.entry_username.get().strip()
        fullname = self.entry_fullname.get().strip()

        if not username or not fullname:
            messagebox.showwarning("Configuration", "Veuillez remplir tous les champs.")
            return

        if self.current_frame is not None:
            encoding = biometrics.extraire_encodage_visage(self.current_frame)
            if encoding is None:
                messagebox.showerror("Biométrie", "Visage non détecté. Placez-vous bien face à la caméra.")
                return

            succes, msg = database.enroler_utilisateur(username, fullname, "ADMIN", encoding)
            if succes:
                self.stop_cam()
                messagebox.showinfo("Installation", f"Initialisation réussie !\nBienvenue M. {fullname}")
                self.controller.show_frame("MainAuthFrame")
            else:
                messagebox.showerror("Erreur", msg)
        else:
            messagebox.showerror("Caméra", "La caméra n'est pas encore prête. Réessayez dans un instant.")


# ----------------------------------------------------------------------
# Écran d'Authentification (Boîte centrée sur fond Bleu Ciel)
# ----------------------------------------------------------------------
class MainAuthFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#38bdf8")
        self.controller = controller
        self.cap = None
        self.is_running = False
        self.current_frame = None

        creer_pied_de_page(self)

        dialog_box = tk.Frame(self, bg="#1e293b", bd=2, relief="solid")
        dialog_box.place(relx=0.5, rely=0.48, anchor="center", width=750, height=550)

        header_frame = tk.Frame(dialog_box, bg="#0f172a", height=55)
        header_frame.pack(fill="x")

        lbl_logo = tk.Label(header_frame, text="🛡️ BIO-FACE-SECURE", font=("Helvetica", 14, "bold"), fg="#38bdf8", bg="#0f172a")
        lbl_logo.pack(side="left", padx=15, pady=10)

        btn_admin = tk.Button(header_frame, text="🔑 Dashboard Admin", font=("Helvetica", 9, "bold"),
                              bg="#0284c7", fg="white", bd=0, padx=12, pady=5, cursor="hand2", command=self.ouvrir_admin)
        btn_admin.pack(side="right", padx=15, pady=10)

        self.lbl_video = tk.Label(dialog_box, bg="#020617", bd=2, relief="solid")
        self.lbl_video.pack(pady=15)

        self.lbl_status = tk.Label(dialog_box, text="Positionnez votre visage face au capteur...", font=("Helvetica", 10, "bold"), fg="#94a3b8", bg="#1e293b")
        self.lbl_status.pack(pady=2)

        btn_scan = tk.Button(dialog_box, text="⚡ Lancer l'Authentification", font=("Helvetica", 11, "bold"),
                             bg="#10b981", fg="white", bd=0, padx=18, pady=8, cursor="hand2", command=self.action_authentifier)
        btn_scan.pack(pady=12)

    def on_show(self):
        if not self.is_running:
            self.cap = cv2.VideoCapture(0)
            self.is_running = True
            threading.Thread(target=self.update_webcam, daemon=True).start()

    def stop_cam(self):
        self.is_running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def update_webcam(self):
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame.copy()
                cv2_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2_rgb).resize((460, 290))
                imgtk = ImageTk.PhotoImage(image=img)
                if self.is_running:
                    self.lbl_video.imgtk = imgtk
                    self.lbl_video.configure(image=imgtk)

    def action_authentifier(self):
        if self.current_frame is not None:
            code_statut, message = main.traiter_tentative_acces(self.current_frame)
            if code_statut == "SUCCES":
                self.lbl_status.configure(text=message, fg="#4ade80")
            elif code_statut == "FRAUDE":
                self.lbl_status.configure(text=message, fg="#f87171")
                messagebox.showerror("Alerte Sécurité", message)
            else:
                self.lbl_status.configure(text=message, fg="#fbbf24")

    def ouvrir_admin(self):
        if self.current_frame is not None:
            code, msg = main.traiter_tentative_acces(self.current_frame)
            if code == "SUCCES":
                enc = biometrics.extraire_encodage_visage(self.current_frame)
                user_id, username, score = biometrics.comparer_empreinte_avec_bdd(enc)
                
                self.stop_cam() # Arrêt propre de la caméra
                admin_frame = self.controller.frames["AdminDashboardFrame"]
                admin_frame.set_admin_session(username)
                self.controller.show_frame("AdminDashboardFrame")
            else:
                messagebox.showwarning("Accès Refusé", "Seul un Administrateur authentifié peut accéder au Dashboard.")


# ----------------------------------------------------------------------
# Dashboard Administrateur
# ----------------------------------------------------------------------
class AdminDashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#38bdf8")
        self.controller = controller
        self.cap_enrol = None
        self.is_enrol_running = False
        self.frame_enrol_current = None
        self.admin_name = "Administrateur"

        creer_pied_de_page(self)

        dialog_box = tk.Frame(self, bg="#1e293b", bd=2, relief="solid")
        dialog_box.place(relx=0.5, rely=0.48, anchor="center", width=910, height=600)

        self.top_bar = tk.Frame(dialog_box, bg="#0f172a", height=50)
        self.top_bar.pack(fill="x")

        self.lbl_welcome = tk.Label(self.top_bar, text=f"🛡️ Bienvenue M. {self.admin_name} | Console Admin",
                                     font=("Helvetica", 11, "bold"), fg="#f8fafc", bg="#0f172a")
        self.lbl_welcome.pack(side="left", padx=15, pady=10)

        btn_retour = tk.Button(self.top_bar, text="← Déconnexion", font=("Helvetica", 8, "bold"), bg="#ef4444", fg="white",
                                bd=0, padx=10, pady=4, cursor="hand2", command=self.retour_accueil)
        btn_retour.pack(side="right", padx=15, pady=10)

        self.notebook = ttk.Notebook(dialog_box)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        self.tab_enrollement = tk.Frame(self.notebook, bg="#1e293b")
        self.tab_users = tk.Frame(self.notebook, bg="#1e293b")
        self.tab_alertes = tk.Frame(self.notebook, bg="#1e293b")
        self.tab_logs = tk.Frame(self.notebook, bg="#1e293b")

        self.notebook.add(self.tab_enrollement, text="➕ Enrôlement Visuel")
        self.notebook.add(self.tab_users, text="👥 Profils")
        self.notebook.add(self.tab_alertes, text="🚨 Alertes")
        self.notebook.add(self.tab_logs, text="📜 Journaux d'Accès")

        self.setup_enrollement_tab()
        self.setup_users_tab()
        self.setup_alertes_tab()
        self.setup_logs_tab()

    def set_admin_session(self, admin_username):
        self.admin_name = admin_username
        self.lbl_welcome.configure(text=f"🛡️ Bienvenue M. {self.admin_name} | Console Admin")

    def retour_accueil(self):
        self.stop_cam()
        self.controller.show_frame("MainAuthFrame")

    def setup_enrollement_tab(self):
        card_form = tk.Frame(self.tab_enrollement, bg="#0f172a", bd=1, relief="solid")
        card_form.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        tk.Label(card_form, text="Nouveau Profil Biométrique", font=("Helvetica", 11, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", padx=15, pady=(15, 5))

        tk.Label(card_form, text="Identifiant (Username) :", fg="#94a3b8", bg="#0f172a", font=("Helvetica", 9)).pack(anchor="w", padx=15, pady=2)
        self.entry_username = tk.Entry(card_form, bg="#1e293b", fg="white", insertbackground="white", bd=1, font=("Helvetica", 9))
        self.entry_username.pack(fill="x", padx=15, pady=3)

        tk.Label(card_form, text="Nom complet :", fg="#94a3b8", bg="#0f172a", font=("Helvetica", 9)).pack(anchor="w", padx=15, pady=2)
        self.entry_fullname = tk.Entry(card_form, bg="#1e293b", fg="white", insertbackground="white", bd=1, font=("Helvetica", 9))
        self.entry_fullname.pack(fill="x", padx=15, pady=3)

        tk.Label(card_form, text="Rôle système :", fg="#94a3b8", bg="#0f172a", font=("Helvetica", 9)).pack(anchor="w", padx=15, pady=2)
        self.combo_role = ttk.Combobox(card_form, values=["USER", "ADMIN"], state="readonly", font=("Helvetica", 9))
        self.combo_role.set("USER")
        self.combo_role.pack(fill="x", padx=15, pady=3)

        btn_capture = tk.Button(card_form, text="📸 Capturer & Chiffrer (128D)", font=("Helvetica", 10, "bold"),
                                bg="#10b981", fg="white", bd=0, pady=6, cursor="hand2", command=self.action_enroller)
        btn_capture.pack(fill="x", padx=15, pady=15)

        self.lbl_cam_enrol = tk.Label(self.tab_enrollement, bg="#020617", bd=1, relief="solid")
        self.lbl_cam_enrol.pack(side="right", padx=10, pady=10)

    def start_enrol_cam(self):
        if not self.is_enrol_running:
            self.cap_enrol = cv2.VideoCapture(0)
            self.is_enrol_running = True
            threading.Thread(target=self.update_enrol_cam, daemon=True).start()

    def stop_cam(self):
        self.is_enrol_running = False
        if self.cap_enrol and self.cap_enrol.isOpened():
            self.cap_enrol.release()
            self.cap_enrol = None

    def update_enrol_cam(self):
        while self.is_enrol_running and self.cap_enrol and self.cap_enrol.isOpened():
            ret, frame = self.cap_enrol.read()
            if ret:
                self.frame_enrol_current = frame.copy()
                cv2_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2_rgb).resize((360, 240))
                imgtk = ImageTk.PhotoImage(image=img)
                if self.is_enrol_running:
                    self.lbl_cam_enrol.imgtk = imgtk
                    self.lbl_cam_enrol.configure(image=imgtk)

    def action_enroller(self):
        username = self.entry_username.get().strip()
        fullname = self.entry_fullname.get().strip()
        role = self.combo_role.get()

        if not username or not fullname:
            messagebox.showwarning("Formulaire Incomplet", "Veuillez remplir tous les champs.")
            return

        if self.frame_enrol_current is not None:
            encoding = biometrics.extraire_encodage_visage(self.frame_enrol_current)
            if encoding is None:
                messagebox.showerror("Erreur", "Aucun visage net n'a été détecté.")
                return

            succes, msg = database.enroler_utilisateur(username, fullname, role, encoding)
            if succes:
                messagebox.showinfo("Succès", msg)
                self.entry_username.delete(0, tk.END)
                self.entry_fullname.delete(0, tk.END)
                self.charger_utilisateurs()
            else:
                messagebox.showerror("Erreur", msg)

    def setup_users_tab(self):
        bar = tk.Frame(self.tab_users, bg="#1e293b")
        bar.pack(fill="x", pady=5)
        tk.Button(bar, text="🔄 Actualiser", bg="#334155", fg="white", bd=0, padx=8, pady=4, cursor="hand2", command=self.charger_utilisateurs).pack(side="left")
        tk.Button(bar, text="🗑️ Supprimer profil", bg="#ef4444", fg="white", bd=0, padx=8, pady=4, cursor="hand2", command=self.action_supprimer_user).pack(side="right")

        cols = ("ID", "Nom d'utilisateur", "Nom Complet", "Rôle", "Créé le")
        self.tree_users = ttk.Treeview(self.tab_users, columns=cols, show="headings")
        for c in cols:
            self.tree_users.heading(c, text=c)
            self.tree_users.column(c, width=120)
        self.tree_users.pack(fill="both", expand=True)

    def charger_utilisateurs(self):
        for item in self.tree_users.get_children():
            self.tree_users.delete(item)
        for u in database.lister_utilisateurs():
            self.tree_users.insert("", "end", values=u)

    def action_supprimer_user(self):
        selected = self.tree_users.selection()
        if not selected:
            messagebox.showwarning("Sélection requise", "Veuillez sélectionner un profil.")
            return
        user_vals = self.tree_users.item(selected, "values")
        user_id, username = user_vals[0], user_vals[1]

        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer '{username}' ?"):
            database.supprimer_utilisateur(user_id)
            self.charger_utilisateurs()
            messagebox.showinfo("Bio-Face-Secure", "Profil supprimé avec succès.")

    def setup_alertes_tab(self):
        bar = tk.Frame(self.tab_alertes, bg="#1e293b")
        bar.pack(fill="x", pady=5)
        tk.Button(bar, text="🔄 Actualiser alertes", bg="#334155", fg="white", bd=0, padx=8, pady=4, cursor="hand2", command=self.charger_alertes).pack(side="left")

        cols = ("ID Log", "Utilisateur Cible", "Statut d'Alerte", "Score Confiance", "Horodatage")
        self.tree_alertes = ttk.Treeview(self.tab_alertes, columns=cols, show="headings")
        for c in cols:
            self.tree_alertes.heading(c, text=c)
            self.tree_alertes.column(c, width=130)
        self.tree_alertes.pack(fill="both", expand=True)

    def charger_alertes(self):
        for item in self.tree_alertes.get_children():
            self.tree_alertes.delete(item)
        for a in database.obtenir_alertes_securite():
            self.tree_alertes.insert("", "end", values=a)

    def setup_logs_tab(self):
        bar = tk.Frame(self.tab_logs, bg="#1e293b")
        bar.pack(fill="x", pady=5)
        tk.Button(bar, text="🔄 Actualiser journaux", bg="#334155", fg="white", bd=0, padx=8, pady=4, cursor="hand2", command=self.charger_logs).pack(side="left")

        cols = ("ID Log", "Utilisateur", "Statut", "Score Confiance", "Horodatage")
        self.tree_logs = ttk.Treeview(self.tab_logs, columns=cols, show="headings")
        for c in cols:
            self.tree_logs.heading(c, text=c)
            self.tree_logs.column(c, width=130)
        self.tree_logs.pack(fill="both", expand=True)

    def charger_logs(self):
        for item in self.tree_logs.get_children():
            self.tree_logs.delete(item)
        for l in database.obtenir_journaux_utilisateur():
            self.tree_logs.insert("", "end", values=l)

    def on_show(self):
        self.start_enrol_cam()
        self.charger_utilisateurs()
        self.charger_alertes()
        self.charger_logs()


if __name__ == "__main__":
    app = BioFaceSecureApp()
    app.mainloop()
