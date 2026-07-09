"""Configuration centralisée — chargée depuis .env"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY       = os.getenv("SECRET_KEY", "change-me")
    FLASK_ENV        = os.getenv("FLASK_ENV", "development")
    DEBUG            = os.getenv("FLASK_DEBUG", "False") == "True"

    # Base de données
    DATABASE_PATH    = os.path.join("instance", "bioauth.db")
    ENCRYPTION_KEY_PATH = os.getenv("ENCRYPTION_KEY_PATH",
                                     "instance/.secret.key")

    # JWT
    JWT_SECRET_KEY   = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    JWT_EXPIRY_MIN   = 60

    # Webcam
    CAMERA_INDEX     = int(os.getenv("CAMERA_INDEX", 0))
    CAMERA_WIDTH     = int(os.getenv("CAMERA_WIDTH", 640))
    CAMERA_HEIGHT    = int(os.getenv("CAMERA_HEIGHT", 480))
    CAMERA_FPS       = int(os.getenv("CAMERA_FPS", 30))

    # Biométrie
    SIMILARITY_THRESHOLD   = float(os.getenv("SIMILARITY_THRESHOLD", 0.50))
    LIVENESS_EAR_THRESHOLD = float(os.getenv("LIVENESS_EAR_THRESHOLD", 0.25))
    LIVENESS_BLINK_FRAMES  = int(os.getenv("LIVENESS_BLINK_FRAMES", 2))
    LIVENESS_HEAD_ANGLE_PX = int(os.getenv("LIVENESS_HEAD_ANGLE_PX", 18))
    LIVENESS_TIMEOUT_SEC   = int(os.getenv("LIVENESS_TIMEOUT_SEC", 10))

    # Sécurité
    MAX_LOGIN_ATTEMPTS     = int(os.getenv("MAX_LOGIN_ATTEMPTS", 3))
    SESSION_TIMEOUT_MIN    = int(os.getenv("SESSION_TIMEOUT_MIN", 30))
    RATE_LIMIT_AUTH        = int(os.getenv("RATE_LIMIT_AUTH", 5))
    ANTI_SPOOFING_ENABLED  = os.getenv("ANTI_SPOOFING_ENABLED","True")=="True"
    AUDIT_ENABLED          = os.getenv("AUDIT_ENABLED", "True") == "True"

    # Logs
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR   = os.getenv("LOG_DIR", "instance/logs")

    # Upload
    UPLOAD_FOLDER    = os.path.join("app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 Mo

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
}

def get_config():
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
