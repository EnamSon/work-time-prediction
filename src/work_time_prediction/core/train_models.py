# src/work_time_prediction/core/train_models.py
# Logique d'entraînement des modèles ML

from sklearn.ensemble import RandomForestRegressor  # type: ignore

from work_time_prediction.core.constants import FEATURES
from work_time_prediction.core.database import get_all_data
from work_time_prediction.core.ml_state import ml_state
from work_time_prediction.core.exceptions import NoDataFoundError


def train_models() -> int:
    """
    Charge les données de la DB, encode l'ID et entraîne les modèles.
    Retourne le nombre de points de données utilisés.
    
    Raises:
        NoDataFoundError: Si aucune donnée n'est disponible dans la base de données.
    """
    df = get_all_data()
    
    if df.empty:
        raise NoDataFoundError(
            "Impossible d'entraîner : aucune donnée trouvée dans la base de données."
        )

    # 1. Encodage de l'ID Employé
    all_employee_ids = df['Employee_ID'].unique()
    ml_state.employee_encoder.fit(all_employee_ids)
    df['Employee_ID_Encoded'] = ml_state.employee_encoder.transform(df['Employee_ID'])
    
    # 2. Mise à jour du mapping global
    ml_state.employee_id_map = {
        real_id: encoded_id
        for real_id, encoded_id in zip(
            all_employee_ids, 
            ml_state.employee_encoder.transform(all_employee_ids)
        )
    }
    
    X = df[FEATURES]
    
    # 3. Modèle pour l'heure d'arrivée
    y_arrival = df['first_punch_min']
    ml_state.model_arrival = RandomForestRegressor(
        n_estimators=100, 
        random_state=42, 
        n_jobs=-1, 
        max_depth=10
    )
    ml_state.model_arrival.fit(X, y_arrival)

    # 4. Modèle pour l'heure de départ
    y_departure = df['last_punch_min']
    ml_state.model_departure = RandomForestRegressor(
        n_estimators=100, 
        random_state=42, 
        n_jobs=-1, 
        max_depth=10
    )
    ml_state.model_departure.fit(X, y_departure)
    
    ml_state.is_trained = True
    
    return len(df)  # Nombre de points de données utilisés
