import sqlite3
import json
import logging
from cryptography.fernet import Fernet

# Configuration de la Traçabilité complète (Logs)
logging.basicConfig(
    filename='biosecure_activity.log',
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def generer_ou_charger_cle():
    try:
        with open("secret.key", "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
        return key

CLE_CHIFFREMENT = generer_ou_charger_cle()
fernet = Fernet(CLE_CHIFFREMENT)

def initialiser_bdd():
    conn = sqlite3.connect("bio_face_secure.db")
    cursor = conn.cursor()
    # Table Utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            role TEXT NOT NULL,
            signature_chiffree BLOB NOT NULL
        )
    ''')
    # Table Paramètres pour ajuster le seuil de similarité (Exigence BF2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parametres (
            cle TEXT PRIMARY KEY,
            valeur REAL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO parametres (cle, valeur) VALUES ('seuil', 0.50)")
    conn.commit()
    conn.close()

def log_evenement(niveau, message):
    if niveau == "INFO":
        logging.info(message)
    elif niveau == "WARNING":
        logging.warning(message)

def récupérer_seuil():
    conn = sqlite3.connect("bio_face_secure.db")
    cursor = conn.cursor()
    cursor.execute("SELECT valeur FROM parametres WHERE cle = 'seuil'")
    seuil = cursor.fetchone()[0]
    conn.close()
    return seuil

def modifier_seuil(nouveau_seuil):
    conn = sqlite3.connect("bio_face_secure.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE parametres SET valeur = ? WHERE cle = 'seuil'", (nouveau_seuil,))
    conn.commit()
    conn.close()
    log_evenement("INFO", f"Seuil de similarité ajusté à : {nouveau_seuil}")

def enrôler_utilisateur(nom, role, vecteur_128D):
    vecteur_json = json.dumps(vecteur_128D).encode()
    vecteur_chiffre = fernet.encrypt(vecteur_json) # Chiffrement AES-256
    
    conn = sqlite3.connect("bio_face_secure.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO utilisateurs (nom, role, signature_chiffree) VALUES (?, ?, ?)",
        (nom, role, vecteur_chiffre)
    )
    conn.commit()
    conn.close()
    log_evenement("INFO", f"Enrôlement réussi : {nom} ({role}) - Signature chiffrée stockée.")

def recuperer_utilisateurs():
    conn = sqlite3.connect("bio_face_secure.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, role, signature_chiffree FROM utilisateurs")
    lignes = cursor.fetchall()
    conn.close()
    
    utilisateurs = []
    for id_u, nom, role, vecteur_chiffre in lignes:
        try:
            vecteur_json = fernet.decrypt(vecteur_chiffre).decode()
            vecteur_128D = json.loads(vecteur_json)
            utilisateurs.append({"id": id_u, "nom": nom, "role": role, "vecteur": vecteur_128D})
        except Exception:
            continue
    return utilisateurs

def supprimer_utilisateur(id_utilisateur):
    conn = sqlite3.connect("bio_face_secure.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM utilisateurs WHERE id = ?", (id_utilisateur,))
    conn.commit()
    conn.close()
    log_evenement("INFO", f"Utilisateur ID {id_utilisateur} supprimé par l'administrateur.")
