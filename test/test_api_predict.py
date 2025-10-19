# tests/test_api_predict.py
# Tests pour l'endpoint de prédiction

import pytest
import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from work_time_prediction.main import app
from work_time_prediction.core.exceptions import (
    ModelNotTrainedError,
    EmployeeNotFoundError
)

# Initialisation du client de test
client = TestClient(app)


class TestPredictEndpoint:
    """Tests pour l'endpoint POST /api/predict/."""
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_success_single_day(self, mock_generate):
        """Teste la prédiction réussie pour un seul jour."""
        mock_raw_data = [
            {
                "date": "10/10/2025",
                "first_punch": "08:15",
                "last_punch": "16:45",
                "historical": False
            }
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "10/10/2025",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert "predictions" in response_data
        assert len(response_data["predictions"]) == 1
        assert response_data["predictions"][0]["first_punch"] == "08:15"
        assert response_data["predictions"][0]["last_punch"] == "16:45"
        assert response_data["predictions"][0]["historical"] is False
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_success_multiple_days(self, mock_generate):
        """Teste la prédiction réussie pour plusieurs jours."""
        mock_raw_data = [
            {
                "date": "09/10/2025",
                "first_punch": "08:00",
                "last_punch": "17:00",
                "historical": True
            },
            {
                "date": "10/10/2025",
                "first_punch": "08:15",
                "last_punch": "16:45",
                "historical": False
            },
            {
                "date": "11/10/2025",
                "first_punch": "08:10",
                "last_punch": "17:10",
                "historical": False
            }
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "10/10/2025",
            "window_size": 3
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["predictions"]) == 3
        
        # Vérifier le mélange de données historiques et prédites
        assert response_data["predictions"][0]["historical"] is True
        assert response_data["predictions"][1]["historical"] is False
        assert response_data["predictions"][2]["historical"] is False
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_model_not_trained(self, mock_generate):
        """Teste l'erreur quand le modèle n'est pas entraîné."""
        mock_generate.side_effect = ModelNotTrainedError()
        
        request_data = {
            "employee_id": "E001",
            "target_date": "10/10/2025",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        assert "n'est pas encore entraîné" in response.json()["detail"]
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_employee_not_found(self, mock_generate):
        """Teste l'erreur quand l'employé est inconnu."""
        message = "L'employé avec l'ID 'E999' est introuvable dans les données historiques."
        mock_generate.side_effect = EmployeeNotFoundError("E999")
        
        request_data = {
            "employee_id": "E999",
            "target_date": "10/10/2025",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == message
    
    def test_predict_endpoint_invalid_date_format_dashes(self):
        """Teste l'erreur pour un format de date avec tirets (ISO)."""
        request_data = {
            "employee_id": "E001",
            "target_date": "2025-10-10",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        assert "format de date" in response.json()["detail"].lower()
    
    def test_predict_endpoint_invalid_date_format_wrong_separator(self):
        """Teste l'erreur pour un format de date avec mauvais séparateur."""
        request_data = {
            "employee_id": "E001",
            "target_date": "10.10.2025",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        assert "format de date" in response.json()["detail"].lower()
    
    def test_predict_endpoint_invalid_date_values(self):
        """Teste l'erreur pour des valeurs de date invalides."""
        request_data = {
            "employee_id": "E001",
            "target_date": "32/13/2025",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_with_default_window_size(self, mock_generate):
        """Teste la prédiction avec la taille de fenêtre par défaut."""
        mock_raw_data = [
            {
                "date": "10/10/2025",
                "first_punch": "08:00",
                "last_punch": "17:00",
                "historical": False
            }
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "10/10/2025"
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_large_window_size(self, mock_generate):
        """Teste la prédiction avec une grande fenêtre (1 mois)."""
        mock_raw_data = [
            {
                "date": f"{i:02d}/10/2025",
                "first_punch": "08:00",
                "last_punch": "17:00",
                "historical": False
            }
            for i in range(1, 32)
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "15/10/2025",
            "window_size": 31
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert len(response.json()["predictions"]) == 31
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_historical_data_only(self, mock_generate):
        """Teste la prédiction avec uniquement des données historiques."""
        mock_raw_data = [
            {
                "date": "05/10/2025",
                "first_punch": "08:00",
                "last_punch": "17:00",
                "historical": True
            },
            {
                "date": "06/10/2025",
                "first_punch": "08:05",
                "last_punch": "17:05",
                "historical": True
            }
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "05/10/2025",
            "window_size": 2
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        predictions = response.json()["predictions"]
        assert all(p["historical"] is True for p in predictions)
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_response_structure(self, mock_generate):
        """Vérifie la structure complète de la réponse de prédiction."""
        mock_raw_data = [
            {
                "date": "10/10/2025",
                "first_punch": "08:00",
                "last_punch": "17:00",
                "historical": False
            }
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "10/10/2025",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure
        assert "predictions" in data
        assert isinstance(data["predictions"], list)
        
        prediction = data["predictions"][0]
        assert "date" in prediction
        assert "first_punch" in prediction
        assert "last_punch" in prediction
        assert "historical" in prediction
        
        # Vérifier les types
        assert isinstance(prediction["date"], str)
        assert isinstance(prediction["first_punch"], str)
        assert isinstance(prediction["last_punch"], str)
        assert isinstance(prediction["historical"], bool)
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_internal_error(self, mock_generate):
        """Teste la gestion d'une erreur interne inattendue."""
        mock_generate.side_effect = Exception("Erreur inattendue dans le modèle")
        
        request_data = {
            "employee_id": "E001",
            "target_date": "10/10/2025",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 500
        assert "erreur interne" in response.json()["detail"].lower()
    
    def test_predict_endpoint_missing_employee_id(self):
        """Teste l'erreur quand employee_id est manquant."""
        request_data = {
            "target_date": "10/10/2025",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_predict_endpoint_missing_target_date(self):
        """Teste l'erreur quand target_date est manquant."""
        request_data = {
            "employee_id": "E001",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_weekend_dates(self, mock_generate):
        """Teste la prédiction pour des dates de weekend."""
        mock_raw_data = [
            {
                "date": "12/10/2025",  # Samedi
                "first_punch": "09:00",
                "last_punch": "13:00",
                "historical": False
            },
            {
                "date": "13/10/2025",  # Dimanche
                "first_punch": "10:00",
                "last_punch": "14:00",
                "historical": False
            }
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "12/10/2025",
            "window_size": 2
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert len(response.json()["predictions"]) == 2
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_past_date(self, mock_generate):
        """Teste la prédiction pour une date passée (devrait retourner historique)."""
        mock_raw_data = [
            {
                "date": "01/01/2024",
                "first_punch": "08:00",
                "last_punch": "17:00",
                "historical": True
            }
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "01/01/2024",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert response.json()["predictions"][0]["historical"] is True
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_future_date(self, mock_generate):
        """Teste la prédiction pour une date future."""
        mock_raw_data = [
            {
                "date": "01/01/2026",
                "first_punch": "08:00",
                "last_punch": "17:00",
                "historical": False
            }
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "01/01/2026",
            "window_size": 1
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert response.json()["predictions"][0]["historical"] is False
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_multiple_employees(self, mock_generate):
        """Teste les prédictions pour différents employés."""
        # Prédiction pour E001
        mock_generate.return_value = [
            {
                "date": "10/10/2025",
                "first_punch": "08:00",
                "last_punch": "17:00",
                "historical": False
            }
        ]
        
        request_e001 = {
            "employee_id": "E001",
            "target_date": "10/10/2025",
            "window_size": 1
        }
        
        response_e001 = client.post(
            "/api/predict/",
            content=json.dumps(request_e001),
            headers={"Content-Type": "application/json"}
        )
        
        # Prédiction pour E002
        mock_generate.return_value = [
            {
                "date": "10/10/2025",
                "first_punch": "09:00",
                "last_punch": "18:00",
                "historical": False
            }
        ]
        
        request_e002 = {
            "employee_id": "E002",
            "target_date": "10/10/2025",
            "window_size": 1
        }
        
        response_e002 = client.post(
            "/api/predict/",
            content=json.dumps(request_e002),
            headers={"Content-Type": "application/json"}
        )
        
        assert response_e001.status_code == 200
        assert response_e002.status_code == 200
    
    @patch('work_time_prediction.api.predict.generate_predictions')
    def test_predict_endpoint_date_range_around_target(self, mock_generate):
        """Vérifie que la fenêtre est bien centrée autour de la date cible."""
        # Window de 5 jours = 2 jours avant + cible + 2 jours après
        mock_raw_data = [
            {"date": "08/10/2025", "first_punch": "08:00", "last_punch": "17:00", "historical": False},
            {"date": "09/10/2025", "first_punch": "08:00", "last_punch": "17:00", "historical": False},
            {"date": "10/10/2025", "first_punch": "08:00", "last_punch": "17:00", "historical": False},
            {"date": "11/10/2025", "first_punch": "08:00", "last_punch": "17:00", "historical": False},
            {"date": "12/10/2025", "first_punch": "08:00", "last_punch": "17:00", "historical": False}
        ]
        mock_generate.return_value = mock_raw_data
        
        request_data = {
            "employee_id": "E001",
            "target_date": "10/10/2025",
            "window_size": 5
        }
        
        response = client.post(
            "/api/predict/",
            content=json.dumps(request_data),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        predictions = response.json()["predictions"]
        assert len(predictions) == 5
        
        # Vérifier que la date cible est au milieu
        dates = [p["date"] for p in predictions]
        assert "10/10/2025" in dates
    
    def test_predict_endpoint_empty_json(self):
        """Teste l'erreur avec un JSON vide."""
        response = client.post(
            "/api/predict/",
            content=json.dumps({}),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_predict_endpoint_malformed_json(self):
        """Teste l'erreur avec un JSON mal formé."""
        response = client.post(
            "/api/predict/",
            content="not a valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
