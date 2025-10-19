# Modèle Pydantic pour la requête de configuration de colonnes

from pydantic import BaseModel

class RequiredColumnsMappingRequest(BaseModel):
    """
    Définit la structure de la requête pour la configuration des colonnes.
    """
    id: str
    date: str
    start: str
    end: str
