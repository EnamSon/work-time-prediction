# Modèle Pydantic pour la requête de configuration de colonnes

from pydantic import BaseModel

class RequiredColumnsMappingRequest(BaseModel):
    """
    Définit la structure de la requête pour la configuration des colonnes.
    """
    id_column: str
    date_column: str
    start_time_column: str
    end_time_column: str
