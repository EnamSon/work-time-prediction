# Modèle Pydantic pour la réponse de prédiction

from pydantic import BaseModel
from typing import List

class PredictedDay(BaseModel):
    """
    Définit la structure de données pour un jour prédit ou historique.
    """
    date: str
    first_punch: str
    last_punch: str
    historical: bool

class PredictionResponse(BaseModel):
    """
    Conteneur pour la liste des prédictions.
    """
    predictions: List[PredictedDay]
