# Image de base légère avec Python
FROM python:3.10-slim

# Éviter que Python écrive des fichiers .pyc et forcer l'affichage immédiat des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système nécessaires pour la compilation OpenCV et Dlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Copie et installation des exigences Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'intégralité du code source du projet
COPY . .

# Commande de démarrage par défaut
CMD ["python", "main.py"]
