# tests/test_api_status.py
# Tests pour l'endpoint de statut

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from work_time_prediction.main import app

# Initialisation du client de test
client = TestClient(app)


class TestStatusEndpoint:
    """Tests pour l'endpoint GET /api/."""
    
    @patch('work_time_prediction.api.status.ml_state')
    def test_status_check_trained(self, mock_ml_state):
        """Vérifie le statut lorsque le modèle est entraîné."""
        mock_ml_state.is_trained = True
        
        response = client.get("/api/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "is_trained" in data
        assert data["is_trained"] is True
        assert "API en ligne" in data["message"]
    
    @patch('work_time_prediction.api.status.ml_state')
    def test_status_check_not_trained(self, mock_ml_state):
        """Vérifie le statut lorsque le modèle n'est pas entraîné."""
        mock_ml_state.is_trained = False
        
        response = client.get("/api/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_trained"] is False
    
    @patch('work_time_prediction.api.status.ml_state')
    def test_status_check_response_structure(self, mock_ml_state):
        """Vérifie la structure de la réponse."""
        mock_ml_state.is_trained = False
        
        response = client.get("/api/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data["message"], str)
        assert isinstance(data["is_trained"], bool)
    
    @patch('work_time_prediction.api.status.ml_state')
    def test_status_check_multiple_calls(self, mock_ml_state):
        """Vérifie que l'endpoint peut être appelé plusieurs fois."""
        mock_ml_state.is_trained = True
        
        response1 = client.get("/api/")
        response2 = client.get("/api/")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["is_trained"] == response2.json()["is_trained"]
