# src/work_time_prediction/core/train_models.py
# Logique d'entraînement des modèles ML

from sklearn.ensemble import RandomForestRegressor  # type: ignore

from work_time_prediction.core.constants import FEATURES, DFCols
from work_time_prediction.core.database import get_all_data
from work_time_prediction.core.ml_state import MLState
from work_time_prediction.core.exceptions import NoDataFoundError
import pandas as pd
from pathlib import Path

def train_models(df: pd.DataFrame, data_db_path: str | Path) -> MLState:
    """
    Charge les données de la DB, encode l'ID et entraîne les modèles.
    Retourne le nombre de points de données utilisés.
    
    Raises:
        NoDataFoundError: Si aucune donnée n'est disponible dans la base de données.
    """
    df = get_all_data(data_db_path)
    
    if df.empty:
        raise NoDataFoundError(
            "Impossible d'entraîner : aucune donnée trouvée dans la base de données."
        )

    ml_state = MLState()
    # 1. Encodage de l'ID Employé
    all_employee_ids = df[DFCols.ID].unique()
    ml_state.id_encoder.fit(all_employee_ids)
    df[DFCols.ID_ENCODED] = ml_state.id_encoder.transform(df[DFCols.ID])
    
    # 2. Mise à jour du mapping global
    ml_state.id_map = {
        real_id: encoded_id
        for real_id, encoded_id in zip(
            all_employee_ids, 
            ml_state.id_encoder.transform(all_employee_ids)
        )
    }
    
    X = df[FEATURES]
    
    # 3. Modèle pour l'heure d'arrivée
    y_arrival = df[DFCols.START_TIME_BY_MINUTES]
    ml_state.model_start_time = RandomForestRegressor(
        n_estimators=100, 
        random_state=42, 
        n_jobs=-1, 
        max_depth=10
    )
    ml_state.model_start_time.fit(X, y_arrival)

    # 4. Modèle pour l'heure de départ
    y_departure = df[DFCols.END_TIME_BY_MINUTES]
    ml_state.model_end_time = RandomForestRegressor(
        n_estimators=100, 
        random_state=42, 
        n_jobs=-1, 
        max_depth=10
    )
    ml_state.model_end_time.fit(X, y_departure)
    
    ml_state.is_trained = True
    
    return ml_state
