# src/work_time_prediction/api/predict.py
# Endpoint de génération de prédictions

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import List
import pandas as pd

from work_time_prediction.models.predict_request import PredictionRequest
from work_time_prediction.models.predict_response import PredictionResponse, PredictedDay
from work_time_prediction.core.predictions import generate_predictions
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
async def get_predictions(request: PredictionRequest):
    """
    Prédit les horaires pour une fenêtre de dates autour de la date cible.
    
    Args:
        request: Requête contenant l'ID employé, la date cible et la taille de fenêtre
        
    Returns:
        Réponse contenant les prédictions pour toutes les dates
        
    Raises:
        HTTPException: En cas d'erreur de format de date, modèle non entraîné, 
                      employé non trouvé ou erreur interne
    """
    try:
        # Conversion et détermination de la fenêtre de prédiction
        target_date = datetime.strptime(request.target_date, '%d/%m/%Y')
        all_dates = _calculate_date_range(target_date, request.window_size)

        # Génération des résultats (Historique + Prédictions)
        raw_results = generate_predictions(request.employee_id, all_dates)

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
