import cv2
import face_recognition
import time
from database import recuperer_utilisateurs, récupérer_seuil, log_evenement

def evaluer_orientation(points_visage):
    """ Analyse les repères faciaux pour détecter les mouvements (Défense Anti-Spoofing) """
    if 'noseline' in points_visage and 'left_eye' in points_visage and 'right_eye' in points_visage:
        nez = points_visage['noseline'][0][0]
        oeil_g_x = points_visage['left_eye'][0][0]
        oeil_d_x = points_visage['right_eye'][0][0]
        
        dist_gauche = abs(nez - oeil_g_x)
        dist_droite = abs(oeil_d_x - nez)
        
        if dist_gauche / (dist_droite + 1e-6) > 1.8:
            return "DROITE"
        elif dist_droite / (dist_gauche + 1e-6) > 1.8:
            return "GAUCHE"
    return "CENTRE"

def executer_defi_vivacite(frame, defi_actuel):
    """ Valide si l'utilisateur répond physiquement au défi soumis """
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    points_visages = face_recognition.face_landmarks(rgb_small)
    
    for points in points_visages:
        if evaluer_orientation(points) == defi_actuel:
            return True
    return False

def authentifier_capture(frame):
    """ Compare la signature actuelle avec la BDD par distance euclidienne (BF1) """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_frame)
    
    if not encodings:
        return "AUCUN_VISAGE", None
        
    signature_actuelle = encodings[0]
    utilisateurs = recuperer_utilisateurs()
    seuil = récupérer_seuil()
    
    for u in utilisateurs:
        # Calcul de la Distance Euclidean
        distance = face_recognition.face_distance([u["vecteur"]], signature_actuelle)[0]
        if distance < seuil:
            log_evenement("INFO", f"Authentification réussie pour {u['nom']} (Distance: {distance:.2f})")
            return "SUCCES", u
            
    log_evenement("WARNING", "Tentative d'accès : Visage inconnu ou rejeté.")
    return "INCONNU", None
