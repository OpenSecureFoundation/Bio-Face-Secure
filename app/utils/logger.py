"""Logger centralisé."""
import logging
import os
from config import get_config

_configured = False

def setup_logging():
    global _configured
    if _configured:
        return
    cfg = get_config()
    os.makedirs(cfg.LOG_DIR, exist_ok=True)
    level = getattr(logging, cfg.LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(
                os.path.join(cfg.LOG_DIR, "bioauth.log"),
                encoding="utf-8"),
            logging.StreamHandler(),
        ]
    )
    _configured = True

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"bioauth.{name}")
