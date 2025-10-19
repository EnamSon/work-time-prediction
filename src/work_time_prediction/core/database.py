# Gestion de la connexion SQLite et des opérations de données

import sqlite3
import pandas as pd
import io
# Importation de l'exception spécifique pour la base de données
from sqlite3 import OperationalError 

from work_time_prediction.core.constants import DB_FILE, TABLE_NAME, DF_COLS, REQUIRED_COLUMNS_RAW
from work_time_prediction.core.utils.time_converter import time_to_minutes
from work_time_prediction.core.exceptions import InvalidCsvFormatError

# --- Fonctions de Base de Données ---

def get_db_connection():
    """Crée et retourne une connexion SQLite (ici, en mémoire pour la simplicité du PoC)."""
    # Pour un déploiement réel, vous utiliseriez un chemin de fichier pour DB_NAME
    conn = sqlite3.connect(DB_FILE)
    return conn

def load_data_from_csv(csv_data: io.StringIO) -> pd.DataFrame:
    """Charge le CSV et effectue le prétraitement initial."""
    try:
        # Tentative de lecture avec différents séparateurs
        csv_data.seek(0)
        try:
            df = pd.read_csv(csv_data, sep=',')
        except Exception:
            csv_data.seek(0)
            df = pd.read_csv(csv_data, sep=';')

        df.columns = [col.strip().replace(' ', '_') for col in df.columns]

        # Noms des colonnes requises après le nettoyage
        required_columns_clean = [col.replace(' ', '_') for col in REQUIRED_COLUMNS_RAW]
    
        # Vérification des colonnes requises
        missing_cols = [col for col in required_columns_clean if col not in df.columns]
        
        if missing_cols:
            raise InvalidCsvFormatError(
                f"Le fichier CSV est incomplet. Colonnes manquantes : {', '.join(missing_cols)}"
            )

        # Conversion clé : Assurer que l'ID est une chaîne de caractères (plus générique)
        df['Employee_ID'] = df['Employee_ID'].astype(str)

        # Ingestion de données brutes pour le nettoyage
        df['first_punch_min'] = df['First_Punch'].apply(time_to_minutes)
        df['last_punch_min'] = df['Last_Punch'].apply(time_to_minutes)
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')

        # Nettoyage et filtrage
        df.dropna(subset=['Date', 'Employee_ID'], inplace=True)
        df = df[(df['first_punch_min'] > 0) & (df['last_punch_min'] > 0)]
        df = df[df['last_punch_min'] > df['first_punch_min']]

        return df[DF_COLS]

    except Exception as e:
        raise InvalidCsvFormatError(f"Échec du chargement ou du prétraitement du CSV : {e}")


def save_data_to_db(df: pd.DataFrame):
    """Sauvegarde le DataFrame traité dans la base de données."""
    conn = get_db_connection()
    try:
        # Écraser la table existante
        df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
    finally:
        conn.close()

def get_all_data() -> pd.DataFrame:
    """Récupère toutes les données de la base de données."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn, parse_dates=['Date'])
        # Re-ajouter les colonnes Day_of_Week et Day_of_Year pour l'entraînement
        df['Day_of_Year'] = df['Date'].dt.dayofyear
        df['Day_of_Week'] = df['Date'].dt.dayofweek
        return df
    except (OperationalError, pd.errors.DatabaseError):
        # La table n'existe pas encore
        return pd.DataFrame()
    finally:
        conn.close()
