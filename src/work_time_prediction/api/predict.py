# src/work_time_prediction/api/predict.py
# Endpoint de génération de prédictions

from fastapi import APIRouter, HTTPException, Header
from datetime import datetime, timedelta
from typing import List
import pandas as pd

from work_time_prediction.models.predict_request import PredictionRequest
from work_time_prediction.models.predict_response import PredictionResponse, PredictedDay
from work_time_prediction.core.predictions import generate_predictions
from work_time_prediction.core.session_manager import session_manager
from work_time_prediction.core.exceptions import (
    ModelNotTrainedError, 
    EmployeeNotFoundError
)

router = APIRouter()


def _calculate_date_range(target_date: datetime, window_size: int) -> List[datetime]:
    """
    Calcule la plage de dates autour de la date cible.
    
    Args:
        target_date: Date centrale pour les prédictions
        window_size: Taille de la fenêtre (nombre total de jours)
        
    Returns:
        Liste des dates dans la fenêtre
    """
    start_date = target_date - timedelta(days=window_size // 2)
    end_date = target_date + timedelta(days=window_size // 2)
    
    # Conversion explicite des Timestamp pandas en datetime
    return [
        d.to_pydatetime() 
        for d in pd.date_range(start=start_date, end=end_date, freq='D')
    ]


@router.post("/predict/", response_model=PredictionResponse)
@router.post("/predict", response_model=PredictionResponse)
async def predict_schedule(
    request: PredictionRequest,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """
    Génère des prédictions d'horaires pour un employé.
    Charge automatiquement le modèle depuis la session.
    
    Args:
        request: Données de la requête (id, target_date, window_size)
        session_id: ID de session (requis dans le header)
    
    Returns:
        PredictionResponse: Liste des prédictions
    """
    # Valider la session
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session invalide ou expirée")
    
    # Charger le modèle depuis la session
    model_loaded = session_manager.load_model(session_id)
    if not model_loaded:
        raise HTTPException(
            status_code=400, 
            detail="Aucun modèle entraîné trouvé pour cette session. Veuillez d'abord entraîner un modèle."
        )
    
    try:
        # Conversion et détermination de la fenêtre de prédiction
        target_date = datetime.strptime(request.target_date, '%d/%m/%Y')
        all_dates = _calculate_date_range(target_date, request.window_size)

        # Génération des résultats (Historique + Prédictions)
        raw_results = generate_predictions(model_loaded, request.id, all_dates)

        # Construction des objets PredictedDay pour Pydantic
        predictions = [PredictedDay(**data) for data in raw_results]

        return PredictionResponse(predictions=predictions)

    except ModelNotTrainedError as e:
        raise HTTPException(status_code=400, detail=e.message)
    
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Format de date cible invalide. Utilisez jj/mm/aaaa."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne lors de la prédiction: {e}"
        )
