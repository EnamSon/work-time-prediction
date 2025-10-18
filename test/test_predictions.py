# Tests pour src/work_time_prediction/core/predictions.py

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch
from work_time_prediction.core.predictions import (
    train_models, 
    generate_predictions, 
    ml_state
)
from work_time_prediction.core.exceptions import (
    ModelNotTrainedError, 
    EmployeeNotFoundError,
    NoDataFoundError
)

# --- Données de Simulation ---

@pytest.fixture
def mock_historical_data():
    """Fixture retournant un DataFrame de données historiques propre pour les tests ML."""
    data = {
        'Employee_ID': ['E001', 'E001', 'E001', 'E002', 'E002'],
        'Date': [
            pd.to_datetime('2025-10-01'), 
            pd.to_datetime('2025-10-02'), 
            pd.to_datetime('2025-10-03'),
            pd.to_datetime('2025-10-01'),
            pd.to_datetime('2025-10-02')
        ],
        # Temps en minutes depuis minuit (ex: 8:00 = 480, 16:00 = 960)
        'first_punch_min': [480.0, 485.0, 475.0, 540.0, 530.0],
        'last_punch_min': [960.0, 970.0, 950.0, 1020.0, 1030.0]
    }
    df = pd.DataFrame(data)
    # Ajouter les features de temps (Day_of_Week: Lun=0, Mar=1, Mer=2)
    df['Day_of_Week'] = df['Date'].dt.dayofweek
    df['Day_of_Year'] = df['Date'].dt.dayofyear
    return df

@pytest.fixture(autouse=True)
def reset_ml_state():
    """Réinitialise l'état ML global avant chaque test."""
    ml_state.__init__()
    
# --- Tests de train_models ---

@patch('work_time_prediction.core.predictions.get_all_data')
def test_train_models_success(mock_get_all_data, mock_historical_data):
    """Teste l'entraînement réussi du modèle."""
    mock_get_all_data.return_value = mock_historical_data
    
    data_points = train_models()
    
    assert data_points == 5
    assert ml_state.is_trained is True
    assert ml_state.model_arrival is not None
    assert ml_state.model_departure is not None
    assert 'E001' in ml_state.employee_id_map
    assert 'E002' in ml_state.employee_id_map

@patch('work_time_prediction.core.predictions.get_all_data')
def test_train_models_empty_data(mock_get_all_data):
    """Teste la levée d'une erreur si les données historiques sont vides."""
    mock_get_all_data.return_value = pd.DataFrame()
    
    with pytest.raises(NoDataFoundError, match="Impossible d'entraîner"):
        train_models()

# --- Tests de generate_predictions ---

@patch('work_time_prediction.core.predictions.get_all_data')
def test_generate_predictions_not_trained(mock_get_all_data):
    """Teste la levée d'une erreur si la prédiction est tentée avant l'entraînement."""
    # ml_state est réinitialisé par la fixture reset_ml_state
    dates = [datetime.now()]
    with pytest.raises(ModelNotTrainedError):
        generate_predictions("E001", dates)

@patch('work_time_prediction.core.predictions.get_all_data')
def test_generate_predictions_employee_not_found(mock_get_all_data, mock_historical_data):
    """Teste la levée d'une erreur si l'ID d'employé est inconnu."""
    mock_get_all_data.return_value = mock_historical_data
    train_models() # Entraîner d'abord
    
    dates = [datetime.now()]
    with pytest.raises(EmployeeNotFoundError):
        generate_predictions("E999", dates)

@patch('work_time_prediction.core.predictions.get_all_data')
def test_generate_predictions_mixed_dates(mock_get_all_data, mock_historical_data):
    """Teste la génération pour un mélange de dates historiques et futures."""
    mock_get_all_data.return_value = mock_historical_data
    train_models() # Entraîner
    
    # Date historique (2025-10-01) et Date future (aujourd'hui)
    historic_date = datetime(2025, 10, 1)
    future_date = datetime.now() + timedelta(days=10) # Date arbitraire future
    
    dates_to_predict = [future_date, historic_date]
    results = generate_predictions("E001", dates_to_predict)
    
    # Assurer que l'ordre est conservé
    future_result = results[0]
    historic_result = results[1]
    
    # 1. Vérification du résultat historique (E001, 2025-10-01: 480 min = 08:00, 960 min = 16:00)
    assert historic_result['date'] == "01/10/2025"
    assert historic_result['historical'] is True
    assert historic_result['first_punch'] == "08:00" # 480 minutes
    assert historic_result['last_punch'] == "16:00" # 960 minutes
    
    # 2. Vérification du résultat futur (doit être une prédiction)
    assert future_result['date'] == future_date.strftime('%d/%m/%Y')
    assert future_result['historical'] is False
    # Les prédictions ML sont des floats, donc on vérifie le format
    assert len(future_result['first_punch']) == 5 # Format HH:MM
    assert len(future_result['last_punch']) == 5 # Format HH:MM
