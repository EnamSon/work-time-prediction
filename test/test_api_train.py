# tests/test_api_train.py
# Tests pour l'endpoint d'entraînement

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from work_time_prediction.main import app
from work_time_prediction.core.exceptions import InvalidCsvFormatError, NoDataFoundError

# Initialisation du client de test
client = TestClient(app)

# Données CSV de simulation pour l'upload
MOCK_CSV_CONTENT = """Employee ID,Date,Day of Week,First Punch,Last Punch,Hours,Minutes,Total Minutes,Task
E001,01/01/2023,Sun,09:00,17:00,8,0,480,ProjectA
E001,02/01/2023,Mon,08:30,17:30,9,0,540,ProjectB
E002,01/01/2023,Sun,09:15,17:15,8,0,480,ProjectA
E002,02/01/2023,Mon,09:00,18:00,9,0,540,ProjectB
E003,01/01/2023,Sun,08:45,17:45,9,0,540,ProjectC
"""

MOCK_CSV_FILE = {"file": ("data.csv", MOCK_CSV_CONTENT, "text/csv")}

INVALID_CSV_CONTENT = """Invalid,CSV,Format
Not,Proper,Data
Missing,Required,Columns
"""

INVALID_CSV_FILE = {"file": ("invalid.csv", INVALID_CSV_CONTENT, "text/csv")}

EMPTY_CSV_CONTENT = """Employee ID,Date,Day of Week,First Punch,Last Punch,Hours,Minutes,Total Minutes,Task
"""

EMPTY_CSV_FILE = {"file": ("empty.csv", EMPTY_CSV_CONTENT, "text/csv")}


class TestTrainEndpoint:
    """Tests pour l'endpoint POST /api/train/."""
    
    @patch('work_time_prediction.api.train.train_models')
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_success(self, mock_load, mock_save, mock_train):
        """Teste l'entraînement réussi avec un CSV valide."""
        # Configuration des mocks
        mock_load.return_value = MagicMock()  # DataFrame mocké
        mock_train.return_value = 100  # Simule 100 points de données
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data_points"] == 100
        assert "entraînés et prêts" in data["message"]
        
        # Vérifier que les fonctions ont été appelées dans le bon ordre
        mock_load.assert_called_once()
        mock_save.assert_called_once()
        mock_train.assert_called_once()
    
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_invalid_csv_format(self, mock_load):
        """Teste la levée d'une erreur si le CSV est invalide."""
        mock_load.side_effect = InvalidCsvFormatError("Colonnes manquantes ou mal formatées")
        
        response = client.post("/api/train/", files=INVALID_CSV_FILE)
        
        assert response.status_code == 400
        assert "format de fichier" in response.json()["detail"].lower()
        assert "colonnes" in response.json()["detail"].lower()
    
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_csv_parsing_error(self, mock_load):
        """Teste l'erreur de parsing CSV."""
        mock_load.side_effect = InvalidCsvFormatError("Erreur de parsing du fichier CSV")
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 400
        assert "format de fichier" in response.json()["detail"].lower()
    
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_database_connection_error(self, mock_load, mock_save):
        """Teste la gestion d'erreur de connexion à la base de données."""
        mock_load.return_value = MagicMock()
        mock_save.side_effect = Exception("Impossible de se connecter à la base de données")
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 500
        assert "base de données" in response.json()["detail"].lower()
    
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_database_write_error(self, mock_load, mock_save):
        """Teste la gestion d'erreur d'écriture en base de données."""
        mock_load.return_value = MagicMock()
        mock_save.side_effect = Exception("Erreur lors de l'insertion des données")
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 500
        assert "sauvegarde" in response.json()["detail"].lower()
    
    @patch('work_time_prediction.api.train.train_models')
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_no_data_after_save(self, mock_load, mock_save, mock_train):
        """Teste l'erreur quand aucune donnée n'est disponible après sauvegarde."""
        mock_load.return_value = MagicMock()
        mock_train.side_effect = NoDataFoundError("Aucune donnée trouvée dans la base")
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 500
        assert "entraînement" in response.json()["detail"].lower()
    
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_file_decode_error(self, mock_load):
        """Teste l'erreur de décodage du fichier."""
        mock_load.side_effect = Exception("Erreur de décodage UTF-8")
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 500
        assert "lecture du fichier" in response.json()["detail"].lower()
    
    @patch('work_time_prediction.api.train.train_models')
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_small_dataset(self, mock_load, mock_save, mock_train):
        """Teste l'entraînement avec un petit jeu de données."""
        mock_load.return_value = MagicMock()
        mock_train.return_value = 5  # Seulement 5 points
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 200
        assert response.json()["data_points"] == 5
    
    @patch('work_time_prediction.api.train.train_models')
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_large_dataset(self, mock_load, mock_save, mock_train):
        """Teste l'entraînement avec un grand jeu de données."""
        mock_load.return_value = MagicMock()
        mock_train.return_value = 10000  # 10000 points
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 200
        assert response.json()["data_points"] == 10000
    
    @patch('work_time_prediction.api.train.train_models')
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_retrain_success(self, mock_load, mock_save, mock_train):
        """Teste le réentraînement des modèles."""
        mock_load.return_value = MagicMock()
        mock_train.return_value = 100
        
        # Premier entraînement
        response1 = client.post("/api/train/", files=MOCK_CSV_FILE)
        assert response1.status_code == 200
        
        # Deuxième entraînement (réentraînement)
        mock_train.return_value = 150  # Plus de données
        response2 = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response2.status_code == 200
        assert response2.json()["status"] == "success"
        assert response2.json()["data_points"] == 150
    
    def test_train_endpoint_no_file_provided(self):
        """Teste l'erreur quand aucun fichier n'est fourni."""
        response = client.post("/api/train/")
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @patch('work_time_prediction.api.train.train_models')
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_response_structure(self, mock_load, mock_save, mock_train):
        """Vérifie la structure complète de la réponse de succès."""
        mock_load.return_value = MagicMock()
        mock_train.return_value = 100
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier que tous les champs requis sont présents
        assert "status" in data
        assert "message" in data
        assert "data_points" in data
        
        # Vérifier les types
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)
        assert isinstance(data["data_points"], int)
    
    @patch('work_time_prediction.api.train.train_models')
    @patch('work_time_prediction.api.train.save_data_to_db')
    @patch('work_time_prediction.api.train.load_data_from_csv')
    def test_train_endpoint_ml_training_exception(self, mock_load, mock_save, mock_train):
        """Teste la gestion d'exception inattendue lors de l'entraînement ML."""
        mock_load.return_value = MagicMock()
        mock_train.side_effect = Exception("Erreur inattendue dans RandomForest")
        
        response = client.post("/api/train/", files=MOCK_CSV_FILE)
        
        assert response.status_code == 500
        assert "entraînement ml" in response.json()["detail"].lower()