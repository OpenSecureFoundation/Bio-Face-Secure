import database
import biometrics

def traiter_tentative_acces(frame_bgr):
    """
    Traite une tentative d'authentification biométrique depuis l'image capturée.
    Retourne : (code_statut, message)
    """
    encoding = biometrics.extraire_encodage_visage(frame_bgr)
    
    if encoding is None:
        return "ERREUR", "Aucun visage détecté. Veuillez vous placer bien en face du capteur."

    user_id, fullname, score = biometrics.comparer_empreinte_avec_bdd(encoding)

    if user_id is not None:
        # Recherche des informations utilisateur pour vérifier son rôle
        utilisateurs = database.recuperer_utilisateurs()
        role = "USER"
        username = fullname
        
        for u in utilisateurs:
            if u["id"] == user_id:
                role = u["role"]
                username = u["username"]
                break

        msg = f"Accès Autorisé : Bienvenue M. {fullname} (Confiance: {score}%)"
        database.log_evenement(username, f"SUCCES ({role})", score)
        return "SUCCES", msg
    else:
        msg = f"Accès Refusé : Visage inconnu ou non reconnu (Confiance: {score}%)"
        database.log_evenement("Inconnu", "ECHEC_IDENTIFICATION", score)
        return "FRAUDE", msg
