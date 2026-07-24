import sqlite3
import numpy as np

DB_NAME = "bio_face_secure.db"

def initialiser_bdd():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            fullname TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'USER',
            encoding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('seuil', '0.5')")
    
    conn.commit()
    conn.close()

def existe_administrateur():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def enroler_utilisateur(username, fullname, role, encoding):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        encoding_bytes = encoding.astype(np.float64).tobytes()
        cursor.execute(
            "INSERT INTO users (username, fullname, role, encoding) VALUES (?, ?, ?, ?)",
            (username, fullname, role, encoding_bytes)
        )
        conn.commit()
        conn.close()
        return True, f"Utilisateur {username} enrôlé avec succès."
    except sqlite3.IntegrityError:
        return False, f"L'utilisateur {username} existe déjà."
    except Exception as e:
        return False, f"Erreur lors de l'enrôlement : {str(e)}"

def lister_utilisateurs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, fullname, role, created_at FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows

def recuperer_utilisateurs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, fullname, role, encoding FROM users")
    rows = cursor.fetchall()
    conn.close()
    
    users = []
    for row in rows:
        u_id, username, fullname, role, enc_blob = row
        enc_array = np.frombuffer(enc_blob, dtype=np.float64)
        users.append({
            "id": u_id,
            "username": username,
            "fullname": fullname,
            "role": role,
            "encoding": enc_array
        })
    return users

def supprimer_utilisateur(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def recuperer_seuil():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'seuil'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return float(row[0])
    return 0.5

def log_evenement(username, status, confidence):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (username, status, confidence) VALUES (?, ?, ?)",
        (username, status, confidence)
    )
    conn.commit()
    conn.close()

def obtenir_journaux_utilisateur():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, status, confidence, timestamp FROM logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtenir_alertes_securite():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, status, confidence, timestamp FROM logs WHERE status LIKE '%FRAUDE%' OR status LIKE '%INCONNU%' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
