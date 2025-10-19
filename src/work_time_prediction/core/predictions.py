# Logique de prédiction du Machine Learning

from typing import Dict, List, Any
import pandas as pd
from datetime import datetime

from work_time_prediction.core.constants import FEATURES
from work_time_prediction.core.database import get_all_data
from work_time_prediction.core.utils import minutes_to_time
from work_time_prediction.core.exceptions import ModelNotTrainedError, EmployeeNotFoundError
from work_time_prediction.core.ml_state import ml_state


def generate_predictions(employee_id: str, dates_to_predict: List[datetime]) -> List[Dict[str, Any]]:
    """
    Génère les prédictions pour une liste de dates données.
    Mélange les données historiques réelles et les prédictions ML.
    """
    if not ml_state.is_trained or ml_state.model_arrival is None or ml_state.model_departure is None:
        raise ModelNotTrainedError()

    if employee_id not in ml_state.employee_id_map:
         raise EmployeeNotFoundError(employee_id)
    
    # 1. Récupération des données historiques
    historical_df = get_all_data()
    emp_history = historical_df[historical_df['Employee_ID'] == employee_id]
    historical_data_map = {
        row['Date'].strftime('%d/%m/%Y'): {
            'first_punch_min': row['first_punch_min'],
            'last_punch_min': row['last_punch_min']
        }
        for _, row in emp_history.iterrows()
    }

    # 2. Préparation du DataFrame pour l'inférence (pour les dates non historiques)
    future_data = []
    for date in dates_to_predict:
        date_str = date.strftime('%d/%m/%Y')
        if date_str not in historical_data_map:
            features = {
                'Employee_ID_Encoded': ml_state.employee_id_map[employee_id],
                'Day_of_Week': date.weekday(),
                'Day_of_Year': date.timetuple().tm_yday,
                'Date': date # Conserver la date pour le mapping
            }
            future_data.append(features)
    
    if future_data:
        future_df = pd.DataFrame(future_data)
        X_future = future_df[FEATURES]
        
        # Prédictions
        pred_arrival_min = ml_state.model_arrival.predict(X_future)
        pred_departure_min = ml_state.model_departure.predict(X_future)
    else:
        # Aucune prédiction nécessaire, toutes les dates sont historiques
        future_df = pd.DataFrame()
        pred_arrival_min = []
        pred_departure_min = []


    # 3. Construction des résultats
    results = []
    pred_idx = 0
    
    for date in dates_to_predict:
        date_str = date.strftime('%d/%m/%Y')
        
        if date_str in historical_data_map:
            # Utiliser les données historiques réelles
            data = historical_data_map[date_str]
            arrival_min = data['first_punch_min']
            departure_min = data['last_punch_min']
            is_historical = True
        else:
            # Utiliser les données prédites
            if pred_idx < len(pred_arrival_min):
                arrival_min = pred_arrival_min[pred_idx]
                departure_min = pred_departure_min[pred_idx]
                pred_idx += 1
            else:
                # Cela ne devrait pas arriver si la logique est correcte
                arrival_min = 0
                departure_min = 0

            is_historical = False
            
            # Correction : S'assurer que l'heure de départ prédite est après l'arrivée
            if departure_min < arrival_min:
                departure_min = arrival_min + (9 * 60) # Ajout d'une durée de travail minimum
            
            # S'assurer que les temps prédits sont non-négatifs
            arrival_min = max(0, arrival_min)
            departure_min = max(0, departure_min)


        results.append({
            "date": date_str,
            "first_punch": minutes_to_time(arrival_min),
            "last_punch": minutes_to_time(departure_min),
            "historical": is_historical
        })

    return results
