# Logique d'entraînement et de prédiction du Machine Learning

from typing import Dict, List, Any
import pandas as pd
# Utilisation de 'Any' et ignore pour gérer les dépendances sans stubs typés (mypy)
from sklearn.ensemble import RandomForestRegressor # type: ignore
from sklearn.preprocessing import LabelEncoder # type: ignore
from datetime import datetime

from work_time_prediction.core.constants import FEATURES
from work_time_prediction.core.database import get_all_data
from work_time_prediction.core.utils import minutes_to_time
from work_time_prediction.core.exceptions import ModelNotTrainedError, EmployeeNotFoundError, NoDataFoundError

# --- Stockage Global de l'État ML (Modèles et Encodeurs) ---

class GlobalMLState:
    """Conteneur pour les modèles entraînés et les encodeurs."""
    def __init__(self):
        # Utilisation de 'Any' pour les classes sklearn non typées
        self.model_arrival: Any | None = None
        self.model_departure: Any | None = None
        self.employee_encoder: Any = LabelEncoder()
        self.is_trained: bool = False
        self.employee_id_map: Dict[str, int] = {} # Correspondance ID réel -> ID encodé

# Instance globale (Singleton)
ml_state = GlobalMLState()

# --- Fonctions ML ---

def train_models() -> int:
    """
    Charge les données de la DB, encode l'ID et entraîne les modèles.
    Retourne le nombre de points de données utilisés.
    """
    df = get_all_data()
    
    if df.empty:
        raise NoDataFoundError("Impossible d'entraîner : aucune donnée trouvée dans la base de données.")

    # 1. Encodage de l'ID Employé
    all_employee_ids = df['Employee_ID'].unique()
    ml_state.employee_encoder.fit(all_employee_ids)
    df['Employee_ID_Encoded'] = ml_state.employee_encoder.transform(df['Employee_ID'])
    
    # 2. Mise à jour du mapping global
    ml_state.employee_id_map = {
        real_id: encoded_id
        for real_id, encoded_id in zip(all_employee_ids, ml_state.employee_encoder.transform(all_employee_ids))
    }
    
    X = df[FEATURES]
    
    # 3. Modèle pour l'heure d'arrivée
    y_arrival = df['first_punch_min']
    ml_state.model_arrival = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
    ml_state.model_arrival.fit(X, y_arrival)

    # 4. Modèle pour l'heure de départ
    y_departure = df['last_punch_min']
    ml_state.model_departure = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
    ml_state.model_departure.fit(X, y_departure)
    
    ml_state.is_trained = True
    
    return len(df) # Nombre de points de données utilisés

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
