# tests/test_train_models.py
# Tests unitaires pour le module train_models

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime

from work_time_prediction.core.train_models import train_models
from work_time_prediction.core.ml_state import ml_state
from work_time_prediction.core.exceptions import NoDataFoundError


@pytest.fixture
def sample_training_data():
    """Fixture fournissant des données d'entraînement simulées."""
    return pd.DataFrame({
        'Employee_ID': ['E001', 'E001', 'E002', 'E002', 'E003'],
        'Date': [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 1)
        ],
        'Day_of_Week': [0, 1, 0, 1, 0],
        'Day_of_Year': [1, 2, 1, 2, 1],
        'first_punch_min': [480, 485, 490, 495, 500],
        'last_punch_min': [1020, 1025, 1030, 1035, 1040]
    })


@pytest.fixture(autouse=True)
def reset_ml_state():
    """Réinitialise ml_state avant et après chaque test."""
    ml_state.reset()
    yield
    ml_state.reset()


class TestTrainModels:
    """Tests pour la fonction train_models()."""
    
    @patch('work_time_prediction.core.train_models.get_all_data')
    def test_train_models_success(self, mock_get_data, sample_training_data):
        """Vérifie l'entraînement réussi des modèles."""
        mock_get_data.return_value = sample_training_data
        
        # Entraîner les modèles
        data_points = train_models()
        
        # Vérifications
        assert data_points == 5
        assert ml_state.is_trained is True
        assert ml_state.model_start_time is not None
        assert ml_state.model_end_time is not None
        assert len(ml_state.id_map) == 3
        assert 'E001' in ml_state.id_map
        assert 'E002' in ml_state.id_map
        assert 'E003' in ml_state.id_map
    
    @patch('work_time_prediction.core.train_models.get_all_data')
    def test_train_models_empty_dataframe(self, mock_get_data):
        """Vérifie que NoDataFoundError est levée si DataFrame vide."""
        mock_get_data.return_value = pd.DataFrame()
        
        with pytest.raises(NoDataFoundError) as exc_info:
            train_models()
        
        assert "aucune donnée trouvée" in str(exc_info.value).lower()
        assert ml_state.is_trained is False
    
    @patch('work_time_prediction.core.train_models.get_all_data')
    def test_train_models_employee_encoding(self, mock_get_data, sample_training_data):
        """Vérifie que l'encodage des employés fonctionne correctement."""
        mock_get_data.return_value = sample_training_data
        
        train_models()
        
        # Vérifier que chaque employé a un ID encodé unique
        encoded_ids = set(ml_state.id_map.values())
        assert len(encoded_ids) == 3
        
        # Vérifier que les 3 IDs attendus sont présents
        assert 'E001' in ml_state.id_map
        assert 'E002' in ml_state.id_map
        assert 'E003' in ml_state.id_map
    
    @patch('work_time_prediction.core.train_models.get_all_data')
    def test_train_models_model_types(self, mock_get_data, sample_training_data):
        """Vérifie que les modèles sont du bon type."""
        mock_get_data.return_value = sample_training_data
        
        train_models()
        
        # Vérifier que les modèles ont une méthode predict
        assert hasattr(ml_state.model_start_time, 'predict')
        assert hasattr(ml_state.model_end_time, 'predict')
        assert callable(ml_state.model_start_time.predict)
        assert callable(ml_state.model_end_time.predict)
    
    @patch('work_time_prediction.core.train_models.get_all_data')
    def test_train_models_multiple_times(self, mock_get_data, sample_training_data):
        """Vérifie qu'on peut réentraîner les modèles plusieurs fois."""
        mock_get_data.return_value = sample_training_data
        
        # Premier entraînement
        data_points_1 = train_models()
        model_1_id = id(ml_state.model_start_time)
        
        # Deuxième entraînement
        data_points_2 = train_models()
        model_2_id = id(ml_state.model_start_time)
        
        assert data_points_1 == data_points_2
        assert ml_state.is_trained is True
        # Les modèles sont réentraînés (nouvelles instances)
        assert model_1_id != model_2_id
    
    @patch('work_time_prediction.core.train_models.get_all_data')
    def test_train_models_single_employee(self, mock_get_data):
        """Vérifie l'entraînement avec un seul employé."""
        single_emp_data = pd.DataFrame({
            'Employee_ID': ['E001'] * 3,
            'Date': [datetime(2024, 1, i) for i in range(1, 4)],
            'Day_of_Week': [0, 1, 2],
            'Day_of_Year': [1, 2, 3],
            'first_punch_min': [480, 485, 490],
            'last_punch_min': [1020, 1025, 1030]
        })
        mock_get_data.return_value = single_emp_data
        
        data_points = train_models()
        
        assert data_points == 3
        assert len(ml_state.id_map) == 1
        assert 'E001' in ml_state.id_map
    
    @patch('work_time_prediction.core.train_models.get_all_data')
    def test_train_models_many_employees(self, mock_get_data):
        """Vérifie l'entraînement avec beaucoup d'employés."""
        many_emp_data = pd.DataFrame({
            'Employee_ID': [f'E{i:03d}' for i in range(100)] * 2,
            'Date': [datetime(2024, 1, 1), datetime(2024, 1, 2)] * 100,
            'Day_of_Week': [0, 1] * 100,
            'Day_of_Year': [1, 2] * 100,
            'first_punch_min': [480] * 200,
            'last_punch_min': [1020] * 200
        })
        mock_get_data.return_value = many_emp_data
        
        data_points = train_models()
        
        assert data_points == 200
        assert len(ml_state.id_map) == 100
    
    @patch('work_time_prediction.core.train_models.get_all_data')
    def test_train_models_encoder_consistency(self, mock_get_data, sample_training_data):
        """Vérifie la cohérence de l'encodeur après l'entraînement."""
        mock_get_data.return_value = sample_training_data
        
        train_models()
        
        # Vérifier que l'encodeur peut transformer les IDs connus
        known_ids = ['E001', 'E002', 'E003']
        encoded = ml_state.id_encoder.transform(known_ids)
        
        assert len(encoded) == 3
        assert all(ml_state.id_map[emp_id] == encoded[i] 
                   for i, emp_id in enumerate(known_ids))