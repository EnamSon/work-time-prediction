# src/work_time_prediction/core/ml_state.py
# Gestion de l'état global des modèles ML

from typing import Any, Dict
from sklearn.preprocessing import LabelEncoder  # type: ignore


class GlobalMLState:
    """Conteneur pour les modèles entraînés et les encodeurs."""
    
    def __init__(self):
        # Utilisation de 'Any' pour les classes sklearn non typées
        self.model_arrival: Any | None = None
        self.model_departure: Any | None = None
        self.employee_encoder: Any = LabelEncoder()
        self.is_trained: bool = False
        self.employee_id_map: Dict[str, int] = {}  # Correspondance ID réel -> ID encodé

    def reset(self) -> None:
        """Réinitialise l'état ML (utile pour les tests)."""
        self.model_arrival = None
        self.model_departure = None
        self.employee_encoder = LabelEncoder()
        self.is_trained = False
        self.employee_id_map = {}

    def is_employee_known(self, employee_id: str) -> bool:
        """Vérifie si un employé est connu dans le système."""
        return employee_id in self.employee_id_map

    def get_encoded_id(self, employee_id: str) -> int:
        """Retourne l'ID encodé d'un employé."""
        return self.employee_id_map[employee_id]


# Instance globale (Singleton)
ml_state = GlobalMLState()
