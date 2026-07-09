#!/bin/bash

echo "======================================"
echo "   BIOAUTH - DEMARRAGE SYSTEME"
echo "======================================"

# 1. Aller dans le projet
cd ~/bioauth_flask || { echo "Dossier introuvable"; exit 1; }

# 2. Activer l'environnement virtuel
source venv/bin/activate

# 3. Stopper les anciens processus Flask et ngrok
echo "[INFO] Nettoyage des anciens processus..."

pkill -f run.py 2>/dev/null
pkill -f ngrok 2>/dev/null

# 4. Attendre que les ports se libèrent
sleep 2

# 5. Lancer Flask dans un nouveau terminal
echo "[INFO] Lancement du serveur Flask..."
gnome-terminal -- bash -c "python3 run.py; exec bash"

# 6. Attendre que Flask démarre correctement
sleep 5

# 7. Lancer ngrok dans un autre terminal
echo "[INFO] Lancement de ngrok..."
gnome-terminal -- bash -c "ngrok http 5000; exec bash"

echo "======================================"
echo "   SYSTEME BIOAUTH EN LIGNE"
echo "======================================"
