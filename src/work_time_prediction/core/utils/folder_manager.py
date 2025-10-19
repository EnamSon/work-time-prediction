from work_time_prediction.core.constants import (
    APP_ROOT_DIR, DATA_DIR, LOGS_DIR, CONFIG_DIR, MODELS_DIR, SESSIONS_DIR, QUOTAS_DIR
)
from pathlib import Path


def get_model_dir(model_id: str) -> Path:
    """
    Retourne le chemin du répertoire d'un modèle spécifique.
    
    Args:
        model_id: Identifiant unique du modèle
        
    Returns:
        Path vers le répertoire du modèle
    """
    return MODELS_DIR / model_id


def get_model_file_path(model_id: str, filename: str) -> Path:
    """
    Retourne le chemin complet d'un fichier dans le répertoire d'un modèle.
    
    Args:
        model_id: Identifiant unique du modèle
        filename: Nom du fichier (utiliser les constantes MODEL_*_FILE)
        
    Returns:
        Path vers le fichier
    """
    return get_model_dir(model_id) / filename


def ensure_directories_exist():
    """
    Crée tous les répertoires nécessaires s'ils n'existent pas.
    À appeler au démarrage de l'application.
    """
    directories = [
        APP_ROOT_DIR,
        DATA_DIR,
        LOGS_DIR,
        CONFIG_DIR,
        MODELS_DIR,
        SESSIONS_DIR,
        QUOTAS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# ============================================================================
# INITIALISATION AU CHARGEMENT DU MODULE
# ============================================================================

# Créer les répertoires au chargement si nécessaire
# (Optionnel - peut être fait explicitement dans main.py)
# ensure_directories_exist()