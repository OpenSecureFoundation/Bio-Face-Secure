"""Moteur de reconnaissance — comparaison biométrique."""
import numpy as np
from config import get_config


def compare(captured: list, stored_list: list) -> tuple:
    """
    Retourne (nom | None, score_%).
    """
    threshold = get_config().SIMILARITY_THRESHOLD
    if not stored_list:
        return None, 0.0

    cap       = np.array(captured)
    best_name = None
    best_dist = 1.0

    for name, enc in stored_list:
        d = float(np.linalg.norm(cap - np.array(enc)))
        if d < best_dist:
            best_dist, best_name = d, name

    similarity = round(max(0.0, (1.0 - best_dist) * 100), 1)
    return (best_name, similarity) if best_dist <= threshold else (None, similarity)
