# Tests pour src/work_time_prediction/core/database.py

import pytest
import pandas as pd
import io
import os
from unittest.mock import patch
from work_time_prediction.core.database import (
    load_data_from_csv, 
    save_data_to_db, 
    get_all_data, 
    get_db_connection
)
from work_time_prediction.core.exceptions import InvalidCsvFormatError
from work_time_prediction.core.constants import DB_FILE, TABLE_NAME

# Données CSV de simulation brutes (format standard)
MOCK_CSV_CONTENT = """Employee ID,Date,Day of Week,First Punch,Last Punch,Hours,Minutes,Total Minutes,Task
E001,01/01/2023,Sun,09:00,17:00,8,0,480,ProjectA
E001,02/01/2023,Mon,08:30,16:30,8,0,480,ProjectB
E002,01/01/2023,Sun,10:00,18:30,8,30,510,ProjectC
E002,03/01/2023,Tue,11:00,17:00,6,0,360,ProjectA
"""

# Fixture qui crée un chemin de fichier DB temporaire pour garantir l'isolation
@pytest.fixture
def temp_db_path(tmp_path):
    """Crée un chemin d'accès à un fichier SQLite temporaire unique."""
    db_file = tmp_path / "test_db.sqlite"
    return str(db_file)

# --- Tests de load_data_from_csv (Inchagngés) ---

def test_load_data_from_csv_success():
    """Teste le chargement et le prétraitement d'un CSV valide."""
    csv_data = io.StringIO(MOCK_CSV_CONTENT)
    df = load_data_from_csv(csv_data)
    
    assert not df.empty
    assert len(df) == 4
    assert list(df.columns) == ['Employee_ID', 'Date', 'first_punch_min', 'last_punch_min']
    
    # Vérification des conversions de temps
    assert df.iloc[0]['first_punch_min'] == 540.0
    assert df.iloc[0]['last_punch_min'] == 1020.0

def test_load_data_from_csv_invalid_format():
    """Teste la gestion d'un CSV avec un format de colonnes insuffisant."""
    invalid_csv = "A,B,C,D\n1,2,3,4"
    csv_data = io.StringIO(invalid_csv)
    with pytest.raises(InvalidCsvFormatError):
        load_data_from_csv(csv_data)

def test_load_data_from_csv_empty():
    """Teste la gestion d'un CSV vide."""
    empty_csv = ""
    csv_data = io.StringIO(empty_csv)
    with pytest.raises(InvalidCsvFormatError):
        load_data_from_csv(csv_data)
        
# --- Tests de save_data_to_db et get_all_data ---

@patch('work_time_prediction.core.database.DB_FILE', new=':memory:')
def test_get_all_data_empty_db():
    """Teste la récupération quand la table n'existe pas encore (nouvelle DB en mémoire)."""
    # Le patch ':memory:' ici est suffisant pour isoler ce test
    df = get_all_data()
    assert df.empty

# Correction: Utilisation de monkeypatch pour remplacer la constante DB_NAME
# dans le module database. Cela garantit que toutes les fonctions du module
# utilisent le chemin de fichier temporaire pour la durée du test.
def test_save_and_get_data_flow(temp_db_path, monkeypatch):
    """Teste le flux complet: chargement, sauvegarde et récupération en utilisant un fichier temporaire."""
    
    # 1. Patch de la constante DB_NAME dans le module database
    monkeypatch.setattr('work_time_prediction.core.database.DB_FILE', temp_db_path)
    
    csv_data = io.StringIO(MOCK_CSV_CONTENT)
    df_processed = load_data_from_csv(csv_data)
    
    # 2. Sauvegarde des données (utilise le fichier temporaire)
    save_data_to_db(df_processed)
    
    # Vérification que le fichier a été créé
    assert os.path.exists(temp_db_path)
    
    # 3. Récupération des données (utilise le même fichier temporaire)
    df_retrieved = get_all_data()
    
    assert not df_retrieved.empty
    assert len(df_retrieved) == 4
    
    # Le premier jour (01/01/2023) était un dimanche (6)
    assert df_retrieved.iloc[0]['Day_of_Week'] == 6
    assert df_retrieved.iloc[0]['Day_of_Year'] == 1
