# Logique de prédiction du Machine Learning

from typing import Dict, List, Any
import pandas as pd
from datetime import datetime

from work_time_prediction.core.constants import FEATURES, DFCols, DATE_FORMAT
from work_time_prediction.core.database import get_all_data
from work_time_prediction.core.utils.time_converter import minutes_to_time
from work_time_prediction.core.exceptions import ModelNotTrainedError, EmployeeNotFoundError
from work_time_prediction.core.ml_state import MLState
from pathlib import Path

def generate_predictions(
        ml_state: MLState, id: str, dates_to_predict: List[datetime], data_db_path: str | Path
) -> List[Dict[str, Any]]:
    """
    Génère les prédictions pour une liste de dates données.
    Mélange les données historiques réelles et les prédictions ML.
    """
    if not ml_state.is_trained or ml_state.model_start_time is None or ml_state.model_end_time is None:
        raise ModelNotTrainedError()

    if id not in ml_state.id_map:
         raise EmployeeNotFoundError(id)
    
    # 1. Récupération des données historiques
    historical_df = get_all_data(data_db_path)
    emp_history = historical_df[historical_df[DFCols.ID] == id]
    historical_data_map = {
        row[DFCols.DATE].strftime(DATE_FORMAT): {
            DFCols.START_TIME_BY_MINUTES: row[DFCols.START_TIME_BY_MINUTES],
            DFCols.END_TIME_BY_MINUTES: row[DFCols.END_TIME_BY_MINUTES]
        }
        for _, row in emp_history.iterrows()
    }

    # 2. Préparation du DataFrame pour l'inférence (pour les dates non historiques)
    future_data = []
    for date in dates_to_predict:
        date_str = date.strftime(DATE_FORMAT)
        if date_str not in historical_data_map:
            features = {
                DFCols.ID_ENCODED: ml_state.id_map[id],
                DFCols.DAY_OF_WEEK: date.weekday(),
                DFCols.DAY_OF_YEAR: date.timetuple().tm_yday,
                DFCols.DATE: date # Conserver la date pour le mapping
            }
            future_data.append(features)
    
    if future_data:
        future_df = pd.DataFrame(future_data)
        X_future = future_df[FEATURES]
        
        # Prédictions
        pred_start_time_by_minutes = ml_state.model_start_time.predict(X_future)
        pred_end_time_by_minutes = ml_state.model_end_time.predict(X_future)
    else:
        # Aucune prédiction nécessaire, toutes les dates sont historiques
        future_df = pd.DataFrame()
        pred_start_time_by_minutes = []
        pred_end_time_by_minutes = []


    # 3. Construction des résultats
    results = []
    pred_idx = 0
    
    for date in dates_to_predict:
        date_str = date.strftime(DATE_FORMAT)
        
        if date_str in historical_data_map:
            # Utiliser les données historiques réelles
            data = historical_data_map[date_str]
            start_time_by_minutes = data[DFCols.START_TIME_BY_MINUTES]
            end_time_by_minutes = data[DFCols.END_TIME_BY_MINUTES]
            is_historical = True
        else:
            # Utiliser les données prédites
            if pred_idx < len(pred_start_time_by_minutes):
                start_time_by_minutes = pred_start_time_by_minutes[pred_idx]
                end_time_by_minutes = pred_end_time_by_minutes[pred_idx]
                pred_idx += 1
            else:
                # Cela ne devrait pas arriver si la logique est correcte
                start_time_by_minutes = 0
                end_time_by_minutes = 0

            is_historical = False
            
            # Correction : S'assurer que l'heure de départ prédite est après l'arrivée
            if end_time_by_minutes < start_time_by_minutes:
                end_time_by_minutes = start_time_by_minutes + (6 * 60) # Ajout d'une durée de travail minimum
            
            # S'assurer que les temps prédits sont non-négatifs
            start_time_by_minutes = max(0, start_time_by_minutes)
            end_time_by_minutes = max(0, end_time_by_minutes)


        results.append({
            "date": date_str,
            "start_time": minutes_to_time(start_time_by_minutes),
            "end_time": minutes_to_time(end_time_by_minutes),
            "historical": is_historical
        })

    return results