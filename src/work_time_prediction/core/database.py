# Gestion de la connexion SQLite et des opérations de données

import sqlite3
import pandas as pd
import io
# Importation de l'exception spécifique pour la base de données
from sqlite3 import OperationalError 

from work_time_prediction.core.constants import DB_FILE, TABLE_NAME, DF_COLS, DFCols
from work_time_prediction.core.utils.time_converter import time_to_minutes
from work_time_prediction.core.exceptions import InvalidCsvFormatError
from work_time_prediction.core.required_columns import required_columns

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
        required_columns_clean = required_columns.clean()
    
        # Vérification des colonnes requises
        missing_cols = [col for col in vars(required_columns_clean).values() if col not in df.columns]
        
        if missing_cols:
            raise InvalidCsvFormatError(
                f"Le fichier CSV est incomplet. Colonnes manquantes : {', '.join(missing_cols)}"
            )

        # Conversion clé : Assurer que l'ID est une chaîne de caractères (plus générique)
        df[DFCols.ID] = df[required_columns_clean.id].astype(str)

        # Ingestion de données brutes pour le nettoyage
        df[DFCols.START_TIME_BY_MINUTES] = df[required_columns_clean.start].apply(time_to_minutes)
        df[DFCols.END_TIME_BY_MINUTES] = df[required_columns_clean.end].apply(time_to_minutes)
        df[DFCols.DATE] = pd.to_datetime(df[required_columns_clean.date], format='%d/%m/%Y', errors='coerce')

        # Nettoyage et filtrage
        df.dropna(subset=[DFCols.DATE, DFCols.ID], inplace=True)
        df = df[(df[DFCols.START_TIME_BY_MINUTES] > 0) & (df[DFCols.END_TIME_BY_MINUTES] > 0)]
        df = df[df[DFCols.END_TIME_BY_MINUTES] > df[DFCols.START_TIME_BY_MINUTES]]

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
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn, parse_dates=[DFCols.DATE])
        # Re-ajouter les colonnes Day_of_Week et Day_of_Year pour l'entraînement
        df[DFCols.DAY_OF_YEAR] = df[DFCols.DATE].dt.dayofyear
        df[DFCols.DAY_OF_WEEK] = df[DFCols.DATE].dt.dayofweek
        return df
    except (OperationalError, pd.errors.DatabaseError):
        # La table n'existe pas encore
        return pd.DataFrame()
    finally:
        conn.close()