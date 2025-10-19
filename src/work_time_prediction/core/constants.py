# src/work_time_prediction/core/constants.py
# Constantes de l'application

from pathlib import Path

# Base de données
DB_NAME = "work_time_data.db"
TABLE_NAME = "schedule_data"

# Colonnes du DataFrame
class DFCols:
    ID = "Employee_ID"
    ID_ENCODED = "Employee_ID_Encoded"
    DATE = "Date"
    START_TIME_BY_MINUTES = "first_punch_min"
    END_TIME_BY_MINUTES = "last_punch_min"
    DAY_OF_YEAR = "Day_of_Year"
    DAY_OF_WEEK = "Day_of_Week"

# Colonnes du DataFrame après prétraitement
DF_COLS = [DFCols.ID, DFCols.DATE, DFCols.START_TIME_BY_MINUTES, DFCols.END_TIME_BY_MINUTES]

# ============================================================================
# APPLICATION
# ============================================================================

APP_NAME = "work_time_prediction"
APP_VERSION = "1.0.0"

# ============================================================================
# CHEMINS DE BASE
# ============================================================================

# Répertoire home de l'utilisateur
HOME_DIR = Path.home()

# Répertoire racine de l'application dans $HOME
APP_ROOT_DIR = HOME_DIR / APP_NAME

# Répertoires principaux
DATA_DIR = APP_ROOT_DIR / "data"
LOGS_DIR = APP_ROOT_DIR / "logs"
CONFIG_DIR = APP_ROOT_DIR / "config"

# ============================================================================
# CHEMINS DE DONNÉES
# ============================================================================

# Modèles ML
MODELS_DIR = DATA_DIR / "models"

# Sessions et ownership
SESSIONS_DIR = DATA_DIR / "sessions"
SESSIONS_DB_PATH = SESSIONS_DIR / "sessions.db"

# Quotas par IP
QUOTAS_DIR = DATA_DIR / "quotas"
QUOTAS_DB_PATH = QUOTAS_DIR / "quotas.db"

# ============================================================================
# NOMS DE FICHIERS PAR MODÈLE
# ============================================================================

# Noms des fichiers dans chaque dossier de modèle (models/{model_id}/)
MODEL_METADATA_FILE = "metadata.json"
MODEL_ARRIVAL_FILE = "model_arrival.pkl"
MODEL_DEPARTURE_FILE = "model_departure.pkl"
MODEL_ENCODER_FILE = "encoder.pkl"
MODEL_DATA_DB_FILE = "data.db"

# ============================================================================
# CHEMINS DE LOGS
# ============================================================================

APP_LOG_FILE = LOGS_DIR / "app.log"
SECURITY_LOG_FILE = LOGS_DIR / "security.log"
QUOTAS_LOG_FILE = LOGS_DIR / "quotas.log"

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_FILE = CONFIG_DIR / "config.yaml"
ENV_FILE = APP_ROOT_DIR / ".env"

# ============================================================================
# FEATURES ML (Colonnes utilisées pour l'entraînement)
# ============================================================================

FEATURES = [DFCols.ID_ENCODED, DFCols.DAY_OF_WEEK, DFCols.DAY_OF_YEAR]

# ============================================================================
# QUOTAS PAR DÉFAUT
# ============================================================================

DEFAULT_QUOTAS = {
    # Limites par IP
    "models_per_ip": 10,
    "max_file_size_mb": 50,
    "max_employees_per_model": 10000,
    "max_data_points": 100000,
    "max_storage_per_ip_mb": 500,
    
    # Rate limiting
    "requests_per_minute": 60,
    "train_per_hour": 5,
    "predictions_per_day": 1000,
    
    # Bannissement
    "ban_after_violations": 10,
    "ban_duration_hours": 24,
}

# ============================================================================
# SÉCURITÉ
# ============================================================================

# JWT
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 365  # 1 an

# Taille minimale de la clé secrète JWT
MIN_JWT_SECRET_LENGTH = 32

# ============================================================================
# NETTOYAGE
# ============================================================================

CLEANUP_CONFIG = {
    "inactive_model_days": 30,      # Supprimer modèles inactifs après 30 jours
    "log_retention_days": 7,        # Garder les logs 7 jours
    "cleanup_interval_hours": 1,    # Lancer cleanup toutes les heures
}

# ============================================================================
# FORMATS DE DATE/HEURE
# ============================================================================

DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# ============================================================================
# CACHE
# ============================================================================

# Nombre maximum de modèles en cache mémoire (LRU)
MAX_MODELS_IN_CACHE = 50

DB_FILE = APP_ROOT_DIR / DB_NAME
