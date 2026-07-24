import face_recognition
import numpy as np
import database

def extraire_encodage_visage(frame_bgr):
    rgb_frame = frame_bgr[:, :, ::-1]
    encodings = face_recognition.face_encodings(rgb_frame)
    if len(encodings) > 0:
        return encodings[0]
    return None

def comparer_empreinte_avec_bdd(encoding_actuel):
    if encoding_actuel is None:
        return None, "Visage non détecté", 0.0

    utilisateurs = database.recuperer_utilisateurs()
    if not utilisateurs:
        return None, "Aucun utilisateur en BDD", 0.0

    seuil = database.recuperer_seuil()
    meilleure_distance = float("inf")
    meilleur_utilisateur = None

    for user in utilisateurs:
        dist = face_recognition.face_distance([user["encoding"]], encoding_actuel)[0]
        if dist < meilleure_distance:
            meilleure_distance = dist
            meilleur_utilisateur = user

    score_confiance = round((1.0 - meilleure_distance) * 100, 2)

    if meilleure_distance <= seuil and meilleur_utilisateur is not None:
        return meilleur_utilisateur["id"], meilleur_utilisateur["fullname"], score_confiance

    return None, "Inconnu", score_confiance
