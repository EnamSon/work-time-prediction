# Tests pour src/work_time_prediction/core/api.py

import pytest
import json
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient
from work_time_prediction.main import app
from work_time_prediction.core.exceptions import (
    ModelNotTrainedError, 
    EmployeeNotFoundError, 
    InvalidCsvFormatError
)

# Initialisation du client de test
client = TestClient(app)

# Données CSV de simulation pour l'upload
MOCK_CSV_CONTENT = """Employee ID,Date,Day of Week,First Punch,Last Punch,Hours,Minutes,Total Minutes,Task
E001,01/01/2023,Sun,09:00,17:00,8,0,480,ProjectA
"""
# Un fichier avec des données de test
MOCK_CSV_FILE = {"file": ("data.csv", MOCK_CSV_CONTENT, "text/csv")}

# --- Tests de l'Endpoint /api/ ---

# Patch de l'état global ML là où il est utilisé (dans api.py)
@patch('work_time_prediction.core.api.ml_state')
def test_status_trained(mock_ml_state):
    """Teste le statut lorsque le modèle est entraîné."""
    # Simuler l'état entraîné
    mock_ml_state.is_trained = True
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json()["is_trained"] is True

@patch('work_time_prediction.core.api.ml_state')
def test_status_not_trained(mock_ml_state):
    """Teste le statut lorsque le modèle n'est pas entraîné."""
    # Simuler l'état non entraîné
    mock_ml_state.is_trained = False
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json()["is_trained"] is False

# --- Tests de l'Endpoint /api/train/ ---

@patch('work_time_prediction.core.api.train_models')
@patch('work_time_prediction.core.api.save_data_to_db')
@patch('work_time_prediction.core.api.load_data_from_csv', return_value=MagicMock()) # Mock du DF
def test_train_endpoint_success(mock_load, mock_save, mock_train):
    """Teste l'endpoint d'entraînement réussi."""
    mock_train.return_value = 100 # Simule 100 points de données
    response = client.post("/api/train/", files=MOCK_CSV_FILE)
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data_points"] == 100
    mock_load.assert_called_once()
    mock_save.assert_called_once()
    mock_train.assert_called_once()

@patch('work_time_prediction.core.api.load_data_from_csv')
def test_train_endpoint_invalid_csv(mock_load):
    """Teste la levée d'une erreur si le CSV est invalide."""
    # Simuler la levée de l'exception personnalisée
    mock_load.side_effect = InvalidCsvFormatError("Erreur de test de format")
    response = client.post("/api/train/", files=MOCK_CSV_FILE)
    
    # Code de statut 400 attendu pour une erreur utilisateur (mauvais fichier)
    assert response.status_code == 400
    assert "Erreur de test de format" in response.json()["detail"]


# --- Tests de l'Endpoint /api/predict/ ---

@patch('work_time_prediction.core.api.generate_predictions')
def test_predict_endpoint_success(mock_generate):
    """Teste l'endpoint de prédiction réussi."""
    # Simuler un résultat de prédiction brut (dictionnaire)
    mock_raw_data = [{
        "date": "10/10/2025",
        "first_punch": "08:15",
        "last_punch": "16:45",
        "historical": False
    }]
    mock_generate.return_value = mock_raw_data
    
    request_data = {
        "employee_id": "E001",
        "target_date": "10/10/2025",
        "window_size": 1
    }
    
    response = client.post("/api/predict/", content=json.dumps(request_data), headers={"Content-Type": "application/json"})
    
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["predictions"]) == 1
    assert response_data["predictions"][0]["first_punch"] == "08:15"
    
@patch('work_time_prediction.core.api.generate_predictions')
def test_predict_endpoint_not_trained(mock_generate):
    """Teste la levée d'une erreur si le modèle n'est pas entraîné."""
    mock_generate.side_effect = ModelNotTrainedError()
    request_data = {"employee_id": "E001", "target_date": "10/10/2025"}
    
    response = client.post("/api/predict/", content=json.dumps(request_data), headers={"Content-Type": "application/json"})
    
    assert response.status_code == 400
    assert "n'est pas encore entraîné" in response.json()["detail"]

@patch('work_time_prediction.core.api.generate_predictions')
def test_predict_employee_not_found(mock_generate):
    """Teste la levée d'une erreur si l'employé est inconnu."""
    # Note: Le message d'erreur doit correspondre exactement à ce que l'API renvoie
    message = "L'employé avec l'ID 'E999' est introuvable dans les données historiques."
    mock_generate.side_effect = EmployeeNotFoundError("E999")
    request_data = {"employee_id": "E999", "target_date": "10/10/2025"}
    
    response = client.post("/api/predict/", content=json.dumps(request_data), headers={"Content-Type": "application/json"})
    
    assert response.status_code == 404
    # On vérifie l'intégralité du message d'erreur
    assert response.json()["detail"] == message
