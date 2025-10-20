# src/work_time_prediction/core/ml_state.py
# Gestion de l'état global des modèles ML

from typing import Any, Dict
from sklearn.preprocessing import LabelEncoder  # type: ignore


class MLState:
    """Conteneur pour les modèles entraînés et les encodeurs."""
    
    def __init__(self):
        # Utilisation de 'Any' pour les classes sklearn non typées
        self.model_start_time: Any | None = None
        self.model_end_time: Any | None = None
        self.id_encoder: Any = LabelEncoder()
        self.is_trained: bool = False
        self.id_map: Dict[str, int] = {}  # Correspondance ID réel -> ID encodé

    def reset(self) -> None:
        """Réinitialise l'état ML (utile pour les tests)."""
        self.model_start_time = None
        self.model_end_time = None
        self.id_encoder = LabelEncoder()
        self.is_trained = False
        self.id_map = {}

    def is_id_known(self, id: str) -> bool:
        """Vérifie si un employé est connu dans le système."""
        return id in self.id_map

    def get_encoded_id(self, id: str) -> int:
        """Retourne l'ID encodé d'un employé."""
        return self.id_map[id]


# Instance globale (Singleton)
ml_state = MLState()
