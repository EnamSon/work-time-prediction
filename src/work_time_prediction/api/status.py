# src/work_time_prediction/api/status.py
# Endpoint de vérification du statut du service

from fastapi import APIRouter
from work_time_prediction.core.ml_state import ml_state

router = APIRouter()


@router.get("/")
async def status_check():
    """
    Endpoint de statut pour vérifier si le service est en ligne et entraîné.
    
    Returns:
        Dictionnaire contenant le message de statut et l'état d'entraînement
    """
    return {
        "message": "Service de Prédiction d'Horaires - API en ligne", 
        "is_trained": ml_state.is_trained
    }